from .base import ServiceState, ServiceStatus


def get_latest_injuries(*, api_key: str | None) -> ServiceStatus:
    if not api_key:
        return ServiceStatus("injuries", ServiceState.UNAVAILABLE, "Missing RAPIDAPI__KEY")
    return ServiceStatus("injuries", ServiceState.DEGRADED, "Stub")
