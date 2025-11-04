
# This Python file uses the following encoding: utf-8
import sys
import signal
from PySide6.QtCore import QCoreApplication, QObject, Slot, QThread, QSocketNotifier, QTimer
from queue import Queue
import logging
import json
from pathlib import Path
from comm_protocol import FileManagerMsg,FileMngMsgId,RideDataMsg,ProcessedDataMsg,TelemetryOrigin,TelemetryMsg


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MsgCreatorThread(QThread):
    def __init__(self, app,riding,  AddRideDataQueue=Queue, SendDataQueue=Queue,CreateMsgQueue=Queue,parent=None):
        super().__init__(parent)

        self.is_running = False

        self.AddRideDataQueue = AddRideDataQueue
        self.SendDataQueue = SendDataQueue
        self.CreateMsgQueue = CreateMsgQueue

        self.riding = riding
        self.app = app
        self.msg = TelemetryMsg(info=None, gps=None, crank=None)        

        self.setObjectName("MsgCreatorThread")


        self.app.aboutToQuit.connect(self.stop)

    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("Thread MsgCreator já está em execução.")
            return
            
        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("Thread MsgCreator iniciada.")

    @Slot()
    def stop(self):
        """
        Para a thread de forma limpa.
        """
        if not self.is_running:
            return
            
        logging.warning("Parando a thread MsgCreator...")
        self.is_running = False  
        
        self.quit() 
        

        if not self.wait(5000):
             logging.error("Thread MsgCreator não respondeu. Forçando finalização.")
             self.terminate() 
        else:
             logging.info("Thread MsgCreator finalizada com sucesso.")

    def run(self):
        """
        Este é o coração da thread. O código aqui dentro
        executa no novo processo de thread.
        """
        while self.is_running:
            try:
                data = self.CreateMsgQueue.get()
                origem = data.data_origin
                match origem:
                    case TelemetryOrigin.GPS:
                        self.gps_data(data)
                    case TelemetryOrigin.CRANK:
                        self.cranck_data(data)
                    case _:
                        logging.warning(f"Comando desconhecido recebido: {data}")

                self.msleep(100) 

            except Exception as e:
                self.msleep(100)

                if "Empty" in str(e): 
                    pass 
                else:
                    logging.error(f"Erro na thread createmessage: {e}")

    def gps_data(self,data):
     
        try:
            self.msg.crank = data.data
            self.msg.info = data.info
            if self.riding:
                return
            
            #send eventUI

        except Exception as e:
            logging.error(f"Erro em GPS data: {e}")
    
    def cranck_data(self, data):
        try:
            if data.data is None:
                return
            self.msg.crank = data.data
            
            if self.msg.gps is not None and self.msg.crank is not None and self.msg.info is not None:
                logging.info("Dados de GPS e Crank recebidos. Montando e enviando mensagem.")
                self.AddRideDataQueue.put(self.msg)
            
            #send eventUI EVENT

        except Exception as e:
            logging.error(f"Erro no cranck: {e}")


  
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    # Crie todas as filas necessárias
    AddRideDataQueue = Queue()
    SendDataQueue = Queue()
    CreateMsgQueue = Queue() 

    riding_status = True 

    msg_creator = MsgCreatorThread(app, riding_status, AddRideDataQueue, SendDataQueue, CreateMsgQueue)



    signal.signal(signal.SIGINT, signal.SIG_DFL)

    print("Running HMI")
    msg_creator.start() 
    sys.exit(app.exec())