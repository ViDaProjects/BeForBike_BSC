import sys
import serial
import pynmea2
import time
from queue import Queue
import os
import logging

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread, Slot, QUrl, QTimer
from PySide6.QtQuickWidgets import QQuickWidget

from PySide6.QtCore import (
     Signal, Property
)
from PySide6.QtPositioning import QGeoCoordinate

from comm_protocol import GpsData, GpsSentences


class GpsGatherThread(QThread):
    def __init__(self, process_gps_data_queue: Queue):
        super().__init__()
        self.port = "/dev/serial0"
        self.baudrate = 9600
        self.is_running = True
        self.process_gps_queue = process_gps_data_queue

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            logging.info("[GPS Gather] Waiting for GPS data...")
            while self.is_running:
                newdata = ser.readline().decode('ascii', errors='replace')
                if newdata:
                    if newdata.startswith("$GPGGA"):
                        sentence = GpsSentences(gga=newdata)
                        self.process_gps_queue.put(sentence)
                    elif newdata.startswith("$GPRMC"):
                        sentence = GpsSentences(rmc=newdata)
                        self.process_gps_queue.put(sentence)
        except serial.SerialException as e:
            logging.error("[GPS Gather] Error opening serial port: %s", e)
        except Exception as e:
            logging.error("[GPS Gather] Unexpected error: %s", e)

    def stop(self):
        self.is_running = False
        self.wait()

class GpsProcessorThread(QThread):
    def __init__(self, process_gps_data_queue: Queue, show_data_queue: Queue):
        super().__init__()
        self.is_running = True
        self.process_gps_queue = process_gps_data_queue
        self.gps_data_msg = GpsData()
        self.show_data_queue = show_data_queue
        # NEW: Caches for assembling data from multiple sentences
        #Only GPS integrated for now (not updating timestamp) ----------------
        #self._cached_gga = {}
        #self._cached_rmc = {}


    def run(self):
        logging.info("[GPS Processor] Processing NMEA data...")
        while self.is_running:
            #if not self.process_gps_queue.empty():
            sentences = self.process_gps_queue.get()
            #Continuar a partir daqui
            if sentences.gga:
                try:
                    msg = pynmea2.parse(sentences.gga)
                    logging.info(repr(msg))
                    if msg.gps_qual > 0:
                        self.gps_data_msg.latitude = msg.latitude,
                        self.gps_data_msg.longitude= msg.longitude,
                        self.gps_data_msg.altitude= msg.altitude,
                        #self.gps_data_msg.fix_satellites ----- pegar satelitesss----
                        self.gps_data_msg.fix_quality = msg.gps_qual

                        #Tirar daqui depoissss (Vira msg creator) ------------------
                        self.show_data_queue.put(self.gps_data_msg)
                        print("GpsProcessorThread: Valid data sent to UI queue.")
                except pynmea2.ParseError as e:
                    print(f"GpsProcessorThread: NMEA parsing error: {e}")

    def stop(self):
            self.is_running = False
            self.wait()



class MapWidget(QQuickWidget):
    """
    A generic QQuickWidget to display a map, a current position,
    and a plotted path.

    Now also parses GGA and RMC sentences to build a GpsData object.
    """

    # --- Signals ---
    currentPositionChanged = Signal()
    pathModelChanged = Signal()

    # NEW: Signal to emit the complete GpsData object
    newGpsDataAvailable = Signal(object) # Emits a GpsData object

    def __init__(self, show_data_queue: Queue, parent=None):
        super().__init__(parent)

        self.show_data_queue: Queue = show_data_queue

        # --- Internal state ---
        self._is_plotting = False
        self._current_position = QGeoCoordinate(0, 0)
        self._path_list = []

        # NEW: Caches for assembling data from multiple sentences
        self._cached_gga = {}
        self._cached_rmc = {}

        # Expose this Python object to QML
        self.rootContext().setContextProperty("map_backend", self)

        # Load the QML file
        qml_file = os.path.join(os.path.dirname(__file__), "map.qml")
        self.setSource(QUrl.fromLocalFile(qml_file))

        self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

    # --- QML-accessible Properties ---

    @Property(QGeoCoordinate, notify=currentPositionChanged)
    def currentPosition(self):
        return self._current_position

    @Property("QVariantList", notify=pathModelChanged)
    def pathModel(self):
        return self._path_list

    @Slot()
    def start_plotting(self):
        print("Starting path plotting...")
        self._is_plotting = True
        self._path_list = []
        if self._current_position.isValid():
            self._path_list.append(self._current_position)
        self.pathModelChanged.emit()

    @Slot()
    def stop_plotting(self):
        print("Stopping path plotting.")
        self._is_plotting = False
