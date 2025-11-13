# This Python file uses the following encoding: utf-8
import sys
import signal
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import QTimer, Slot, Signal
from PySide6.QtGui import QPixmap
from queue import Queue
import logging

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow
#from gps_map import MapWidget
from gps_system import GpsGatherThread, GpsProcessorThread, TestGpsThread, MapWidget
from comm_protocol import TelemetryMsg
from blinker_module import BlinkerSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sample NMEA data simulating a short path
# (Coordinates are for Curitiba, Brazil)
# A longer simulated path with 20 data points (GGA + RMC)
# This path continues the South-East movement from your original data.
SIM_NMEA_DATA = [
    # Point 1
    "$GPGGA,120001.00,2525.7040,S,04916.3980,W,1,08,0.9,900.0,M,0.0,M,,*7A",
    "$GPRMC,120001.00,A,2525.7040,S,04916.3980,W,1.5,130.0,301025,,,A*62",
    # Point 2
    "$GPGGA,120003.00,2525.7280,S,04916.3800,W,1,08,0.9,901.0,M,0.0,M,,*7D",
    "$GPRMC,120003.00,A,2525.7280,S,04916.3800,W,1.5,130.0,301025,,,A*6F",
    # Point 3
    "$GPGGA,120005.00,2525.7520,S,04916.3620,W,1,08,0.9,902.0,M,0.0,M,,*7E",
    "$GPRMC,120005.00,A,2525.7520,S,04916.3620,W,1.5,130.0,301025,,,A*6C",
    # Point 4
    "$GPGGA,120007.00,2525.7760,S,04916.3440,W,1,08,0.9,901.5,M,0.0,M,,*73",
    "$GPRMC,120007.00,A,2525.7760,S,04916.3440,W,1.5,130.0,301025,,,A*6B",
    # Point 5
    "$GPGGA,120009.00,2525.8000,S,04916.3260,W,1,08,0.9,900.5,M,0.0,M,,*7B",
    "$GPRMC,120009.00,A,2525.8000,S,04916.3260,W,1.5,130.0,301025,,,A*6D",
    # Point 6
    "$GPGGA,120011.00,2525.8240,S,04916.3080,W,1,08,0.9,900.0,M,0.0,M,,*7C",
    "$GPRMC,120011.00,A,2525.8240,S,04916.3080,W,1.5,130.0,301025,,,A*61",
    # Point 7
    "$GPGGA,120013.00,2525.8480,S,04916.2900,W,1,08,0.9,901.0,M,0.0,M,,*72",
    "$GPRMC,120013.00,A,2525.8480,S,04916.2900,W,1.5,130.0,301025,,,A*6F",
    # Point 8
    "$GPGGA,120015.00,2525.8720,S,04916.2720,W,1,08,0.9,902.0,M,0.0,M,,*71",
    "$GPRMC,120015.00,A,2525.8720,S,04916.2720,W,1.5,130.0,301025,,,A*6C",
    # Point 9
    "$GPGGA,120017.00,2525.8960,S,04916.2540,W,1,08,0.9,901.5,M,0.0,M,,*7C",
    "$GPRMC,120017.00,A,2525.8960,S,04916.2540,W,1.5,130.0,301025,,,A*6B",
    # Point 10
    "$GPGGA,120019.00,2525.9200,S,04916.2360,W,1,08,0.9,900.5,M,0.0,M,,*7F",
    "$GPRMC,120019.00,A,2525.9200,S,04916.2360,W,1.5,130.0,301025,,,A*6B",
    # Point 11
    "$GPGGA,120021.00,2525.9440,S,04916.2180,W,1,08,0.9,900.0,M,0.0,M,,*7C",
    "$GPRMC,120021.00,A,2525.9440,S,04916.2180,W,1.5,130.0,301025,,,A*6B",
    # Point 12
    "$GPGGA,120023.00,2525.9680,S,04916.2000,W,1,08,0.9,901.0,M,0.0,M,,*72",
    "$GPRMC,120023.00,A,2525.9680,S,04916.2000,W,1.5,130.0,301025,,,A*6C",
    # Point 13
    "$GPGGA,120025.00,2525.9920,S,04916.1820,W,1,08,0.9,902.0,M,0.0,M,,*71",
    "$GPRMC,120025.00,A,2525.9920,S,04916.1820,W,1.5,130.0,301025,,,A*6B",
    # Point 14
    "$GPGGA,120027.00,2526.0160,S,04916.1640,W,1,08,0.9,901.5,M,0.0,M,,*7C",
    "$GPRMC,120027.00,A,2526.0160,S,04916.1640,W,1.5,130.0,301025,,,A*6A",
    # Point 15
    "$GPGGA,120029.00,2526.0400,S,04916.1460,W,1,08,0.9,900.5,M,0.0,M,,*7B",
    "$GPRMC,120029.00,A,2526.0400,S,04916.1460,W,1.5,130.0,301025,,,A*6A",
    # Point 16
    "$GPGGA,120031.00,2526.0640,S,04916.1280,W,1,08,0.9,900.0,M,0.0,M,,*7A",
    "$GPRMC,120031.00,A,2526.0640,S,04916.1280,W,1.5,130.0,301025,,,A*6A",
    # Point 17
    "$GPGGA,120033.00,2526.0880,S,04916.1100,W,1,08,0.9,901.0,M,0.0,M,,*70",
    "$GPRMC,120033.00,A,2526.0880,S,04916.1100,W,1.5,130.0,301025,,,A*6F",
    # Point 18
    "$GPGGA,120035.00,2526.1120,S,04916.0920,W,1,08,0.9,902.0,M,0.0,M,,*73",
    "$GPRMC,120035.00,A,2526.1120,S,04916.0920,W,1.5,130.0,301025,,,A*6C",
    # Point 19
    "$GPGGA,120037.00,2526.1360,S,04916.0740,W,1,08,0.9,901.5,M,0.0,M,,*7E",
    "$GPRMC,120037.00,A,2526.1360,S,04916.0740,W,1.5,130.0,301025,,,A*69",
    # Point 20
    "$GPGGA,120039.00,2526.1600,S,04916.0560,W,1,08,0.9,900.5,M,0.0,M,,*70",
    "$GPRMC,120039.00,A,2526.1600,S,04916.0560,W,1.5,130.0,3301025,,,A*67",
]

