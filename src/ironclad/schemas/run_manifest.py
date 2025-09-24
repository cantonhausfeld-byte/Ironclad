
from pydantic import BaseModel
from typing import Any
class RunManifest(BaseModel):
    run_id: str
    season: int
    week: int
    profile: str
    settings_json: dict[str, Any]
