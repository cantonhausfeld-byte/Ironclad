from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ServiceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ServiceStatus:
    service: str
    state: ServiceState
    message: str = ""


class RecoverableServiceError(RuntimeError):
    """Errors that may succeed on retry."""


class HardServiceError(RuntimeError):
    """Errors that should stop downstream processing."""
