from typing import Any

from pydantic import BaseModel


class RunManifest(BaseModel):
    run_id: str
    season: int
    week: int
    profile: str
    settings_json: dict[str, Any]
