from dataclasses import dataclass
from enum import Enum


class ServiceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ServiceStatus:
    name: str
    state: ServiceState
    message: str = ""
