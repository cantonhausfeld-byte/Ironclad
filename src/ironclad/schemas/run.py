from pydantic import BaseModel


class RunManifest(BaseModel):
    run_id: str
    season: int
    week: int
    profile: str = "local"
    seed: int = 42
    settings_json: dict = {}
