import sys
import signal
import logging
import os
from PySide6.QtCore import QCoreApplication, QObject, Slot, QThread, QSocketNotifier, QTimer
# Importe o BleManager refatorado
from bluetooth import BleManager
import json
from queue import Queue
from datetime import datetime
from comm_protocol import FileManagerMsg, FileMngMsgId, RideDataMsg
import json
from file_mannager import FileMannagerThread

# --- Constantes ---
FIXED_PERIPHERAL_MAC = "01:23:45:67:90:E7"
COMPANY_ID = 0xF0F0
SECRET_KEY = b"Oficinas3"

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- A CLASSE BluetoothController FOI REMOVIDA ---
# Ela não é mais necessária, pois BleManager agora é uma QThread
# e pode ser instanciada e iniciada diretamente.

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)

    # --- Criação das Filas (Queues) ---
    sendRideDataQueue = Queue()
    ProcessCrankDataQueue = Queue()
    FileManagerQueue = Queue()

    manager = FileMannagerThread(app, FileManagerQueue=FileManagerQueue,
                                 SendDataQueue=sendRideDataQueue,
                                 CreateMsgQueue=ProcessCrankDataQueue)


    ble_manager = BleManager(
        fixed_mac=FIXED_PERIPHERAL_MAC,
        company_id=COMPANY_ID,
        secret_key=SECRET_KEY,
        sendRideDataQueue=sendRideDataQueue,
        ProcessCrankDataQueue=ProcessCrankDataQueue,
        FileManagerQueue=FileManagerQueue,
        parent=app  
    )


    app.aboutToQuit.connect(manager.stop)
    app.aboutToQuit.connect(ble_manager.stop)


    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # --- Inicia as Threads ---
    manager.start()
    ble_manager.start()  # <-- Inicia a thread do Bluetooth

    logging.info("Serviço no ar. Loop de eventos principal iniciado.")
    sys.exit(app.exec())