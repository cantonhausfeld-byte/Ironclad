
from enum import Enum
class ServiceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
class RecoverableServiceError(RuntimeError): ...
class HardServiceError(RuntimeError): ...
