from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Union, Dict

class GpsSentenceType(Enum):
    GGA = auto()
    RMC = auto()

@dataclass
class GpsSentences:
    type: GpsSentenceType
    data: str