# This Python file uses the following encoding: utf-8
import sys
import signal
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import QTimer, Slot, Signal, QLocale
from PySide6.QtGui import QPixmap
from queue import Queue
import logging

from clock_updater import DateChangeWatcher, GPSClock
from datetime import datetime


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow
#from gps_map import MapWidget
from gps_system import GpsGatherThread, GpsProcessorThread, TestGpsThread, MapWidget
from comm_protocol import TelemetryMsg, CrankData, GpsData
from blinker_module import BlinkerSystem
from comm_protocol import GpsSentenceType, GpsSentences
from bluetooth import BleManager
from crank_parser import CrankParser
from crank_processor import CrankProcessor
from createmsg import MsgCreatorThread
from file_manager import FileManagerThread
from ride import RideThread
from ride_state import RideState
import qdarktheme

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sample NMEA data simulating a short path
# (Coordinates are for Curitiba, Brazil)
# A longer simulated path with 20 data points (GGA + RMC)
# This path continues the South-East movement from your original data.
SIM_NMEA_DATA = [
  "$GNRMC,130252.00,A,2526.16833,S,04916.13352,W,1.450,,191125,,,A*69",
  "$GNGGA,130252.00,2526.16833,S,04916.13352,W,1,08,2.64,970.6,M,-2.5,M,,*50",
  "$GNRMC,130253.00,A,2526.16783,S,04916.13351,W,1.608,,191125,,,A*60",
  "$GNGGA,130253.00,2526.16783,S,04916.13351,W,1,08,2.64,970.5,M,-2.5,M,,*55",
  "$GNRMC,130254.00,A,2526.16728,S,04916.13374,W,1.723,,191125,,,A*69",
  "$GNGGA,130254.00,2526.16728,S,04916.13374,W,1,08,2.64,970.4,M,-2.5,M,,*55",
  "$GNRMC,130255.00,A,2526.16893,S,04916.13381,W,0.965,,191125,,,A*60",
  "$GNGGA,130255.00,2526.16893,S,04916.13381,W,1,08,1.07,970.3,M,-2.5,M,,*50",
  "$GNRMC,130256.00,A,2526.16843,S,04916.13374,W,1.126,,191125,,,A*6A",
  "$GNGGA,130256.00,2526.16843,S,04916.13374,W,1,08,1.07,970.2,M,-2.5,M,,*55",
  "$GNRMC,130257.00,A,2526.16838,S,04916.13372,W,0.977,,191125,,,A*6C",
  "$GNGGA,130257.00,2526.16838,S,04916.13372,W,1,08,1.07,970.1,M,-2.5,M,,*5D",
  "$GNRMC,130258.00,A,2526.17070,S,04916.13469,W,0.308,,191125,,,A*69",
  "$GNGGA,130258.00,2526.17070,S,04916.13469,W,1,09,1.03,969.2,M,-2.5,M,,*54",
  "$GNRMC,130259.00,A,2526.17015,S,04916.13471,W,0.637,,191125,,,A*6B",
  "$GNGGA,130259.00,2526.17015,S,04916.13471,W,1,09,1.03,969.1,M,-2.5,M,,*5C",
  "$GNRMC,130300.00,A,2526.16962,S,04916.13469,W,0.869,,191125,,,A*62",
  "$GNGGA,130300.00,2526.16962,S,04916.13469,W,1,09,1.03,969.1,M,-2.5,M,,*50",
  "$GNRMC,130301.00,A,2526.16814,S,04916.13442,W,0.721,,191125,,,A*69",
  "$GNGGA,130301.00,2526.16814,S,04916.13442,W,1,04,2.24,968.6,M,-2.5,M,,*55",
  "$GNRMC,130302.00,A,2526.16781,S,04916.13429,W,0.805,,191125,,,A*6D",
  "$GNGGA,130302.00,2526.16781,S,04916.13429,W,1,04,2.24,968.5,M,-2.5,M,,*5B",
  "$GNRMC,130252.00,A,2526.16833,S,04916.13352,W,1.450,,191125,,,A*69",
  "$GNGGA,130252.00,2526.16833,S,04916.13352,W,1,08,2.64,970.6,M,-2.5,M,,*50",
  "$GNRMC,130253.00,A,2526.16783,S,04916.13351,W,1.608,,191125,,,A*60",
  "$GNGGA,130253.00,2526.16783,S,04916.13351,W,1,08,2.64,970.5,M,-2.5,M,,*55",
  "$GNRMC,130254.00,A,2526.16728,S,04916.13374,W,1.723,,191125,,,A*69",
  "$GNGGA,130254.00,2526.16728,S,04916.13374,W,1,08,2.64,970.4,M,-2.5,M,,*55",
  "$GNRMC,130255.00,A,2526.16893,S,04916.13381,W,0.965,,191125,,,A*60",
  "$GNGGA,130255.00,2526.16893,S,04916.13381,W,1,08,1.07,970.3,M,-2.5,M,,*50",
  "$GNRMC,130256.00,A,2526.16843,S,04916.13374,W,1.126,,191125,,,A*6A",
  "$GNGGA,130256.00,2526.16843,S,04916.13374,W,1,08,1.07,970.2,M,-2.5,M,,*55",
  "$GNRMC,130257.00,A,2526.16838,S,04916.13372,W,0.977,,191125,,,A*6C",
  "$GNGGA,130257.00,2526.16838,S,04916.13372,W,1,08,1.07,970.1,M,-2.5,M,,*5D",
  "$GNRMC,130258.00,A,2526.17070,S,04916.13469,W,0.308,,191125,,,A*69",
  "$GNGGA,130258.00,2526.17070,S,04916.13469,W,1,09,1.03,969.2,M,-2.5,M,,*54",
  "$GNRMC,130259.00,A,2526.17015,S,04916.13471,W,0.637,,191125,,,A*6B",
  "$GNGGA,130259.00,2526.17015,S,04916.13471,W,1,09,1.03,969.1,M,-2.5,M,,*5C",
  "$GNRMC,130300.00,A,2526.16962,S,04916.13469,W,0.869,,191125,,,A*62",
  "$GNGGA,130300.00,2526.16962,S,04916.13469,W,1,09,1.03,969.1,M,-2.5,M,,*50",
  "$GNRMC,130301.00,A,2526.16814,S,04916.13442,W,0.721,,191125,,,A*69",
  "$GNGGA,130301.00,2526.16814,S,04916.13442,W,1,04,2.24,968.6,M,-2.5,M,,*55",
  "$GNRMC,130302.00,A,2526.16781,S,04916.13429,W,0.805,,191125,,,A*6D",
  "$GNGGA,130302.00,2526.16781,S,04916.13429,W,1,04,2.24,968.5,M,-2.5,M,,*5B",
    "$GNRMC,130252.00,A,2526.16833,S,04916.13352,W,1.450,,191125,,,A*69",
  "$GNGGA,130252.00,2526.16833,S,04916.13352,W,1,08,2.64,970.6,M,-2.5,M,,*50",
  "$GNRMC,130253.00,A,2526.16783,S,04916.13351,W,1.608,,191125,,,A*60",
  "$GNGGA,130253.00,2526.16783,S,04916.13351,W,1,08,2.64,970.5,M,-2.5,M,,*55",
  "$GNRMC,130254.00,A,2526.16728,S,04916.13374,W,1.723,,191125,,,A*69",
  "$GNGGA,130254.00,2526.16728,S,04916.13374,W,1,08,2.64,970.4,M,-2.5,M,,*55",
  "$GNRMC,130255.00,A,2526.16893,S,04916.13381,W,0.965,,191125,,,A*60",
  "$GNGGA,130255.00,2526.16893,S,04916.13381,W,1,08,1.07,970.3,M,-2.5,M,,*50",
  "$GNRMC,130256.00,A,2526.16843,S,04916.13374,W,1.126,,191125,,,A*6A",
  "$GNGGA,130256.00,2526.16843,S,04916.13374,W,1,08,1.07,970.2,M,-2.5,M,,*55",
  "$GNRMC,130257.00,A,2526.16838,S,04916.13372,W,0.977,,191125,,,A*6C",
  "$GNGGA,130257.00,2526.16838,S,04916.13372,W,1,08,1.07,970.1,M,-2.5,M,,*5D",
  "$GNRMC,130258.00,A,2526.17070,S,04916.13469,W,0.308,,191125,,,A*69",
  "$GNGGA,130258.00,2526.17070,S,04916.13469,W,1,09,1.03,969.2,M,-2.5,M,,*54",
  "$GNRMC,130259.00,A,2526.17015,S,04916.13471,W,0.637,,191125,,,A*6B",
  "$GNGGA,130259.00,2526.17015,S,04916.13471,W,1,09,1.03,969.1,M,-2.5,M,,*5C",
  "$GNRMC,130300.00,A,2526.16962,S,04916.13469,W,0.869,,191125,,,A*62",
  "$GNGGA,130300.00,2526.16962,S,04916.13469,W,1,09,1.03,969.1,M,-2.5,M,,*50",
  "$GNRMC,130301.00,A,2526.16814,S,04916.13442,W,0.721,,191125,,,A*69",
  "$GNGGA,130301.00,2526.16814,S,04916.13442,W,1,04,2.24,968.6,M,-2.5,M,,*55",
  "$GNRMC,130302.00,A,2526.16781,S,04916.13429,W,0.805,,191125,,,A*6D",
  "$GNGGA,130302.00,2526.16781,S,04916.13429,W,1,04,2.24,968.5,M,-2.5,M,,*5B",
  "$GNRMC,130252.00,A,2526.16833,S,04916.13352,W,1.450,,191125,,,A*69",
  "$GNGGA,130252.00,2526.16833,S,04916.13352,W,1,08,2.64,970.6,M,-2.5,M,,*50",
  "$GNRMC,130253.00,A,2526.16783,S,04916.13351,W,1.608,,191125,,,A*60",
  "$GNGGA,130253.00,2526.16783,S,04916.13351,W,1,08,2.64,970.5,M,-2.5,M,,*55",
  "$GNRMC,130254.00,A,2526.16728,S,04916.13374,W,1.723,,191125,,,A*69",
  "$GNGGA,130254.00,2526.16728,S,04916.13374,W,1,08,2.64,970.4,M,-2.5,M,,*55",
  "$GNRMC,130255.00,A,2526.16893,S,04916.13381,W,0.965,,191125,,,A*60",
  "$GNGGA,130255.00,2526.16893,S,04916.13381,W,1,08,1.07,970.3,M,-2.5,M,,*50",
  "$GNRMC,130256.00,A,2526.16843,S,04916.13374,W,1.126,,191125,,,A*6A",
  "$GNGGA,130256.00,2526.16843,S,04916.13374,W,1,08,1.07,970.2,M,-2.5,M,,*55",
  "$GNRMC,130257.00,A,2526.16838,S,04916.13372,W,0.977,,191125,,,A*6C",
  "$GNGGA,130257.00,2526.16838,S,04916.13372,W,1,08,1.07,970.1,M,-2.5,M,,*5D",
  "$GNRMC,130258.00,A,2526.17070,S,04916.13469,W,0.308,,191125,,,A*69",
  "$GNGGA,130258.00,2526.17070,S,04916.13469,W,1,09,1.03,969.2,M,-2.5,M,,*54",
  "$GNRMC,130259.00,A,2526.17015,S,04916.13471,W,0.637,,191125,,,A*6B",
  "$GNGGA,130259.00,2526.17015,S,04916.13471,W,1,09,1.03,969.1,M,-2.5,M,,*5C",
  "$GNRMC,130300.00,A,2526.16962,S,04916.13469,W,0.869,,191125,,,A*62",
  "$GNGGA,130300.00,2526.16962,S,04916.13469,W,1,09,1.03,969.1,M,-2.5,M,,*50",
  "$GNRMC,130301.00,A,2526.16814,S,04916.13442,W,0.721,,191125,,,A*69",
  "$GNGGA,130301.00,2526.16814,S,04916.13442,W,1,04,2.24,968.6,M,-2.5,M,,*55",
  "$GNRMC,130302.00,A,2526.16781,S,04916.13429,W,0.805,,191125,,,A*6D",
  "$GNGGA,130302.00,2526.16781,S,04916.13429,W,1,04,2.24,968.5,M,-2.5,M,,*5B"
]

