import sys
import serial
import pynmea2
import time
from queue import Queue
import os
import logging

from datetime import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread, Slot, QUrl, QTimer
from PySide6.QtQuickWidgets import QQuickWidget

from PySide6.QtCore import (
     Signal, Property
)
from PySide6.QtPositioning import QGeoCoordinate

from comm_protocol import GpsData, GpsSentences, GpsSentenceType, TelemetryMsg, ProcessedDataMsg, TelemetryOrigin, PacketInfo



class GpsGatherThread(QThread):
    def __init__(self, process_gps_data_queue: Queue):
        super().__init__()
        self.port = "/dev/serial0"
        self.baudrate = 9600
        self.is_running = False
        self.process_gps_queue = process_gps_data_queue

    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("GpsGatherThread is already running")
            return

        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("GpsGatherThread is running. Trying to open serial port")

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=10)
            logging.info("[GPS Gather] Waiting for GPS data... %s", ser)
            while self.is_running:
                newdata = ser.readline().decode('ascii', errors='replace')
                type = None
                if newdata:
                    if newdata.startswith("$GNGGA"):
                        type = GpsSentenceType.GGA
                    elif newdata.startswith("$GNRMC"):
                        type = GpsSentenceType.RMC
                    else:
                        # Log what was received that wasn't a recognized sentence
                        #logging.debug("[GPS Gather] Unrecognized sentence: %s", newdata)
                        continue

                    sentence = GpsSentences(type=type, data=newdata)
                    logging.debug("[GPS Gather] Got sentence: %s", sentence)
                    self.process_gps_queue.put(sentence)
                else:
                    logging.warning("[GPS Gather] Read line was empty (newdata)")
        except serial.SerialException as e:
            logging.error("[GPS Gather] Error opening serial port: %s", e)
        except Exception as e:
            logging.error("[GPS Gather] Unexpected error: %s", e)

    def stop(self):
        self.is_running = False
        self.wait()

class GpsProcessorThread(QThread):
    #Change here --- Emit this signal by msgCreator ------------
    update_ui = Signal(TelemetryMsg)

    def __init__(self, process_gps_data_queue: Queue, create_msg_queue: Queue):

        super().__init__()
        self.is_running = False
        self.process_gps_queue = process_gps_data_queue
        self.create_msg_queue = create_msg_queue
        # NEW: Caches for assembling data from multiple sentences
        #Only GPS integrated for now (not updating timestamp) ----------------
        self._cached_gga = {}
        self._cached_rmc = {}

    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("GpsProcessorThread is already running")
            return

        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("GpsProcessorThread is running")

    def run(self):
        logging.info("[GPS Processor] Processing NMEA data...")

        while self.is_running:
            #if not self.process_gps_queue.empty():
            sentence = self.process_gps_queue.get()
            if not isinstance(sentence, GpsSentences):
                logging.error("[GPS Processor] Data from process gps queue is not GpsSentence")
                continue

            try:
                msg = pynmea2.parse(sentence.data)
            except pynmea2.ParseError as e:
                logging.error(f"[GPS Processor] NMEA parsing error: {e}")
                continue

            #logging.info("[GPS Processor] %s", repr(msg))
            if sentence.type == GpsSentenceType.GGA:
                self._cached_gga = msg
                self.check_for_complete_data()
            elif sentence.type == GpsSentenceType.RMC:
                self._cached_rmc = msg
                self.check_for_complete_data()
            else:
                logging.warning("[GPS Processor] Received unexpected sentence")

    def stop(self):
            self.is_running = False
            self.wait()

    def check_for_complete_data(self):
        if self._cached_gga and self._cached_rmc:
            if self._cached_gga.timestamp == self._cached_rmc.timestamp:

                # Check if altitude is None (or a non-numeric type) and set a default
                if self._cached_gga.altitude is None:
                    safe_altitude = 0.0
                else:
                    # Ensure it is a float if it exists
                    safe_altitude = float(self._cached_gga.altitude)

                if self._cached_gga.timestamp:
                    cached_gga = self._cached_gga.timestamp.strftime("%H:%M:%S")
                else: 
                    cached_gga = ""

                gps_data_msg = GpsData(
                    timestamp = cached_gga, # To undo string: datetime.strptime(timestamp, "%H:%M:%S")
                    latitude = self._cached_gga.latitude,
                    longitude = self._cached_gga.longitude,
                    altitude= safe_altitude,
                    fix_satellites = self._cached_gga.num_sats,
                    fix_quality = self._cached_gga.gps_qual,
                    speed = 0, #self._cached_rmc.spd_over_grnd,      # Speed in knots
                    direction = 0) #self._cached_rmc.true_course     # Direction in degrees

                # DEBUG CRÍTICO: Imprima a coordenada de saída ANTES de enviar para a UI
                logging.info(f"[GPS Processor] Valid DD Coords: {gps_data_msg.latitude}, {gps_data_msg.longitude}")

                #Change this to send ProcessedDataMsg to CreateMsgQueue -------------------------
                """show_data = TelemetryMsg(
                    info = None,
                    gps = gps_data_msg,
                    crank = None)
                processedData = ProcessedDataMsg(data_origin=TelemetryOrigin.GPS, data=gps_data_msg)
                self.create_msg_queue.put(processedData)
                
                self.update_ui.emit(show_data)
                """
                print(self._cached_rmc)
                if self._cached_rmc.datestamp and self._cached_rmc.timestamp:
                    real_time = datetime.combine(
                        self._cached_rmc.datestamp,
                        self._cached_rmc.timestamp  # or _cached_gga.timestamp
                    ).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    real_time = ""

                send_data = ProcessedDataMsg(
                    data_origin = TelemetryOrigin.GPS,
                    data = gps_data_msg,
                    info = PacketInfo(ride_id=None, date=real_time, time=real_time,)
                )
                self.create_msg_queue.put(send_data)
                
