import sys
import os
from PySide6.QtCore import (
    QUrl, QTimer, Signal, Slot, Property
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton
)
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtPositioning import QGeoCoordinate
from comm_protocol import GpsData

# -----------------------------------------------------------------
#  The Generic MapWidget Class (Updated)
# -----------------------------------------------------------------

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

    def __init__(self, parent=None):
        super().__init__(parent)

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

    # --- Public Slots (Your API) ---

    @Slot(str)
    def process_nmea_sentence(self, sentence: str):
        """
        Public slot to receive NMEA sentences.
        It routes GGA and RMC sentences to their parsers.
        """
        if sentence.startswith("$GPGGA"):
            gga_data = self._parse_gga(sentence)
            if gga_data:
                # Store data
                self._cached_gga = gga_data

                # --- IMPORTANT: Update map immediately (original functionality) ---
                new_coord = QGeoCoordinate(
                    gga_data['latitude'],
                    gga_data['longitude'],
                    gga_data['altitude']
                )

                if self._current_position != new_coord:
                    self._current_position = new_coord
                    self.currentPositionChanged.emit()

                    if self._is_plotting:
                        self._path_list.append(new_coord)
                        self.pathModelChanged.emit()

                # Check if we can build a full GpsData object
                self._check_for_complete_data()

        elif sentence.startswith("$GPRMC"):
            rmc_data = self._parse_rmc(sentence)
            if rmc_data:
                # Store data
                self._cached_rmc = rmc_data
                # Check if we can build a full GpsData object
                self._check_for_complete_data()

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

    # --- Internal Helpers ---

    def _check_for_complete_data(self):
        """
        Checks if we have cached GGA and RMC data with matching timestamps.
        If so, creates a GpsData object and emits it.
        """
        if self._cached_gga and self._cached_rmc:
            # Check if timestamps match
            if self._cached_gga['timestamp'] == self._cached_rmc['timestamp']:
                try:
                    # Combine data and create the object
                    data = GpsData(
                        timestamp=self._cached_gga['timestamp'],
                        latitude=self._cached_gga['latitude'],
                        longitude=self._cached_gga['longitude'],
                        altitude=self._cached_gga['altitude'],
                        fix_satellites=self._cached_gga['fix_satellites'],
                        fix_quality=self._cached_gga['fix_quality'],
                        speed=self._cached_rmc['speed'],
                        direction=self._cached_rmc['direction']
                    )

                    # Emit the complete data object
                    self.newGpsDataAvailable.emit(data)

                except Exception as e:
                    print(f"Error creating GpsData object: {e}")

                # Clear caches for the next batch
                self._cached_gga = {}
                self._cached_rmc = {}

    def _convert_nmea_latlon_to_decimal(self, value: str, direction: str):
        """Converts NMEA latitude/longitude (ddmm.mmmm) to decimal degrees."""
        if not value:
            return 0.0

        raw_val = float(value)
        degrees = int(raw_val / 100)
        minutes = (raw_val % 100) / 60.0
        decimal = degrees + minutes

        if direction in ['S', 'W']:
            decimal = -decimal

        return decimal

    def _parse_gga(self, sentence: str) -> dict | None:
        """
        Parses a $GPGGA sentence.
        Returns a dictionary or None on failure.
        """
        try:
            parts = sentence.split(',')

            # Check for basic validity and fix quality
            fix_quality = int(parts[6])
            if len(parts) < 11 or parts[0] != '$GPGGA' or fix_quality == 0:
                return None # No fix

            # Timestamp (hhmmss.ss)
            timestamp = parts[1]

            # Latitude (ddmm.mmmm, N/S)
            latitude = self._convert_nmea_latlon_to_decimal(parts[2], parts[3])

            # Longitude (dddmm.mmmm, E/W)
            longitude = self._convert_nmea_latlon_to_decimal(parts[4], parts[5])

            # Altitude (in meters)
            altitude = float(parts[9])

            # Satellites
            fix_satellites = int(parts[7])

            return {
                "timestamp": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "fix_quality": fix_quality,
                "fix_satellites": fix_satellites
            }

        except (ValueError, IndexError) as e:
            print(f"Error parsing GGA sentence: {e}")
            return None

    def _parse_rmc(self, sentence: str) -> dict | None:
        """
        Parses a $GPRMC sentence.
        Returns a dictionary or None on failure.
        """
        try:
            parts = sentence.split(',')

            # Check for basic validity and status (A=Active, V=Void)
            status = parts[2]
            if len(parts) < 10 or parts[0] != '$GPRMC' or status != 'A':
                return None # No active fix

            # Timestamp (hhmmss.ss)
            timestamp = parts[1]

            # Latitude (ddmm.mmmm, N/S)
            latitude = self._convert_nmea_latlon_to_decimal(parts[3], parts[4])

            # Longitude (dddmm.mmmm, E/W)
            longitude = self._convert_nmea_latlon_to_decimal(parts[5], parts[6])

            # Speed over ground (knots)
            speed = float(parts[7])

            # Track angle (degrees True)
            direction = float(parts[8]) if parts[8] else 0.0

            return {
                "timestamp": timestamp,
                "latitude": latitude,  # Included for timestamp matching
                "longitude": longitude, # Included for timestamp matching
                "speed": speed,
                "direction": direction
            }

        except (ValueError, IndexError) as e:
            print(f"Error parsing RMC sentence: {e}")
            return None


