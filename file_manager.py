
# This Python file uses the following encoding: utf-8
import sys
import signal
from PySide6.QtCore import QCoreApplication, Slot, QThread, QSocketNotifier, QTimer,Signal
from queue import Queue
import logging
import json
from pathlib import Path
from comm_protocol import FileManagerMsg,FileMngMsgId,RideDataMsg


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class FileManagerThread(QThread):
    id = Signal(int)
    def __init__(self, app,  FileManagerQueue=Queue, SendDataQueue=Queue,parent=None):
        super().__init__(parent)

        self.is_running = False

        self.FileManagerQueue = FileManagerQueue
        self.SendDataQueue = SendDataQueue
       
        self.pasta_alvo = Path(__file__).resolve().parent / "rides"
        self.count_rides_file = self.pasta_alvo / "ride_count.txt"
        self.app = app


        self.setObjectName("FileManagerThread")


        self.app.aboutToQuit.connect(self.stop)

    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("Thread FileManager já está em execução.")
            return
            
        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("Thread FileManager iniciada.")

    @Slot()
    def stop(self):
        """
        Para a thread de forma limpa.
        """
        if not self.is_running:
            return
            
        logging.warning("Parando a thread FileManager...")
        self.is_running = False  
        
        self.quit() 
        

        if not self.wait(5000):
             logging.error("Thread FileManager não respondeu. Forçando finalização.")
             self.terminate() 
        else:
             logging.info("Thread FileManager finalizada com sucesso.")

    def run(self):
        """
        Este é o coração da thread. O código aqui dentro
        executa no novo processo de thread.
        """
        while self.is_running:
            try:
                data = self.FileManagerQueue.get()
                comando = data.msg_id
                match comando:
                    case FileMngMsgId.CREATE_FILE:
                        self.save_data(data.file_name,data.telemetry_list)
                    case FileMngMsgId.DELETE_FILE:
                        self.delete_file(data.file_name)
                    case FileMngMsgId.SEARCH_FILES:
                        self.search_file()
                    case FileMngMsgId.GET_RIDE_ID:
                        self.get_id()
                    case _:
                        logging.warning(f"Comando desconhecido recebido: {data}")

                self.msleep(100) 

            except Exception as e:
                self.msleep(100)

                if "Empty" in str(e): 
                    pass 
                else:
                    logging.error(f"Erro na thread FileManager: {e}")
    
    def get_id(self):
        try:
            if not self.count_rides_file.exists():
                with open(self.count_rides_file, "w") as file:
                    file.write("0")
            
            with open(self.count_rides_file, "r+") as file:
                current_id = int(file.read().strip())
                new_id = current_id + 1
                file.seek(0)
                file.write(str(new_id))
                file.truncate()
            

            self.id.emit(new_id)

        except Exception as e:
            logging.error(f"Erro ao obter ID da ride: {e}")

    def save_data(self,file_name, lista_dados):
        
        try:
            logging.info(f"salvando dados")

            full_path = self.pasta_alvo / file_name
            with open(full_path, "w",encoding="UTF-8") as file:
                logging.info(f"salvando dados em {full_path}")
                json.dump(lista_dados, file, indent=4) # indent=4 é opcional (para legibilidade)               
        except Exception as e:
            logging.error(f"Erro ao salvar dados em {file_name}: {e}")
    
    def delete_file(self, file_name):
        try:
            file_path = self.pasta_alvo / file_name
            file_path.unlink() 
            logging.info(f"Arquivo {file_name} deletado com sucesso.")
            
        except FileNotFoundError:
            logging.warning(f"Arquivo {file_name} não encontrado para deleção.")
        except Exception as e:
            logging.error(f"Erro ao deletar arquivo {file_name}: {e}")



    def search_file(self):
        try:
            for arquivo in self.pasta_alvo.glob("*.json"):
                #data.file_name = arquivo.name
                #data_list = [{"filename":arquivo.name}]
                with arquivo.open('r', encoding='utf-8') as file:
                    try:
                        logging.info(f"Arquivo encontrado")

                        #telemetry_log = [json.dumps(item) for item in json.load(file)]
                        telemetry_log = json.load(file)
                        #for i in telemetry_log: 
                        #    print(i,type(i))
                        data = RideDataMsg(file_name=arquivo.name, telemetry_log=telemetry_log)

                        #data_list.extend(json.load(file))
                    except json.JSONDecodeError as e:
                        logging.error(f"Erro ao procurar o arquivo ride.json: {e}")

                if len(data.telemetry_log) is not None:
                    self.SendDataQueue.put(data)

        except FileNotFoundError:
            logging.error("Pasta de rides não encontrada.")

        except Exception as e:
            logging.error(f"Erro ao deletar arquivo ride.json: {e}")

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    
    FileManagerQueue=Queue()
    SendDataQueue=Queue()
    ble_controler = FileManagerThread(app,FileManagerQueue,SendDataQueue)
    # 1. Set the signal handler for SIGINT (Ctrl+C)
    # This allows Ctrl+C to be processed by the Python interpreter
    # while the Qt event loop is running.
    signal.signal(signal.SIGINT, signal.SIG_DFL) # <<< Add this line



    print("Running HMI")
    # 2. The try/except block is no longer necessary here
    # as the signal handler will handle the Ctrl+C directly.
    # The application will terminate correctly when SIGINT is received.
    sys.exit(app.exec())
