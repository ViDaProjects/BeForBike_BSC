# main.py
import sys
import signal
import logging
from queue import Queue, Empty
from PySide6.QtCore import QCoreApplication, QThread, Slot

# Importe suas threads reais
from fileCreator.file_mannager import FileMannagerThread
from fileCreator.createmsg import MsgCreatorThread
from ride import RideThread 
from simula_ble import MockBleNanoThread

# Importe a nova classe de estado
from rideState import RideState 

from fileCreator.comm_protocol import (
    CrankData, GpsData, PacketInfo, 
    ProcessedDataMsg, TelemetryOrigin
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===================================================================
# PROCESSADORES "PONTE" (Inalterados, mas corrigidos da última vez)
# ===================================================================

class PlaceholderCrankProcessor(QThread):
    def __init__(self, process_q, create_q, parent=None):
        super().__init__(parent)
        self.process_crank_data_queue = process_q
        self.create_msg_queue = create_q
        self.is_running = True
        self.setObjectName("CrankProcessor")

    def run(self):
        logging.info("[CrankProc]: Iniciado.")
        while self.is_running:
            try:
                crank_dict = self.process_crank_data_queue.get(timeout=1)
                crank_obj = CrankData.from_dict(crank_dict)
                
                # Cria PacketInfo fictício (RideThread irá sobrescrever o ID)
                info = PacketInfo(ride_id=0, date="2025-11-11", time="22:00:00") 

                msg = ProcessedDataMsg(
                    data_origin=TelemetryOrigin.CRANK,
                    data=crank_obj,
                    info=info  # <-- Importante
                )
                self.create_msg_queue.put(msg)
            except Empty:
                continue
            except Exception as e:
                logging.error(f"[CrankProc]: Erro: {e}")
    
    def stop(self):
        self.is_running = False
        self.quit()
        self.wait(1000)

class PlaceholderGpsProcessor(QThread):
    def __init__(self, create_q, parent=None):
        super().__init__(parent)
        self.create_msg_queue = create_q
        self.is_running = True
        self.setObjectName("GpsProcessor")
        
    def run(self):
        logging.info("[GpsProc]: Iniciado (simulando dados de GPS).")
        while self.is_running:
            try:
                gps_obj = GpsData(
                    timestamp="2025-11-11T22:00:01Z", latitude=-25.4, longitude=-49.2,
                    altitude=900, speed=25, direction=120, fix_satellites=8, fix_quality=1
                )
                info = PacketInfo(ride_id=0, date="2025-11-11", time="22:00:01")
                
                msg = ProcessedDataMsg(
                    data_origin=TelemetryOrigin.GPS,
                    data=gps_obj,
                    info=info
                )
                self.create_msg_queue.put(msg)
                self.msleep(1000)
            except Exception as e:
                logging.error(f"[GpsProc]: Erro: {e}")

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait(1000)


# ===================================================================
# APLICAÇÃO PRINCIPAL DA SIMULAÇÃO
# ===================================================================

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    
    # --- 1. Criar o objeto de estado compartilhado ---
    shared_ride_state = RideState(app) # 'app' como pai

    # --- 2. Criar todas as filas ---
    add_ride_data_q = Queue()
    file_manager_q = Queue()
    send_ride_data_q = Queue()
    create_msg_q = Queue()
    process_crank_data_q = Queue()

    # --- 3. Criar as threads reais ---
    fm_thread = FileMannagerThread(
        app,
        file_manager_q,
        send_ride_data_q
    )
    
    # --- MUDANÇA: Passe o shared_ride_state ---
    msg_creator_thread = MsgCreatorThread(
        app,
        ride_state=shared_ride_state, 
        AddRideDataQueue=add_ride_data_q, 
        SendDataQueue=send_ride_data_q, 
        CreateMsgQueue=create_msg_q
    )
    
    # --- MUDANÇA: Passe o shared_ride_state ---
    ride_thread = RideThread(
        app,
        ride_state=shared_ride_state, 
        add_ride_data_queue=add_ride_data_q,
        file_manager_queue=file_manager_q,
        send_ride_data_queue=send_ride_data_q
    )

    # --- 4. Criar os processadores "ponte" ---
    crank_processor = PlaceholderCrankProcessor(process_crank_data_q, create_msg_q)
    gps_processor = PlaceholderGpsProcessor(create_msg_q)

    # --- 5. Criar o SIMULADOR ---
    mock_nano = MockBleNanoThread(
        process_crank_data_queue=process_crank_data_q,
        file_path="fileCreator/rides/Ride44.json"
    )

    # --- 6. Conectar SINAIS e SLOTS ---
    
    # Conexão FileMannager -> RideThread (Para obter o ID)
    fm_thread.id.connect(ride_thread.set_ride_id)

    # --- MUDANÇA: Conecte o simulador ao estado compartilhado ---
    mock_nano.nano_connected.connect(shared_ride_state.start_ride)
    mock_nano.nano_disconnected.connect(shared_ride_state.stop_ride)
    
    # Conexão para parar tudo
    app.aboutToQuit.connect(fm_thread.stop)
    app.aboutToQuit.connect(msg_creator_thread.stop)
    app.aboutToQuit.connect(ride_thread.stop) # <-- MUDANÇA: use o slot stop()
    app.aboutToQuit.connect(crank_processor.stop)
    app.aboutToQuit.connect(gps_processor.stop)
    app.aboutToQuit.connect(mock_nano.stop)


    # --- 7. Iniciar todas as threads ---
    logging.info("Iniciando todas as threads...")
    fm_thread.start()
    msg_creator_thread.start()
    ride_thread.start()
    crank_processor.start()
    gps_processor.start()
    
    mock_nano.start()
    
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logging.info("Simulação rodando. Pressione Ctrl+C para sair.")
    sys.exit(app.exec())