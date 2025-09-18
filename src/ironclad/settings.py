from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    profile: Literal["local", "qa", "prod"] = Field(
        default="local", alias="IRONCLAD_PROFILE"
    )
    DUCKDB__PATH: str = Field(default="out/ironclad.duckdb", alias="DUCKDB__PATH")
    demo: int = Field(default=1, alias="IRONCLAD_DEMO")
    oddsapi_key: str | None = Field(default=None, alias="ODDSAPI__KEY")
    sgo_key: str | None = Field(default=None, alias="SPORTSGAMEODDS__KEY")
    weather_key: str | None = Field(default=None, alias="WEATHER__KEY")

    @property
    def duckdb_path(self) -> str:
        return self.DUCKDB__PATH

    def demo_enabled(self) -> bool:
        return bool(int(self.demo or 0))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
