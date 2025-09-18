from pydantic import BaseModel


class OddsSnapshot(BaseModel):
    run_id: str
    game_id: str
    book: str
    market: str
    side: str
    line: float | None = None
    price_american: int
    ts: str
