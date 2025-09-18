from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..settings import settings
from .base import RecoverableServiceError, ServiceState


@dataclass
class OddsLine:
    game_id: str
    book: str
    market: str
    side: str
    line: float | None
    price_american: int
    ts: str


class OddsClient:
    def __init__(self) -> None:
        self.state = (
            ServiceState.AVAILABLE
            if (settings.oddsapi_key or settings.sgo_key or settings.demo_enabled())
            else ServiceState.UNAVAILABLE
        )

    def fetch_board(self, season: int, week: int) -> list[OddsLine]:
        if settings.demo_enabled():
            now = datetime.utcnow().isoformat()
            return [
                OddsLine("2025W1-NYG@WAS", "DraftKings", "ML", "WAS", None, -145, now),
                OddsLine("2025W1-NYG@WAS", "DraftKings", "ML", "NYG", None, 125, now),
                OddsLine("2025W1-NYG@WAS", "DraftKings", "ATS", "WAS", -3.0, -110, now),
                OddsLine("2025W1-NYG@WAS", "DraftKings", "OU", "Over", 42.5, -110, now),
                OddsLine("2025W1-NYG@WAS", "DraftKings", "OU", "Under", 42.5, -110, now),
            ]
        if not (settings.oddsapi_key or settings.sgo_key):
            self.state = ServiceState.UNAVAILABLE
            raise RecoverableServiceError("No odds API key configured.")
        raise RecoverableServiceError("Real odds fetching disabled in Phase 1 foundation build.")
