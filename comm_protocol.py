from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from typing import Union, Dict
from datetime import datetime

# ============================================================
#  ENUMS - Message types and identifiers
# ============================================================

class FileMngMsgId(Enum):
    """ Identifiers for messages handled by the FileManagerThread. """
    CREATE_FILE = auto()
    DELETE_FILE = auto()
    SEARCH_FILES = auto()
    GET_RIDE_ID = auto()

class TelemetryOrigin(Enum):
    """ Indicates the origin of telemetry data. """
    GPS = auto()
    CRANK = auto()

class GpsSentenceType(Enum):
    GGA = auto()
    RMC = auto()

# ============================================================
#  BASIC DATA STRUCTURES
# ============================================================

@dataclass
class CrankReading:
    w: float
    a: float

@dataclass
class PowerData:
    power: float
    cadence: float # IN RPM, DON'T FORGET, IN RPM

@dataclass
class GpsSentences:
    type: GpsSentenceType
    data: str

@dataclass
class GpsData:
    """ Represents GPS-related measurements. """
    timestamp: str
    real_time: datetime
    latitude: float
    longitude: float
    altitude: float
    speed: float
    direction: float
    fix_satellites: int
    fix_quality: int

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict):
        return GpsData(**data)

@dataclass
class CrankData:
    """ Represents crank sensor data. """
    power: float
    cadence: float
    joules: float
    calories: float
    speed_ms: float
    speed: float
    distance: float

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict):
        return CrankData(**data)

@dataclass
class PacketInfo:
    ride_id: int
    date: str
    time: str

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict):
        return CrankData(**data)

# ============================================================
#  INTER-THREAD MESSAGE STRUCTURES
# ============================================================
#ProcessGpsDataQueue and ProcessCrankDataQueue receive raw data from GPS and crank, respectively
#RideThread sends telemetry_log: List[json string of TelemetryMsg] to SendRideDataQueue and FileManagerQueue

## Threads: MsgCreator, CrankProcessor and GpsProcessor
@dataclass
class ProcessedDataMsg:
    """ Processed data from sensors or GPS
    Goes to: CreateMsgQueue
    Sender: GpsProcessorThread and CrankProcessorThread
    Receiver: MsgCreatorThread
    """
    data_origin: TelemetryOrigin
    data: Union[GpsData, CrankData]
    info: PacketInfo = None

## Threads: MsgCreator and RideThread
@dataclass
class TelemetryMsg:
    """ Message containing a snapshot of sensor and GPS telemetry data.
    Goes to: AddRideDataQueue
    Sender: MsgCreatorThread
    Receiver: RideThread, MainWindowThread
    """
    info: PacketInfo
    gps: GpsData
    crank: CrankData = None

    #To get json string, do: json.dump(TelemetryMsg.to_dict())
    def to_dict(self):
        return {
            "info": self.info.to_dict(),
            "gps": self.gps.to_dict(),
            "crank": self.crank.to_dict() if self.crank else None
        }

    @staticmethod
    def from_dict(data: Dict):
        return TelemetryMsg(
            info=PacketInfo.from_dict(data.get("info")),
            gps=GpsData.from_dict(data.get("gps")),
            crank=CrankData.from_dict(data.get("crank")) if data.get("crank") else None
        )

## Threads: FileManager, PeripheralBLE and RideThread
@dataclass
class RideDataMsg:
    """Message containing the complete ride log with telemetry data.
    Goes to: SendRideDataQueue
    Sender: RideThread and FileManagerThread
    Receiver: PeripheralBLE
    """
    file_name: str
    telemetry_log: list[str]

@dataclass
class FileManagerMsg:
    """Message to require some functionatity from FileManager
    Goes to: FileManagerQueue
    Sender: RideThread and PeripheralBLE
    Receiver: FileManagerThread
    """
    msg_id: FileMngMsgId
    file_name: str = None
    telemetry_list: list[str] = field(default_factory=list) #list of json String which represents TelemetryData.to_dict()

    #create_file: filename and list[TelemetryMsg]
    #delete_file: filename
    #search_files: None
    #get_ride_id: None
