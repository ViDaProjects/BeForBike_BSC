from comm_protocol import GpsSentences, GpsSentenceType
from queue import Queue
from PySide6.QtCore import QThread, QCoreApplication, QTimer, Signal, Slot, QObject
import sys
import signal
import json
import time
import logging

DURACAO_COLETA_SEGUNDOS = 4 * 60 
ARQUIVO_SIMULACAO = "gps_data.json"


class GpsSimulator(QObject):
    """
    PRODUTOR: Roda na thread principal.
    Lê o arquivo JSON e, de tempo em tempo, envia uma linha
    bruta para a 'raw_gps_queue'.
    """
    def __init__(self, raw_gps_queue: Queue, parent=None):
        super().__init__(parent)
        self.raw_gps_queue = raw_gps_queue
        self.data_index = 0
        self.log = logging.getLogger("Simulator")
        try:
            with open(ARQUIVO_SIMULACAO, "r") as f:
                self.existing_data = json.load(f)
            self.log.info(f"Carregou {len(self.existing_data)} linhas de dados do {ARQUIVO_SIMULACAO}.")
        except Exception as e:
            self.log.error(f"Falha ao carregar {ARQUIVO_SIMULACAO}: {e}")
            self.existing_data = []

    @Slot()
    def send_next_line(self):
        """ Este Slot é chamado pelo QTimer. """
        if not self.existing_data:
            return

        try:
            line_data = self.existing_data[self.data_index]
            
            self.raw_gps_queue.put(line_data)
            
            self.data_index = (self.data_index + 1) 
            
        except Exception as e:
            if self.data_index == len(self.existing_data):
                return

            self.log.error(f"Erro ao enviar linha: {e}")
            #self.data_index = 0


class GpsProcessorThread(QThread):
    """
    CONSUMIDOR: Roda em uma thread separada.
    1. Pega dados da 'raw_gps_queue' (Fila 1)
    2. Filtra pelos termos de interesse (GGA/RMC)
    3. Cria o dataclass 'GpsSentence'
    4. Coloca o dataclass na 'processed_gps_queue' (Fila 2)
    """
    def __init__(self, raw_queue: Queue, processed_queue: Queue, parent=None):
        super().__init__(parent) 
        self.raw_gps_queue = raw_queue
        self.processed_gps_queue = processed_queue
        self.is_running = True
        self.setObjectName("GpsProcessorThread")

    def run(self):
        
        while self.is_running:
            try:
                raw_string = self.raw_gps_queue.get() 
                if raw_string is None:
                    continue 
                for i in raw_string:

                    if i.startswith('$GNGGA'):
                        sentence_type = GpsSentenceType.GGA
                    elif i.startswith('$GNRMC'):
                        sentence_type = GpsSentenceType.RMC
                    else:
                        continue 
                
                    sentence_obj = GpsSentences(type=sentence_type, data=i)
                
                    self.processed_gps_queue.put(sentence_obj)
                
                    logging.info(f"Processado e enfileirado: {sentence_obj.data}")
                    
            except Exception as e:
                self.log.error(f"Erro no loop: {e}")
        
        self.log.info("Loop 'run' finalizado.")
        
    def stop(self):
        self.log.warning("Recebido sinal de parada.")
        self.is_running = False
        self.raw_gps_queue.put(None) 


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    app = QCoreApplication(sys.argv)
    log = logging.getLogger("Main")
    

    raw_gps_queue = Queue()      
    processed_gps_queue = Queue() 

    simulator = GpsSimulator(raw_gps_queue)

    processor_thread = GpsProcessorThread(raw_gps_queue, processed_gps_queue)

    send_timer = QTimer()
    send_timer.timeout.connect(simulator.send_next_line)

    app.aboutToQuit.connect(processor_thread.stop)
    signal.signal(signal.SIGINT, signal.SIG_DFL) 


    try:
        processor_thread.start()
        send_timer.start(DURACAO_COLETA_SEGUNDOS)
        
        log.info("Loop de eventos do Qt iniciado. Pressione Ctrl+C para parar.")
        status = app.exec()
        log.info(f"Loop de eventos terminado com status {status}.")

    finally:
        if processor_thread.isRunning():
            log.info("Solicitando parada da thread...")
            processor_thread.stop()
            processor_thread.wait(2000)
            
        log.info("Script finalizado.")
        sys.exit(status)