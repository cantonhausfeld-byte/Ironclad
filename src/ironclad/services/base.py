from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ServiceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(slots=True)
class ServiceStatus:
    name: str
    state: ServiceState
    message: str = "OK"


class RecoverableServiceError(RuntimeError):
    ...


class HardServiceError(RuntimeError):
    ...