class MainWindow(QMainWindow):
    update_rtc_by_gps = Signal(datetime)

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
        self.is_riding: bool = False

        #Queues
        self.add_ride_data_queue = Queue()
        self.send_ride_data_queue = Queue()
        self.process_gps_queue = Queue()
        self.process_crank_data_queue = Queue() #final crank data
        self.crank_reading_queue = Queue() #weight and aceleration
        self.create_msg_queue = Queue()
        self.file_manager_queue = Queue()

        #Threads
        #Comment this line if needs to use simulated GPS
        self.gps_gather_thread = GpsGatherThread(self.process_gps_queue)
        self.gps_processor_thread = GpsProcessorThread(self.process_gps_queue, self.create_msg_queue)
        #self.gps_tester_thread = TestGpsThread(self.show_data_queue)
        self.clear_crank_data_labels()

        self.bluetooth_thread = BleManager(
            sendRideDataQueue =self.send_ride_data_queue,
            ProcessCrankDataQueue =self.crank_reading_queue,
            FileManagerQueue= self.file_manager_queue)
        
        #Simulated crank data
        #from teste.ride.simula_ble import MockBleNanoThread
        #ride_path = "/home/oficinas3/david/BeForBike_BSC/teste/ride/fileCreator/rides/Ride44.json"
        #ride_path = "/home/viviane/Documents/Oficinas3/BeForBike_BSC/teste/ride/fileCreator/rides/ride_46.json"
        #self.bluetooth_thread = MockBleNanoThread(self.create_msg_queue, ride_path)
        
        self.shared_ride_state = RideState(app_instance)
        self.ride_thread = RideThread(
            app=app_instance,
            ride_state=self.shared_ride_state,          
            add_ride_data_queue=self.add_ride_data_queue,
            file_manager_queue=self.file_manager_queue,
            send_ride_data_queue=self.send_ride_data_queue
        )

        self.file_manager_thread = FileManagerThread(
            app=app_instance,
            FileManagerQueue=self.file_manager_queue, 
            SendDataQueue=self.send_ride_data_queue
            )
        
        self.msg_creator_thread = MsgCreatorThread(
            app=app_instance,
            ride_state=self.shared_ride_state,
            AddRideDataQueue=self.add_ride_data_queue,
            SendDataQueue=self.send_ride_data_queue,
            CreateMsgQueue=self.create_msg_queue,
        )

        self.crank_parser_thread = CrankParser(
            in_queue=self.crank_reading_queue,
            out_queue=self.process_crank_data_queue
        )

        self.crank_processor_thread = CrankProcessor(
            in_queue=self.process_crank_data_queue,
            out_queue=self.create_msg_queue
        )

        self.date_watcher = DateChangeWatcher()
        self.date_watcher.dateChanged.connect(self.update_datetime_labels)
        self.date_watcher.emit_text()

        # Connect is riding: 
