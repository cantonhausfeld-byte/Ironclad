
from pydantic import BaseModel
class Game(BaseModel):
    game_id: str
    season: int
    week: int
    away: str
    home: str
    kickoff_et: str = ""
