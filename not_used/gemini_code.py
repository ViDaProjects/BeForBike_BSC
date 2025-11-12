import sys
import serial
import pynmea2
import time
from queue import Queue
import os

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread, Signal, Slot, QUrl, QTimer, QObject, QThread
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import QQmlApplicationEngine

# --- Define Queues ---
# Queue for raw NMEA data from the GPS module
process_gps_data_queue = Queue()
# Queue for processed data to be displayed in the UI
show_data_queue = Queue()

class GpsGatherThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.port = "/dev/serial0"
        self.baudrate = 9600
        self.is_running = True

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            print("GpsGatherThread: Waiting for GPS data...")
            while self.is_running:
                newdata = ser.readline().decode('ascii', errors='replace')
                if newdata:
                    process_gps_data_queue.put(newdata)
        except serial.SerialException as e:
            print(f"GpsGatherThread: Error opening serial port: {e}")

    def stop(self):
        self.is_running = False
        self.wait()

class GpsProcessorThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True

    def run(self):
        print("GpsProcessorThread: Processing NMEA data...")
        while self.is_running:
            if not process_gps_data_queue.empty():
                raw_data = process_gps_data_queue.get()
                if raw_data.startswith('$GNGGA'):
                    try:
                        msg = pynmea2.parse(raw_data)
                        if msg.gps_qual > 0:
                            processed_data = {
                                "latitude": msg.latitude,
                                "longitude": msg.longitude,
                                "quality": msg.gps_qual,
                                "altitude": msg.altitude
                            }
                            show_data_queue.put(processed_data)
                            print("GpsProcessorThread: Valid data sent to UI queue.")
                    except pynmea2.ParseError as e:
                        print(f"GpsProcessorThread: NMEA parsing error: {e}")
            else:
                time.sleep(0.1)

    def stop(self):
        self.is_running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Tracker Raspberry Pi")
        self.setGeometry(100, 100, 1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # UI labels
        self.lat_label = QLabel("Latitude: ---")
        self.lon_label = QLabel("Longitude: ---")
        self.alt_label = QLabel("Altitude: ---")
        self.qual_label = QLabel("Signal Quality: ---")

        main_layout.addWidget(self.lat_label)
        main_layout.addWidget(self.lon_label)
        main_layout.addWidget(self.alt_label)
        main_layout.addWidget(self.qual_label)

        # QQuickWidget to display the QML map
        self.quick_widget = QQuickWidget()
        self.quick_widget.setSource(QUrl.fromLocalFile(f"{os.path.abspath(os.path.dirname(__file__))}/map.qml"))
        self.quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        main_layout.addWidget(self.quick_widget)

        # Start the GPS threads
        self.gps_gather_thread = GpsGatherThread()
        self.gps_processor_thread = GpsProcessorThread()

        self.gps_gather_thread.start()
        self.gps_processor_thread.start()

        # Timer to update UI from the queue
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui_from_queue)
        self.timer.start(500) # Check for new data every 500ms

    @Slot()
    def update_ui_from_queue(self):
        if not show_data_queue.empty():
            data = show_data_queue.get()
            lat = data["latitude"]
            lon = data["longitude"]
            quality = data["quality"]
            altitude = data["altitude"]

            self.lat_label.setText(f"Latitude: {lat:.6f}")
            self.lon_label.setText(f"Longitude: {lon:.6f}")
            self.alt_label.setText(f"Altitude: {altitude:.2f}m")

            qualities = {0: "No Fix", 1: "GPS Fix", 2: "DGPS Fix", 3: "PPS Fix", 4: "RTK Fix", 5: "RTK Float"}
            quality_text = qualities.get(quality, "Unknown Quality")
            self.qual_label.setText(f"Signal Quality: {quality_text} ({quality})")

            # Call the QML function to update the map
            root_object = self.quick_widget.rootObject()
            if root_object:
                root_object.updateGpsPosition(lat, lon)

    def closeEvent(self, event):
        self.gps_gather_thread.stop()
        self.gps_processor_thread.stop()
        self.timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
