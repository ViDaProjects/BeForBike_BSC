import json
import logging
from queue import Queue, Empty
from PySide6.QtCore import QThread, Signal, Slot

from comm_protocol import CrankData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MockBleNanoThread(QThread):
    """
    Simula um dispositivo Nano (Crank Sensor) conectando,
    enviando dados, e desconectando.
    """
    
    # Sinais para controlar a RideThread
    crank_connection_status = Signal(bool)

    def start(self):
        self.is_running = True
        super().start()

    def __init__(self, process_crank_data_queue: Queue, file_path: str, parent=None):
        super().__init__(parent)
        self.process_crank_data_queue = process_crank_data_queue
        self.file_path = file_path
        self._is_running = False
        self.setObjectName("MockBleNanoThread")

    def run(self):
        """
        Lógica principal da simulação.
        """
        logging.info("[MockNano]: Thread iniciada. Simulando conexão...")

        # 1. Carregar os dados do arquivo
        try:
            with open(self.file_path, 'r') as f:
                telemetry_strings = json.load(f)
            logging.info(f"[MockNano]: Arquivo {self.file_path} carregado com {len(telemetry_strings)} registros.")
        except Exception as e:
            logging.error(f"[MockNano]: Falha ao carregar {self.file_path}: {e}")
            self._is_running = False
            return

        # 2. Simular conexão e emitir sinal de START
        self.msleep(1000)
        logging.info("[MockNano]: Conectado! Emitindo 'nano_connected' (para iniciar a RideThread).")
        self.crank_connection_status.emit(True)

        # 3. Enviar dados de tempos em tempos
        logging.info("[MockNano]: Iniciando envio de dados do crank...")
        count = 0
        for json_string in telemetry_strings:
            # if not self._is_running:
            #     logging.warning("[MockNano]: Simulação interrompida.")
            #     break
            
            try:
                # O arquivo Ride44.json contém a TelemetryMsg completa.
                # O sensor Nano (Crank) só enviaria os dados do "crank".
                full_msg_dict = json.loads(json_string)
                crank_data_dict = full_msg_dict.get("crank")

                if crank_data_dict:
                    self.process_crank_data_queue.put(crank_data_dict)
                    count += 1
                    logging.info(f"[MockNano]: Enviou pacote de crank {count} para ProcessCrankDataQueue.")
                else:
                    # Pula entradas onde "crank" é null
                    logging.info("[MockNano]: Pacote sem dados de crank, pulando.")

                # Simula um intervalo de 200ms entre pacotes
                self.msleep(200)

            except Exception as e:
                logging.error(f"[MockNano]: Erro ao processar item: {e}")

        # 4. Simulação concluída, emitir sinal de STOP
        logging.info(f"[MockNano]: Simulação concluída. Enviou {count} pacotes.")
        self.msleep(1000)
        logging.info("[MockNano]: Desconectando... Emitindo 'nano_disconnected' (para parar a RideThread).")
        self.crank_connection_status.emit(False)
        
        self._is_running = False
        logging.info("[MockNano]: Thread finalizada.")

    @Slot()
    def stop(self):
        self._is_running = False
        self.quit()
        if not self.wait(2000):
            logging.error("[MockNano]: Thread não parou, forçando.")
            self.terminate()