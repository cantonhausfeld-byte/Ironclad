
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    profile: Literal["local", "qa", "prod"] = Field(default="local", alias="IRONCLAD_PROFILE")
    duckdb_path: str = Field(default="out/ironclad.duckdb", alias="DUCKDB__PATH")
    demo: int = Field(default=1, alias="IRONCLAD_DEMO")
    oddsapi_key: str | None = Field(default=None, alias="ODDSAPI__KEY")
    sgo_key: str | None = Field(default=None, alias="SPORTSGAMEODDS__KEY")
    weather_key: str | None = Field(default=None, alias="WEATHER__KEY")
    tz: str = Field(default="UTC", alias="TZ")
    season: int = Field(default=2025, alias="SEASON")
    week: int | None = Field(default=None, alias="WEEK")

    def demo_enabled(self) -> bool:
        return bool(int(self.demo or 0))

    @property
    def TZ(self) -> str:  # pragma: no cover - passthrough convenience
        return self.tz

    @property
    def SEASON(self) -> int:  # pragma: no cover - passthrough convenience
        return int(self.season)

    @property
    def WEEK(self) -> int | None:  # pragma: no cover - passthrough convenience
        return None if self.week in (None, "") else int(self.week)

    @property
    def DUCKDB__PATH(self) -> str:  # pragma: no cover - passthrough convenience
        return self.duckdb_path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
