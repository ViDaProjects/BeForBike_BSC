# createmsg.py
import sys
import signal
from PySide6.QtCore import QCoreApplication, Slot, QThread, QMutex
from queue import Queue,Empty
import logging
import json
from pathlib import Path

# Importe o novo RideState
from ride_state import RideState 

from comm_protocol import (
    FileManagerMsg, FileMngMsgId, RideDataMsg, 
    ProcessedDataMsg, TelemetryOrigin, TelemetryMsg
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MsgCreatorThread(QThread):
    def __init__(self, 
                 app, 
                 ride_state: RideState,        # <-- MUDANÇA: Recebe o estado
                 AddRideDataQueue=Queue, 
                 SendDataQueue=Queue, 
                 CreateMsgQueue=Queue, 
                 parent=None):
        super().__init__(parent)

        self.is_running = False
        self.ride_state = ride_state        

        self.AddRideDataQueue = AddRideDataQueue
        self.SendDataQueue = SendDataQueue
        self.CreateMsgQueue = CreateMsgQueue

        
        self.app = app
        self.msg = TelemetryMsg(info=None, gps=None, crank=None)        
        self.setObjectName("MsgCreatorThread")
        self.app.aboutToQuit.connect(self.stop)

    def start(self):
        if self.is_running:
            logging.warning("Thread MsgCreator já está em execução.")
            return
        self.is_running = True
        super().start()
        logging.info("Thread MsgCreator iniciada.")

    @Slot()
    def stop(self):
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
        while self.is_running:
            try:
                #try:
                #    self.crank_data = self.CrankQueue.get(timeout = 0.4)
                #    self.updated_crank_data = True
                #except:
                #    pass
                #try:
                #    self.gps_data = self.GpsQueue.get(timeout = 0.4)
                #    self.updated_gps_data = True
                #except:
                #    pass



                data = self.CreateMsgQueue.get(timeout=1) # Adicionado timeout
                origem = data.data_origin
                #logging.info(f"[Create Message]Mensagem recebida de CreateMsgQueue: {data.data_origin} ")
                #print("\n\n\n")

                match origem:
                    case TelemetryOrigin.GPS:
                        self.gps_data(data)
                    case TelemetryOrigin.CRANK:
                        self.crank_data(data)
                    case _:
                        logging.warning(f"Comando desconhecido recebido: {data}")
            
            except Empty: # Captura o timeout
                if not self.is_running:
                    break # Sai do loop se a thread foi parada
                continue # Continua o loop se apenas estiver vazio

            except Exception as e:
                logging.error(f"Erro na thread createmessage: {e}")

    def gps_data(self,data):
        try:

            self.msg.gps = data.data
            self.msg.info = data.info
            
            if self.ride_state.is_riding():
                return
            # send eventUI (lógica da UI aqui)
            self.msg.gps = None

                
        except Exception as e:
            logging.error(f"Erro em GPS data: {e}")
    
    def crank_data(self, data):
        try:
            if data.data is None:
                return
            self.msg.crank = data.data

            if self.msg.gps is not None and self.msg.crank is not None:

                # --- MUDANÇA: Verifica o estado centralizado ---
                if self.ride_state.is_riding():
                    logging.info("Dados de GPS e Crank recebidos (Corrida ATIVA). Montando e enviando mensagem.")
                    #print("\n\n\n\n\n\n\n")

                    msg_to_send = TelemetryMsg(
                        info=self.msg.info,
                        gps=self.msg.gps,
                        crank=self.msg.crank
                    )
                    self.AddRideDataQueue.put(msg_to_send)
                    logging.info(f"[Create Message]Mensagem enviada para AddRideDataQueue: {msg_to_send}")
                    #print("\n\n\n\n\n\n\n")
                    # Limpa apenas depois de enviar com sucesso
                    self.msg.gps = None
                    self.msg.info = None
                    self.msg.crank = None
            
            #else:
                #print("Aguardando mais dados para criar a mensagem...")
                # if not self.ride_state.is_riding():
                    # send eventUI EVENT (lógica da UI aqui)

        except Exception as e:
            logging.info(f"Erro no cranck: {e}")