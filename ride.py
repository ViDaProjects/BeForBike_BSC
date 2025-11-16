# ride.py
import json
import logging
from queue import Queue, Empty
from PySide6.QtCore import QThread, Slot, QMutex, QWaitCondition

# Importe o novo RideState
from rideState import RideState 

from comm_protocol import (
    FileMngMsgId,
    FileManagerMsg,
    RideDataMsg,
    TelemetryMsg
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RideThread(QThread):
    """
    Gerencia o ciclo de vida da corrida.
    Ouve o RideState para saber quando começar/parar.
    """

    def __init__(self,
                 app,
                 ride_state: RideState,          
                 add_ride_data_queue: Queue,
                 file_manager_queue: Queue,
                 send_ride_data_queue: Queue,
                 parent=None):
        super().__init__(parent)
        self.app = app
        self.ride_state = ride_state         
        self.add_ride_data_queue = add_ride_data_queue
        self.file_manager_queue = file_manager_queue
        self.send_ride_data_queue = send_ride_data_queue

        self.is_running = False
        self._current_ride_id = None
        self._telemetry_log = []

        # O Mutex ainda é necessário para as WaitConditions
        self._mutex = QMutex()
        self._ride_start_wait = QWaitCondition()
        self._ride_id_wait = QWaitCondition()

        self.setObjectName("RideThread")
        self.app.aboutToQuit.connect(self.stop)
        
        # --- MUDANÇA ---
        # Conecta o sinal do estado ao nosso slot de "acordar"
        self.ride_state.state_changed.connect(self._on_ride_state_changed)

    def start(self):
        if self.is_running:
            logging.warning("Thread RideThread já está em execução.")
            return
        self.is_running = True
        super().start()
        logging.info("Thread RideThread iniciada.")

    @Slot()
    def stop(self):
        if not self.is_running:
            return
        logging.warning("Parando a thread RideThread...")
        self.is_running = False
        
        # Acorda quaisquer loops em espera para que a thread possa sair
        self._ride_start_wait.wakeAll()
        self._ride_id_wait.wakeAll()
        
        self.quit()
        if not self.wait(5000):
             logging.error("Thread RideThread não respondeu. Forçando finalização.")
             self.terminate() 
        else:
             logging.info("Thread RideThread finalizada com sucesso.")

    # --- SLOTS DE LÓGICA DE NEGÓCIO ---

    @Slot(bool)
    def _on_ride_state_changed(self, is_riding: bool):
        """
        Slot que é chamado pelo RideState.
        Seu único trabalho é acordar o loop run() se ele estiver dormindo.
        """
        if is_riding:
            self._ride_start_wait.wakeAll()
        else:
            # Também acorda no stop, caso esteja preso na espera inicial
            self._ride_start_wait.wakeAll()



    @Slot(int)
    def set_ride_id(self, ride_id: int):
        """
        Slot para receber o ride_id (provavelmente do FileManager).
        (Lógica inalterada)
        """
        self._mutex.lock()
        self._current_ride_id = ride_id
        self._mutex.unlock()
        self._ride_id_wait.wakeAll()

    # --- LÓGICA PRINCIPAL DA THREAD (AJUSTADA) ---

    def run(self):
        while self.is_running:
            
            # 1. Espera pelo evento de início de corrida
            self._mutex.lock()
            while not self.ride_state.is_riding(): 
                if not self.is_running:
                    self._mutex.unlock()
                    return
                self._ride_start_wait.wait(self._mutex)
            
            if not self.is_running:
                self._mutex.unlock()
                return
            self._mutex.unlock()
            
            logging.info("RideThread: Corrida iniciada!")
            self._telemetry_log = []

            # 3. Pede o ride_id
            logging.info("RideThread: Solicitando ride_id...")
            get_id_msg = FileManagerMsg(msg_id=FileMngMsgId.GET_RIDE_ID)
            self.file_manager_queue.put(get_id_msg)

            # 4. Espera pelo ride_id
            self._mutex.lock()
            while self._current_ride_id is None:
                if not self.is_running:
                    self._mutex.unlock()
                    return
                self._ride_id_wait.wait(self._mutex)
            
            ride_id_for_this_ride = self._current_ride_id
            self._mutex.unlock()
            
            file_name = f"ride_{ride_id_for_this_ride}.json"
            logging.info(f"RideThread: ride_id {ride_id_for_this_ride} recebido. Nome: {file_name}")

            # 5. Loop principal de coleta de dados
            while True:
                try:
                    telemetry_msg: TelemetryMsg = self.add_ride_data_queue.get(timeout=0.1)
                    
                    if telemetry_msg.info:
                        telemetry_msg.info.ride_id = ride_id_for_this_ride
                    else:
                        logging.warning("RideThread: Mensagem sem 'info', pulando.")
                        continue
                        
                    json_string = json.dumps(telemetry_msg.to_dict())
                    self._telemetry_log.append(json_string)

                except Empty:
                    is_still_riding = self.ride_state.is_riding() 
                    
                    if not self.is_running:
                        logging.warning("RideThread: Coleta interrompida (stop thread).")
                        break # Sai do loop de coleta
                    
                    if not is_still_riding:
                        logging.info(f"RideThread: Coleta finalizada (stop_ride). Total de {len(self._telemetry_log)} pontos.")
                        break # Sai do loop de coleta

                except Exception as e:
                    # Captura o AttributeError se 'info' for None
                    logging.error(f"Erro na coleta da RideThread: {e}. Pulando pacote.")
                    continue
            
            # 6. Salva os dados
            if self.is_running and self._telemetry_log:
                logging.info(f"RideThread: Enviando dados para FileManagerQueue ({file_name})...")
                file_msg = FileManagerMsg(
                    msg_id=FileMngMsgId.CREATE_FILE,
                    file_name=file_name,
                    telemetry_list=self._telemetry_log
                )
                self.file_manager_queue.put(file_msg)

                logging.info(f"RideThread: Enviando dados para SendRideDataQueue ({file_name})...")
                ride_data_msg = RideDataMsg(
                    file_name=file_name,
                    telemetry_log=self._telemetry_log
                )
                self.send_ride_data_queue.put(ride_data_msg)

            self._mutex.lock()
            self._current_ride_id = None
            self._mutex.unlock()

            logging.info("\nRideThread: Aguardando próxima corrida...")
        
        logging.info("RideThread: Loop de execução (run) finalizado.")