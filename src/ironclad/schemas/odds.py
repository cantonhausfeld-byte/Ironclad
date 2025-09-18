from pydantic import BaseModel
from typing import Optional


class OddsSnapshot(BaseModel):
    run_id: str
    game_id: str
    book: str
    market: str
    side: str
    line: Optional[float] = None
    price_american: int
    ts: str
