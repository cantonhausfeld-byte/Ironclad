from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

Season = Annotated[int, Field(ge=2000)]
Week = Annotated[int, Field(ge=1, le=23)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
Kelly = Annotated[float, Field(ge=0.0, le=1.0)]


class Market(str, Enum):
    ML = "ML"
    ATS = "ATS"
    OU = "OU"
    PROP = "PROP"
    ATD = "ATD"


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    NO_PICK = "NO_PICK"


class Pick(BaseModel):
    run_id: str
    game_id: str
    season: Season
    week: Week
    market: Market
    side: str
    line: float | None
    price_american: int
    model_prob: Probability
    fair_price_american: int
    ev_percent: float
    z_score: float
    robust_ev_percent: float
    grade: Grade
    kelly_fraction: Kelly = 0.0
    stake_units: float = 0.0
    book: str = "DraftKings"
    ts_created: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
