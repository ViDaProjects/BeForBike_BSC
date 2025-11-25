# createmsg.py
import sys
import signal
from PySide6.QtCore import QCoreApplication, Slot, QThread, QMutex, Signal
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
    update_ui = Signal(TelemetryMsg)  # Sinal para atualizar a UI com dados processados

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
                logging.warning("Waiting for data in CreateMsgQueue...")
                data = self.CreateMsgQueue.get(timeout=1) # Adicionado timeout
                origem = data.data_origin
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
            
            self.msg.crank = None
            logging.error("GPS data emitted to UI: %s", self.msg)
            self.update_ui.emit(self.msg) #Update UI even if not riding
            # send eventUI (lógica da UI aqui) 
        except Exception as e:
            logging.error(f"Erro em GPS data: {e}")
    
    def crank_data(self, data: ProcessedDataMsg):
        try:
            if data.data is None:
                logging.warning("[MsgCreator] ProcessedDataMsg from Crank, but no data is available")
                return
            
            self.msg.crank = data.data
            
            if self.msg.gps is not None and self.msg.crank is not None and self.msg.info is not None:

                # --- MUDANÇA: Verifica o estado centralizado ---
                if self.ride_state.is_riding():
                    logging.info("Dados de GPS e Crank recebidos (Corrida ATIVA). Montando e enviando mensagem.")

                    msg_to_send = TelemetryMsg(
                        info=self.msg.info,
                        gps=self.msg.gps,
                        crank=self.msg.crank
                    )
                    logging.debug("TelemetryMsg sent to RideThread and UI: %s", msg_to_send)
                    self.AddRideDataQueue.put(msg_to_send)
                    self.update_ui.emit(msg_to_send)

                    # Limpa apenas depois de enviar com sucesso
                    self.msg.gps = None
                    self.msg.info = None
                    self.msg.crank = None

                else:
                    logging.warning("[MsgCreator] TelemetryMsg data is not None, but the state is not riding. No data sent to UI and RideThread")
            
            else:
                logging.warning("[MsgCreator] Could not create TelemetryData. Current Msg is None")

        except Exception as e:
            logging.error(f"Erro no cranck: {e}")