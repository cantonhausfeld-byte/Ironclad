from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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
    season: int = Field(ge=2000)
    week: int = Field(ge=1, le=23)
    market: Market
    side: str
    line: float | None
    price_american: int
    model_prob: float = Field(ge=0.0, le=1.0)
    fair_price_american: int
    ev_percent: float
    z_score: float
    robust_ev_percent: float
    grade: Grade
    kelly_fraction: float = Field(default=0.0, ge=0, le=1)
    stake_units: float = 0.0
    book: str = "DraftKings"
    ts_created: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
