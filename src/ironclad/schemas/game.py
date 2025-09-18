from pydantic import BaseModel, conint


class Game(BaseModel):
    game_id: str
    season: conint(ge=2000)
    week: conint(ge=1, le=23)
    home: str
    away: str
    kickoff_utc_iso: str
    venue: str | None = None