class MainWindow(QMainWindow):
    update_rtc_by_gps = Signal()

    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Map
        self.map_widget = MapWidget()
        map_layout = QVBoxLayout(self.ui.map_frame)
        map_layout.addWidget(self.map_widget)

        #Blinker
        self.blinker = BlinkerSystem(app_instance)

        #variables
        self.has_fix_position: bool = False
        self.its_first_fix = True

        #For example, connect a button:
        self.ui.start_button.clicked.connect(self.map_widget.start_plotting)
        self.ui.stop_button.clicked.connect(self.map_widget.stop_plotting)

        #Queues
        self.process_gps_queue = Queue()
        #self.show_data_queue = Queue()

        #Threads
        self.gps_gather_thread = GpsGatherThread(self.process_gps_queue)
        self.gps_processor_thread = GpsProcessorThread(self.process_gps_queue)
        #self.gps_tester_thread = TestGpsThread(self.show_data_queue)

        #Start threads
        self.gps_gather_thread.start()
        self.gps_processor_thread.start()
        #self.gps_tester_thread.start()

        """# --- Simulation Logic ---
        self._sim_index = 0
        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(2000) # Send new data every 2 seconds
        self.sim_timer.timeout.connect(self.send_sim_data)

        # Send first data point immediately to center the map
        self.send_sim_data()
        # Start the timer
        self.sim_timer.start()"""

        #Connections
        self.gps_processor_thread.update_ui.connect(self.update_ui_with_msg_creator_data)
        self.blinker.blinkerActivated.connect(self.active_blinker_icon)
        self.blinker.worker.blinkerDeactivated.connect(self.deactive_blinker_icon)

    def closeEvent(self, event):
        self.gps_gather_thread.stop()
        self.gps_processor_thread.stop()
        self.gps_tester_thread.stop()
        event.accept()

    def send_sim_data(self):
        """Simulates receiving a NMEA sentence."""
        if self._sim_index < len(SIM_NMEA_DATA):
            sentence = SIM_NMEA_DATA[self._sim_index]
            print(f"Simulating RX: {sentence}")
            self.map_widget.process_nmea_sentence(sentence)
            self._sim_index += 1
        else:
            print("End of simulation data.")
            self.sim_timer.stop()

    @Slot()
    def update_ui_with_msg_creator_data(self, data: TelemetryMsg):

        #if is riding
        #atualizar labels do crank
        #if Not riding
        #labels with --

        #Ver o que mandei pro joao

        #gps
        #Update gps data: satellities and quality labels
        self.ui.satellities_label.setText(str(data.gps.fix_satellites))
        self.ui.fix_quality_label.setText(str(data.gps.fix_quality))

        #update map
        self.map_widget.update_map_plotting(data.gps.latitude, data.gps.longitude, data.gps.altitude)

        #Update GPS icon
        if data.gps.fix_quality > 0 and not self.has_fix_position:
            #set green icon -------------------------
            self.has_fix_position = True
            if self.its_first_fix:
                self.update_rtc_by_gps.emit()
                self.its_first_fix = False

        elif data.gps.fix_quality == 0 and self.has_fix_position:
            #set gray icon ---------------------------
            self.has_fix_position = False


    @Slot()
    def update_datetime_labels(self):
        pass

    @Slot(str)
    def active_blinker_icon(self, direction):
        if direction == "left":
            pixmap = QPixmap("icons/arrow_left_on.svg")
            self.ui.blinker_label_left.setPixmap(pixmap)
        elif direction == "right":
            pixmap = QPixmap("icons/arrow_right_on.svg")
            self.ui.blinker_label_right.setPixmap(pixmap)

    @Slot(str)
    def deactive_blinker_icon(self, direction):
        if direction == "left":
            pixmap = QPixmap("icons/arrow_left_off.svg")
            self.ui.blinker_label_left.setPixmap(pixmap)
        elif direction == "right":
            pixmap = QPixmap("icons/arrow_right_off.svg")
            self.ui.blinker_label_right.setPixmap(pixmap)

    @Slot()
    def change_app_bt_icon(self, state):
        pass

    @Slot()
    def change_crank_bt_icon(self, state):
        pass

    def clear_crank_data_labels(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Set the signal handler for SIGINT (Ctrl+C)
    # This allows Ctrl+C to be processed by the Python interpreter
    # while the Qt event loop is running.
    signal.signal(signal.SIGINT, signal.SIG_DFL) # <<< Add this line

    widget = MainWindow(app)
    widget.showFullScreen()

    logging.info("Running HMI")
    # 2. The try/except block is no longer necessary here
    # as the signal handler will handle the Ctrl+C directly.
    # The application will terminate correctly when SIGINT is received.
    sys.exit(app.exec())

#36px x 2.5px small icons
#88px x 3px arrows
#Cinza #8a9190
#Verde água mais escuro: #268071
#Verde água mais aberto:
