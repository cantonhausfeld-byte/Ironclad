from .base import ServiceState, ServiceStatus


def get_latest_weather(*, api_key: str | None) -> ServiceStatus:
    if not api_key:
        return ServiceStatus("weather", ServiceState.UNAVAILABLE, "Missing WEATHER__KEY")
    return ServiceStatus("weather", ServiceState.DEGRADED, "Stub")
