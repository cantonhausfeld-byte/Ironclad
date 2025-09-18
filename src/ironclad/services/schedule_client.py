from __future__ import annotations
from typing import List, Tuple
from dataclasses import dataclass
from pydantic import BaseModel
from .http import HTTPClient, HttpConfig
from .base import ServiceStatus, ServiceState


class Game(BaseModel):
    game_id: str
    season: int
    week: int
    home: str
    away: str
    kickoff_utc_iso: str
    venue: str | None = None


@dataclass
class ScheduleClientConfig:
    # Odds API endpoint includes commence_time; we ask for minimal market to get game objects.
    base_url: str = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    api_key: str | None = None
    region: str = "us"
    markets: str = "h2h"
    odds_format: str = "american"
    cache_ttl_s: int = 300


class ScheduleClient:
    def __init__(self, cfg: ScheduleClientConfig, http: HTTPClient | None = None):
        self.cfg = cfg
        self.http = http or HTTPClient(HttpConfig(default_ttl_s=cfg.cache_ttl_s))

    def harvest(self, *, season: int, week: int) -> Tuple[List[Game], ServiceStatus]:
        if not self.cfg.api_key:
            return ([], ServiceStatus("schedule", ServiceState.UNAVAILABLE, "Missing ODDSAPI__KEY"))
        params = {
            "apiKey": self.cfg.api_key,
            "regions": self.cfg.region,
            "markets": self.cfg.markets,
            "oddsFormat": self.cfg.odds_format,
        }
        try:
            payload = self.http.get_json(self.cfg.base_url, params=params, headers=None)
            games = self._parse(payload, season=season, week=week)
            state = ServiceState.AVAILABLE if games else ServiceState.DEGRADED
            msg = "OK" if games else "No games parsed from Odds API."
            return (games, ServiceStatus("schedule", state, msg))
        except Exception as e:
            return ([], ServiceStatus("schedule", ServiceState.UNAVAILABLE, f"Error: {e}"))

    def _parse(self, payload, *, season: int, week: int) -> List[Game]:
        out: List[Game] = []
        if not isinstance(payload, list):
            return out
        for g in payload:
            gid = g.get("id") or ""
            home = g.get("home_team") or ""
            away = g.get("away_team") or ""
            kt = g.get("commence_time")  # ISO Z
            if not (gid and home and away and kt):
                continue
            out.append(
                Game(
                    game_id=gid,
                    season=season,
                    week=week,
                    home=home,
                    away=away,
                    kickoff_utc_iso=kt,
                    venue=None,
                )
            )
        return out


def harvest_schedule_from_oddsapi(
    *, api_key: str | None, season: int, week: int
) -> Tuple[List[Game], ServiceStatus]:
    client = ScheduleClient(ScheduleClientConfig(api_key=api_key))
    return client.harvest(season=season, week=week)
