from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

import duckdb
import pandas as pd


@dataclass
class OddsRow:
    run_id: str
    ts_utc: str
    book: str
    game_id: str
    market: str  # ML/ATS/OU
    line: float | None
    price_american: int
    source: str
    season: int
    week: int


@dataclass
class InjuryRow:
    run_id: str
    ts_utc: str
    player_id: str
    player_name: str
    team: str
    status: str
    prob_active: float | None
    game_id: str
    season: int
    week: int


@dataclass
class WeatherRow:
    run_id: str
    ts_utc: str
    venue_id: str
    game_id: str
    temp_f: float | None
    wind_mph: float | None
    precip_prob: float | None
    season: int
    week: int


class VendorClient:
    def odds_snapshot(self, run_id: str, season: int, week: int):  # pragma: no cover - interface
        raise NotImplementedError

    def injuries_snapshot(self, run_id: str, season: int, week: int):  # pragma: no cover - interface
        raise NotImplementedError

    def weather_snapshot(self, run_id: str, season: int, week: int):  # pragma: no cover - interface
        raise NotImplementedError


class DemoVendor(VendorClient):
    def odds_snapshot(self, run_id: str, season: int, week: int):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[OddsRow] = []
        for i in range(4):
            gid = f"{season}W{week}_G{i+1}"
            for mkt in ["ML", "ATS", "OU"]:
                line = None
                price = random.choice([-110, -105, +100, +120, +140])
                if mkt == "ATS":
                    line = random.choice([-3.5, -2.5, -1.5, +1.5, +2.5, +3.5])
                if mkt == "OU":
                    line = random.choice([41.5, 43.5, 45.5, 47.5])
                rows.append(
                    OddsRow(run_id, now, "DemoBook", gid, mkt, line, price, "demo", season, week)
                )
        return rows

    def injuries_snapshot(self, run_id: str, season: int, week: int):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[InjuryRow] = []
        for team in ["PHI", "DAL", "NYG", "WAS"]:
            rows.append(
                InjuryRow(
                    run_id,
                    now,
                    f"{team}_RB1",
                    "RB One",
                    team,
                    "Questionable",
                    0.6,
                    f"{season}W{week}_G1",
                    season,
                    week,
                )
            )
        return rows

    def weather_snapshot(self, run_id: str, season: int, week: int):
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[WeatherRow] = []
        for i in range(4):
            gid = f"{season}W{week}_G{i+1}"
            rows.append(
                WeatherRow(run_id, now, f"VENUE{i+1}", gid, 70.0 + 2 * i, 8.0 + 2 * i, 0.1 * i, season, week)
            )
        return rows


class OddsAPIClient(VendorClient):
    """Placeholder for a live OddsAPI-backed vendor client."""

    def __init__(self, key: str | None):
        self.key = key
        self._demo = DemoVendor()

    def _has_key(self) -> bool:
        return bool(self.key)

    def odds_snapshot(self, run_id: str, season: int, week: int):
        if not self._has_key():
            return self._demo.odds_snapshot(run_id, season, week)
        raise NotImplementedError("Live odds snapshot fetching is not implemented.")

    def injuries_snapshot(self, run_id: str, season: int, week: int):
        if not self._has_key():
            return self._demo.injuries_snapshot(run_id, season, week)
        raise NotImplementedError("Live injury snapshot fetching is not implemented.")

    def weather_snapshot(self, run_id: str, season: int, week: int):
        if not self._has_key():
            return self._demo.weather_snapshot(run_id, season, week)
        raise NotImplementedError("Live weather snapshot fetching is not implemented.")


class ReplayVendor(VendorClient):
    """
    Serves snapshots previously saved to DuckDB or CSV.
    Priority: DuckDB by run_id → CSV under out/snapshots/<run_id>/.
    """

    def __init__(self, duck_path: str, run_id: str):
        self.duck = duck_path
        self.run_id = run_id

    def _try_duck(self, table: str) -> pd.DataFrame:
        try:
            with duckdb.connect(self.duck, read_only=True) as con:
                return con.execute(
                    f"SELECT * FROM {table} WHERE run_id = ?", [self.run_id]
                ).df()
        except Exception:  # pragma: no cover - fallback path
            return pd.DataFrame()

    def _try_csv(self, name: str) -> pd.DataFrame:
        p = Path("out/snapshots") / self.run_id / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
        return pd.DataFrame()

    def odds_snapshot(self, run_id: str, season: int, week: int):
        df = self._try_duck("odds_snapshots")
        if df.empty:
            df = self._try_csv("odds")
        return [OddsRow(**r) for r in df.to_dict(orient="records")]

    def injuries_snapshot(self, run_id: str, season: int, week: int):
        df = self._try_duck("injury_snapshots")
        if df.empty:
            df = self._try_csv("injuries")
        return [InjuryRow(**r) for r in df.to_dict(orient="records")]

    def weather_snapshot(self, run_id: str, season: int, week: int):
        df = self._try_duck("weather_snapshots")
        if df.empty:
            df = self._try_csv("weather")
        return [WeatherRow(**r) for r in df.to_dict(orient="records")]


def get_vendor():
    """Auto-pick vendor:
       - if SNAPSHOT_RUN_ID set → ReplayVendor
       - else live (OddsAPIClient if key) → fallback DemoVendor
    """

    snap_run = os.environ.get("SNAPSHOT_RUN_ID")
    if snap_run:
        from ironclad.settings import get_settings

        settings = get_settings()
        return ReplayVendor(settings.duckdb_path, snap_run)
    key = os.environ.get("ODDSAPI__KEY")
    return OddsAPIClient(key)