class TestGpsThread(QThread):
    def __init__(self, show_data_queue: Queue):
        super().__init__()
        self.is_running = False
        self.show_data_queue = show_data_queue

    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("GpsTesterThread is already running")
            return

        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("GpsTesterThread is running")


    def run(self):
        logging.info("[GPS Tester] Receiving GpsDataMsg...")
        while self.is_running:
            #if not self.process_gps_queue.empty():
            gps_data = self.show_data_queue.get()

            if isinstance(gps_data, GpsData):
                logging.info("[GPS Tester] %s", gps_data.to_dict())
            else:
                logging.error("[GPS Tester] Wrong data received: %s", type(gps_data))

    def stop(self):
            self.is_running = False
            self.wait()


#O mainwindow lê o show_data_queue e passa pro map widget as coordenadas
#MapWidget cria QGeoCoordinate, emite currentPosition e pathmodel changed
class MapWidget(QQuickWidget):
    """
    A generic QQuickWidget to display a map, a current position,
    and a plotted path.

    Now also parses GGA and RMC sentences to build a GpsData object.
    """

    # --- Signals ---
    currentPositionChanged = Signal()
    pathModelChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Internal state ---
        self._is_plotting = False
        self._current_position = QGeoCoordinate(0, 0)
        self._path_list = []

        # Expose this Python object to QML
        self.rootContext().setContextProperty("map_backend", self)

        # Load the QML file
        qml_file = os.path.join(os.path.dirname(__file__), "map.qml")
        self.setSource(QUrl.fromLocalFile(qml_file))

        self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

    def update_map_plotting(self, latitude, longitude, altitude):

        new_coord = QGeoCoordinate(
            latitude,
            longitude,
            altitude
        )

        if self._current_position != new_coord:
            self._current_position = new_coord
            logging.info("[Map Widget] Current position on map changed to: %s, %s, %s", latitude, longitude, altitude)
            self.currentPositionChanged.emit()

            if self._is_plotting:
                self._path_list.append(new_coord)
                self.pathModelChanged.emit()

    # --- QML-accessible Properties ---
    @Property(QGeoCoordinate, notify=currentPositionChanged)
    def currentPosition(self):
        return self._current_position

    @Property("QVariantList", notify=pathModelChanged)
    def pathModel(self):
        # AQUI ESTÁ A CORREÇÃO: retorna uma *cópia* da lista.
        # Isso garante que o QML leia uma nova 'QVariantList' a cada atualização,
        # resolvendo problemas de binding em alguns ambientes Qt.
        return list(self._path_list)

    @Slot()
    def change_plotting_state(self, riding_state: bool):
        if riding_state and not self._is_plotting:
            self.start_plotting()
        elif not riding_state and self._is_plotting:
            self.stop_plotting()
        else:
            logging.warning("[Map Widget] Received plotting state is the same as current state; no action taken.")
    
    def start_plotting(self):
        logging.info("[Map Widget] Starting path plotting...")
        self._is_plotting = True
        self._path_list = []
        if self._current_position.isValid():
            self._path_list.append(self._current_position)
        self.pathModelChanged.emit()

    def stop_plotting(self):
        logging.info("[Map Widget] Stopping path plotting.")
        self._is_plotting = False