# -----------------------------------------------------------------
#  Demonstration / Test Harness
# -----------------------------------------------------------------

# Sample NMEA data simulating a short path
# (Coordinates are for Curitiba, Brazil)
SIM_GGA_SENTENCES = [
    "$GPGGA,120001.00,2525.7040,S,04916.3980,W,1,08,0.9,900.0,M,0.0,M,,*7A",
    "$GPGGA,120003.00,2525.7280,S,04916.3800,W,1,08,0.9,901.0,M,0.0,M,,*7D",
    "$GPGGA,120005.00,2525.7520,S,04916.3620,W,1,08,0.9,902.0,M,0.0,M,,*7E",
    "$GPGGA,120007.00,2525.7760,S,04916.3440,W,1,08,0.9,901.0,M,0.0,M,,*70",
    "$GPGGA,120009.00,2525.8000,S,04916.3260,W,1,08,0.9,900.0,M,0.0,M,,*78"
]

class TestWindow(QWidget):
    """A simple test window to host the MapWidget and simulation buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.map_widget = MapWidget()
        self.start_button = QPushButton("Start Plotting Path")
        self.stop_button = QPushButton("Stop Plotting Path")

        layout = QVBoxLayout(self)
        layout.addWidget(self.map_widget)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        # Connect buttons to the MapWidget's slots
        self.start_button.clicked.connect(self.map_widget.start_plotting)
        self.stop_button.clicked.connect(self.map_widget.stop_plotting)

        # --- Simulation Logic ---
        self._sim_index = 0
        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(2000) # Send new data every 2 seconds
        self.sim_timer.timeout.connect(self.send_sim_data)

        # Send first data point immediately to center the map
        self.send_sim_data()
        # Start the timer
        self.sim_timer.start()

        self.setWindowTitle("GPS Map Test")
        self.resize(800, 600)

    def send_sim_data(self):
        """Simulates receiving a NMEA sentence."""
        if self._sim_index < len(SIM_GGA_SENTENCES):
            sentence = SIM_GGA_SENTENCES[self._sim_index]
            print(f"Simulating RX: {sentence}")
            self.map_widget.process_nmea_sentence(sentence)
            self._sim_index += 1
        else:
            print("End of simulation data.")
            self.sim_timer.stop()


def main():
    # ⚠️ IMPORTANT: Required for OSM (OpenStreetMap) plugin
    # Set a unique user-agent for the map provider
    os.environ["QT_LOCATION_EXTRA_SETTINGS"] = "osm.useragent=MyGpsApp/1.0"

    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
