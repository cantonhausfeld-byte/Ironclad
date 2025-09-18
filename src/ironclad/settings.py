from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


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

    @property
    def ODDSAPI__KEY(self) -> str | None:
        return self.oddsapi_key

    @property
    def SPORTSGAMEODDS__KEY(self) -> str | None:
        return self.sgo_key

    @property
    def WEATHER__KEY(self) -> str | None:
        return self.weather_key


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
