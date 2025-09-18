from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    profile: Literal["local", "qa", "prod"] = Field(default="local", alias="IRONCLAD_PROFILE")
    duckdb_path: str = Field(default="./data/ironclad.duckdb", alias="DUCKDB_PATH")
    demo: int = Field(default=1, alias="IRONCLAD_DEMO")
    oddsapi_key: str | None = Field(default=None, alias="ODDSAPI__KEY")
    sgo_key: str | None = Field(default=None, alias="SPORTSGAMEODDS__KEY")
    weather_key: str | None = Field(default=None, alias="WEATHER__KEY")

    # --- Exposure guardrail caps ---
    CAPS__MAX_TOTAL_U: float = Field(25.0, description="Total units cap across all picks")
    CAPS__MAX_TEAM_U: float = Field(10.0, description="Per-team exposure cap (units)")
    CAPS__MAX_MARKET_U: float = Field(15.0, description="Per-market exposure cap (units)")
    CAPS__MAX_GAME_U: float = Field(10.0, description="Per-game exposure cap (units)")
    CAPS__REQUIRE_MIN_PICKS: int = Field(1, description="Minimum picks required")

    # --- Sizing defaults ---
    SIZING__BANKROLL_UNITS: float = Field(100.0, description="Bankroll size in units for sizing")
    SIZING__KELLY_SCALE: float = Field(0.25, description="Fractional Kelly multiplier (0..1)")
    SIZING__MAX_PER_BET_U: float = Field(3.0, description="Cap per bet (units)")
    SIZING__MAX_PER_GAME_U: float = Field(10.0, description="Cap per game (units)")
    SIZING__MAX_TOTAL_U: float = Field(25.0, description="Global cap across board (units)")

    def demo_enabled(self) -> bool:
        return bool(int(self.demo or 0))

    @property
    def DUCKDB__PATH(self) -> str:
        return self.duckdb_path


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    return _cached_settings()


settings = get_settings()
