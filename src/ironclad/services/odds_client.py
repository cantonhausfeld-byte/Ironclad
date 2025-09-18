from pydantic import BaseModel

from .base import ServiceState, ServiceStatus


class OddsQuote(BaseModel):
    game_id: str
    market: str
    line: float | None
    price_american: int
    book: str


def get_latest_quotes(*, api_key: str | None) -> tuple[list[OddsQuote], ServiceStatus]:
    if not api_key:
        return ([], ServiceStatus("odds", ServiceState.UNAVAILABLE, "Missing ODDSAPI__KEY"))
    return ([], ServiceStatus("odds", ServiceState.DEGRADED, "Stub"))
