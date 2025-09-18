
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid")
    profile: Literal["local","qa","prod"] = Field(default="local", alias="IRONCLAD_PROFILE")
    duckdb_path: str = Field(default="./data/ironclad.duckdb", alias="DUCKDB_PATH")
    demo: int = Field(default=1, alias="IRONCLAD_DEMO")
    oddsapi_key: str | None = Field(default=None, alias="ODDSAPI__KEY")
    sgo_key: str | None = Field(default=None, alias="SPORTSGAMEODDS__KEY")
    weather_key: str | None = Field(default=None, alias="WEATHER__KEY")
    def demo_enabled(self) -> bool:
        return bool(int(self.demo or 0))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
