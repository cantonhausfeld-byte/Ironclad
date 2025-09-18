from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        extra="forbid",
        env_file=".env",
        env_nested_delimiter="__",
    )

    TZ: str = "America/New_York"
    SEASON: int = 2025
    WEEK: int | None = None

    ODDSAPI__KEY: str | None = None
    SPORTSGAMEODDS__KEY: str | None = None
    RAPIDAPI__KEY: str | None = None
    WEATHER__KEY: str | None = None

    DUCKDB__PATH: str = "out/ironclad.duckdb"


def get_settings() -> "Settings":
    return Settings()  # type: ignore