# Conexão na sua Classe Controladora Principal
        self.bluetooth_thread.crank_connection_status.connect(self.shared_ride_state.set_ride_status)
        self.shared_ride_state.state_changed.connect(self.change_crank_bt_icon)
        self.shared_ride_state.state_changed.connect(self._on_ride_state_change) 
        self.shared_ride_state.state_changed.connect(self.map_widget.change_plotting_state)       
        self.bluetooth_thread.app_connection_status.connect(self.change_app_bt_icon)
        self.update_rtc_by_gps.connect(self.update_clock_from_gps)
        self.file_manager_thread.id.connect(self.ride_thread.set_ride_id)
        #Connections
        

        #Msg Creator update UI with current TelemetryMsg
        self.msg_creator_thread.update_ui.connect(self.update_ui_with_msg_creator_data)
        
      
        self.blinker.blinkerActivated.connect(self.active_blinker_icon)
        self.blinker.worker.blinkerDeactivated.connect(self.deactive_blinker_icon)
        '''
        # --- Simulation Logic ---
        self._sim_index = 0
        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(1000) # Send new data every 2 seconds
        self.sim_timer.timeout.connect(self.send_sim_data)
        
        # Start the timer
        self.sim_timer.start()
        '''

        #Start threads
        self.gps_gather_thread.start()
        self.gps_processor_thread.start()

        self.ride_thread.start()
        self.file_manager_thread.start()
        self.msg_creator_thread.start()
        self.crank_parser_thread.start()
        self.crank_processor_thread.start()

        self.bluetooth_thread.msleep(1000)  # Aguarda meio segundo para garantir que o Bluetooth esteja pronto
        self.bluetooth_thread.start()

    def closeEvent(self, event):
        self.gps_gather_thread.stop()
        self.gps_processor_thread.stop()
        #self.gps_tester_thread.stop()
        self.bluetooth_thread.stop()
        self.ride_thread.stop()
        self.file_manager_thread.stop()
        self.msg_creator_thread.stop()
        self.crank_parser_thread.stop()
        self.crank_processor_thread.stop()

        event.accept()

    def send_sim_data(self):
        """Simulates receiving a NMEA sentence."""
        if self._sim_index < len(SIM_NMEA_DATA):
            sentence = SIM_NMEA_DATA[self._sim_index]
            logging.info(f"[GPS Simulator] Simulating RX: {sentence}")
            type = None
            if sentence.startswith("$GNGGA"):
                type = GpsSentenceType.GGA
            elif sentence.startswith("$GNRMC"):
                type = GpsSentenceType.RMC
            else:
                # Log what was received that wasn't a recognized sentence
                #logging.debug("[GPS Simulator] Unrecognized sentence: %s", newdata)
                pass

            sentence = GpsSentences(type=type, data=sentence)
            logging.debug("[GPS Simulator] Got sentence: %s", sentence)
            self.process_gps_queue.put(sentence)
            #self.map_widget.process_nmea_sentence(sentence)
            self._sim_index += 1
        else:
            logging.info("[GPS Simulator] End of simulation data.")
            self.sim_timer.stop()

    @Slot(bool)
    def _on_ride_state_change(self, is_riding: bool):
        logging.info(f"[MainWindow] The riding state has changed, it is now: {is_riding}")
        self.is_riding = is_riding

    @Slot(TelemetryMsg)
    def update_ui_with_msg_creator_data(self, data: TelemetryMsg):
        logging.info("[MainWindow] Updating UI with new telemetry data.")
        
        #update labels of crank data
        if self.is_riding and isinstance(data.crank, CrankData):
            self.ui.power_label.setText(f"{data.crank.power:.1f} W") #W
            self.ui.cadence_label.setText(f"{data.crank.cadence:.1f} RPM") #RPM
            self.ui.speed_label.setText(f"{data.crank.speed:.1f} km/h") #km/h
            self.ui.distance_label.setText(f"{data.crank.distance:.1f} m") #m
            self.ui.calories_label.setText(f"{data.crank.calories:.1f} Kcal") #Kcal
            logging.info(f"[MainWindow] Crank Data - Power: {data.crank.power}, Cadence: {data.crank.cadence}, Speed: {data.crank.speed}, Distance: {data.crank.distance}, Calories: {data.crank.calories}")

        elif self.is_riding and not isinstance(data.crank, CrankData):
            logging.warning("[MainWindow] Riding state is True but no crank data available.")
            self.clear_crank_data_labels()

        #Ver o que mandei pro joao
        if not isinstance(data.gps, GpsData):
            logging.warning("[MainWindow] No GPS data available in TelemetryMsg to update UI.")
            return

        #gps
        #Update gps data: satellities and quality labels
        self.ui.satellities_label.setText(str(data.gps.fix_satellites))
        self.ui.fix_quality_label.setText(str(data.gps.fix_quality))

        #update map
        self.map_widget.update_map_plotting(data.gps.latitude, data.gps.longitude, data.gps.altitude)
        #Update GPS icon and write RTC at first fix
        try:
            if self.its_first_fix:
                print(data)
                self.update_rtc_by_gps.emit(data.info.date)
                self.its_first_fix = False
        except:
            logging.info("[mainwindow] couldn't emit data for clock update")

        if data.gps.fix_quality > 0 and not self.has_fix_position:
            
            pixmap = QPixmap("icons/gps_on.svg")
            self.ui.gps_icon_label.setPixmap(pixmap)
            self.has_fix_position = True
            

        elif data.gps.fix_quality == 0 and self.has_fix_position:
            pixmap = QPixmap("icons/gps_off.svg")
            self.ui.gps_icon_label.setPixmap(pixmap)
            self.has_fix_position = False
    
    @Slot(datetime)
    def update_clock_from_gps(self, real_time):
        real_time = datetime.strptime(real_time, "%Y-%m-%d %H:%M:%S")
        updater = GPSClock()
        updater.update_time(real_time)

    @Slot(str)
    def update_datetime_labels(self, time):
        date, time = time.split()

        month, day = date.split('.')

        pixmap = QPixmap("date_label")
        self.ui.date_label.setText(f"{day} {month.capitalize()}")
        self.ui.time_label.setText(time)

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
            pixmap = QPixmap("icons/app_bt_on.svg")
            self.ui.app_bt_label.setPixmap(pixmap)
        else:
            pixmap = QPixmap("icons/app_bt_off.svg")
            self.ui.app_bt_label.setPixmap(pixmap)

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
        self.ui.power_label.setText("--") #W
        self.ui.cadence_label.setText("--") #RPM
        self.ui.speed_label.setText("--") #km/h
        self.ui.distance_label.setText("--") #m
        self.ui.calories_label.setText("--") #Kcal

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qdarktheme.setup_theme("dark")
    # 1. Set the signal handler for SIGINT (Ctrl+C)
    # This allows Ctrl+C to be processed by the Python interpreter
    # while the Qt event loop is running.
    signal.signal(signal.SIGINT, signal.SIG_DFL) # <<< Add this line

    widget = MainWindow(app)
    widget.showFullScreen()

    logging.info("[MainWindow] Running HMI")
    # 2. The try/except block is no longer necessary here
    # as the signal handler will handle the Ctrl+C directly.
    # The application will terminate correctly when SIGINT is received.
    sys.exit(app.exec())

#36px x 2.5px small icons
#88px x 3px arrows
#Cinza #8a9190
#Verde água mais escuro: #268071
#Verde água mais aberto:
