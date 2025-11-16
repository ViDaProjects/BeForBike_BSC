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
from comm_protocol import GpsSentenceType, GpsSentences
from bluetooth import BleManager
from createmsg import MsgCreatorThread
from file_manager import FileManagerThread
from ride import RideThread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sample NMEA data simulating a short path
# (Coordinates are for Curitiba, Brazil)
# A longer simulated path with 20 data points (GGA + RMC)
# This path continues the South-East movement from your original data.
SIM_NMEA_DATA = [
"$GNRMC,001353.000,A,2546.17898,S,4916.12660,W,0.490,47.25,130625,,,A,V*38",
"$GNGGA,001353.000,2546.17898,S,4916.12660,W,1,12,0.72,891.0,M,20.8,M,,0000*46",
"$GNRMC,001354.000,A,2546.17897,S,4916.12661,W,0.430,51.49,130625,,,A,V*36",
"$GNGGA,001354.000,2546.17897,S,4916.12661,W,1,12,0.72,890.8,M,20.8,M,,0000*46",
"$GNRMC,001355.000,A,2546.17897,S,4916.12667,W,0.350,53.45,130625,,,A,V*3E",
"$GNGGA,001355.000,2546.17897,S,4916.12667,W,1,12,0.72,890.4,M,20.8,M,,0000*4D",
"$GNRMC,001356.000,A,2546.17900,S,4916.12679,W,0.390,58.59,130625,,,A,V*37",
"$GNGGA,001356.000,2546.17900,S,4916.12679,W,1,12,0.72,890.0,M,20.8,M,,0000*4A",
"$GNRMC,001357.000,A,2546.17899,S,4916.12694,W,0.430,62.85,130625,,,A,V*31",
"$GNGGA,001357.000,2546.17899,S,4916.12694,W,1,12,0.72,889.4,M,20.8,M,,0000*45",
"$GNRMC,001358.000,A,2546.17898,S,4916.12708,W,0.420,66.27,130625,,,A,V*36",
"$GNGGA,001358.000,2546.17898,S,4916.12708,W,1,12,0.72,889.0,M,20.8,M,,0000*4B",
"$GNRMC,001359.000,A,2546.17898,S,4916.12725,W,0.450,70.73,130625,,,A,V*39",
"$GNGGA,001359.000,2546.17898,S,4916.12725,W,1,12,0.72,888.5,M,20.8,M,,0000*41",
"$GNRMC,001400.000,A,2546.17900,S,4916.12742,W,0.540,75.44,130625,,,A,V*32",
"$GNGGA,001400.000,2546.17900,S,4916.12742,W,1,12,0.72,887.9,M,20.8,M,,0000*48",
"$GNRMC,001401.000,A,2546.17900,S,4916.12763,W,0.690,79.89,130625,,,A,V*33",
"$GNGGA,001401.000,2546.17900,S,4916.12763,W,1,12,0.72,887.1,M,20.8,M,,0000*42",
"$GNRMC,001402.000,A,2546.17900,S,4916.12791,W,1.070,84.72,130625,,,A,V*32",
"$GNGGA,001402.000,2546.17900,S,4916.12791,W,1,12,0.72,886.2,M,20.8,M,,0000*4E",
"$GNRMC,001353.000,A,2546.17898,S,4916.12660,W,0.490,47.25,130625,,,A,V*38",
"$GNGGA,001353.000,2546.17898,S,4916.12660,W,1,12,0.72,891.0,M,20.8,M,,0000*46",
"$GNRMC,001354.000,A,2546.17897,S,4916.12661,W,0.430,51.49,130625,,,A,V*36",
"$GNGGA,001354.000,2546.17897,S,4916.12661,W,1,12,0.72,890.8,M,20.8,M,,0000*46",
"$GNRMC,001355.000,A,2546.17897,S,4916.12667,W,0.350,53.45,130625,,,A,V*3E",
"$GNGGA,001355.000,2546.17897,S,4916.12667,W,1,12,0.72,890.4,M,20.8,M,,0000*4D",
"$GNRMC,001356.000,A,2546.17900,S,4916.12679,W,0.390,58.59,130625,,,A,V*37",
"$GNGGA,001356.000,2546.17900,S,4916.12679,W,1,12,0.72,890.0,M,20.8,M,,0000*4A",
"$GNRMC,001357.000,A,2546.17899,S,4916.12694,W,0.430,62.85,130625,,,A,V*31",
"$GNGGA,001357.000,2546.17899,S,4916.12694,W,1,12,0.72,889.4,M,20.8,M,,0000*45",
"$GNRMC,001358.000,A,2546.17898,S,4916.12708,W,0.420,66.27,130625,,,A,V*36",
"$GNGGA,001358.000,2546.17898,S,4916.12708,W,1,12,0.72,889.0,M,20.8,M,,0000*4B",
"$GNRMC,001359.000,A,2546.17898,S,4916.12725,W,0.450,70.73,130625,,,A,V*39",
"$GNGGA,001359.000,2546.17898,S,4916.12725,W,1,12,0.72,888.5,M,20.8,M,,0000*41",
"$GNRMC,001400.000,A,2546.17900,S,4916.12742,W,0.540,75.44,130625,,,A,V*32",
"$GNGGA,001400.000,2546.17900,S,4916.12742,W,1,12,0.72,887.9,M,20.8,M,,0000*48",
"$GNRMC,001401.000,A,2546.17900,S,4916.12763,W,0.690,79.89,130625,,,A,V*33",
"$GNGGA,001401.000,2546.17900,S,4916.12763,W,1,12,0.72,887.1,M,20.8,M,,0000*42",
"$GNRMC,001402.000,A,2546.17900,S,4916.12791,W,1.070,84.72,130625,,,A,V*32",
"$GNGGA,001402.000,2546.17900,S,4916.12791,W,1,12,0.72,886.2,M,20.8,M,,0000*4E"
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

        #Queues
        self.process_gps_queue = Queue()
        self.add_ride_data_queue = Queue()
        self.send_ride_data_queue = Queue()
        self.process_crank_data_queue = Queue() #final crank data
        self.crank_reading_queue = Queue() #weight and aceleration
        self.create_msg_queue = Queue()
        self.file_manager_queue = Queue()

        #Threads
        #self.gps_gather_thread = GpsGatherThread(self.process_gps_queue)
        self.gps_processor_thread = GpsProcessorThread(self.process_gps_queue)
        #self.gps_tester_thread = TestGpsThread(self.show_data_queue)

        #Start threads
        #self.gps_gather_thread.start()
        self.gps_processor_thread.start()
        #self.gps_tester_thread.start()

        # --- Simulation Logic ---
        self._sim_index = 0
        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(2000) # Send new data every 2 seconds
        self.sim_timer.timeout.connect(self.send_sim_data)

        # Start the timer
        self.sim_timer.start()


        #For example, connect a button:
        self.ui.start_button.clicked.connect(self.map_widget.start_plotting)
        self.ui.stop_button.clicked.connect(self.map_widget.stop_plotting)

        #Connections
        self.gps_processor_thread.update_ui.connect(self.update_ui_with_msg_creator_data)
        self.blinker.blinkerActivated.connect(self.active_blinker_icon)
        self.blinker.worker.blinkerDeactivated.connect(self.deactive_blinker_icon)

    def closeEvent(self, event):
        #self.gps_gather_thread.stop()
        self.gps_processor_thread.stop()
        #self.gps_tester_thread.stop()
        event.accept()

    def send_sim_data(self):
        """Simulates receiving a NMEA sentence."""
        if self._sim_index < len(SIM_NMEA_DATA):
            sentence = SIM_NMEA_DATA[self._sim_index]
            logging.info(f"Simulating RX: {sentence}")
            type = None
            if sentence.startswith("$GNGGA"):
                type = GpsSentenceType.GGA
            elif sentence.startswith("$GNRMC"):
                type = GpsSentenceType.RMC
            else:
                # Log what was received that wasn't a recognized sentence
                #logging.debug("[GPS Gather] Unrecognized sentence: %s", newdata)
                pass

            sentence = GpsSentences(type=type, data=sentence)
            logging.debug("[GPS Gather] Got sentence: %s", sentence)
            self.process_gps_queue.put(sentence)
            #self.map_widget.process_nmea_sentence(sentence)
            self._sim_index += 1
        else:
            logging.info("End of simulation data.")
            self.sim_timer.stop()

    @Slot(TelemetryMsg)
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

        #Update GPS icon and write RTC at first fix
        if data.gps.fix_quality > 0 and not self.has_fix_position:
            pixmap = QPixmap("icons/gps_on.png")
            self.ui.gps_icon_label.setPixmap(pixmap)
            self.has_fix_position = True
            if self.its_first_fix:
                self.update_rtc_by_gps.emit()
                self.its_first_fix = False

        elif data.gps.fix_quality == 0 and self.has_fix_position:
            pixmap = QPixmap("icons/gps_off.png")
            self.ui.gps_icon_label.setPixmap(pixmap)
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
    def change_app_bt_icon(self, app_state):
        if app_state:
            pixmap = QPixmap("icons/app_bt_on.png")
            self.ui.crank_bt_label.setPixmap(pixmap)
        else:
            pixmap = QPixmap("icons/app_bt_off.png")
            self.ui.crank_bt_label.setPixmap(pixmap)

    @Slot()
    def change_crank_bt_icon(self, riding_state):
        if riding_state:
            pixmap = QPixmap("icons/crank_bt_on.png")
            self.ui.crank_bt_label.setPixmap(pixmap)
        else:
            pixmap = QPixmap("icons/crank_bt_off.png")
            self.ui.crank_bt_label.setPixmap(pixmap)
            self.clear_crank_data_labels()

    def clear_crank_data_labels(self):
        self.ui.power_label.setText("N/a") #W
        self.ui.cadence_label.setText("N/a") #RPM
        self.ui.speed_label.setText("--") #km/h
        self.ui.distance_label.setText("--") #m
        self.ui.calories_label.setText("--") #Kcal

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
