from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os, time, random
import requests

@dataclass
class OddsRow:
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
    ts_utc: str
    venue_id: str
    game_id: str
    temp_f: float | None
    wind_mph: float | None
    precip_prob: float | None
    season: int
    week: int

class VendorClient:
    """Base class with graceful fallbacks."""
    def odds_snapshot(self, season:int, week:int) -> List[OddsRow]:
        raise NotImplementedError

    def injuries_snapshot(self, season:int, week:int) -> List[InjuryRow]:
        raise NotImplementedError

    def weather_snapshot(self, season:int, week:int) -> List[WeatherRow]:
        raise NotImplementedError

class DemoVendor(VendorClient):
    """Generates small synthetic snapshots that match our schema (for offline/demo)."""
    def odds_snapshot(self, season:int, week:int) -> List[OddsRow]:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[OddsRow] = []
        for i in range(4):
            gid = f"{season}W{week}_G{i+1}"
            for mkt in ["ML","ATS","OU"]:
                line = None
                price = random.choice([-110,-105,+100,+120,+140])
                if mkt == "ATS": line = random.choice([-3.5,-2.5,-1.5,+1.5,+2.5,+3.5])
                if mkt == "OU": line = random.choice([41.5,43.5,45.5,47.5])
                rows.append(OddsRow(now,"DemoBook",gid,mkt,line,price,"demo",season,week))
        return rows

    def injuries_snapshot(self, season:int, week:int) -> List[InjuryRow]:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[InjuryRow] = []
        for team in ["PHI","DAL","NYG","WAS"]:
            rows.append(InjuryRow(now,f"{team}_RB1","RB One",team,"Questionable",0.6,f"{season}W{week}_G1",season,week))
        return rows

    def weather_snapshot(self, season:int, week:int) -> List[WeatherRow]:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rows: List[WeatherRow] = []
        for i in range(4):
            gid = f"{season}W{week}_G{i+1}"
            rows.append(WeatherRow(now,f"VENUE{i+1}",gid,70.0+2*i,8.0+2*i,0.1*i,season,week))
        return rows

class OddsAPIClient(VendorClient):
    """Example live client (OddsAPI-ish). If key missing, falls back to DemoVendor."""
    BASE = "https://api.the-odds-api.com/v4"
    def __init__(self, key: Optional[str]):
        self.key = key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ironclad/1.0"})
        self._demo = DemoVendor()

    def _has_key(self) -> bool:
        return bool(self.key)

    def odds_snapshot(self, season:int, week:int) -> List[OddsRow]:
        if not self._has_key():
            return self._demo.odds_snapshot(season, week)
        # NOTE: This is a skeleton. Adapt endpoint/params to your provider.
        try:
            # Example call; replace with your actual schedule/markets fetch
            # r = self.session.get(f"{self.BASE}/sports/americanfootball_nfl/odds", params={"apiKey": self.key, ...}, timeout=10)
            # r.raise_for_status()
            # payload = r.json()
            # Transform payload -> OddsRow list
            return self._demo.odds_snapshot(season, week)  # placeholder transformation
        except Exception:
            return self._demo.odds_snapshot(season, week)

    def injuries_snapshot(self, season:int, week:int) -> List[InjuryRow]:
        return self._demo.injuries_snapshot(season, week)

    def weather_snapshot(self, season:int, week:int) -> List[WeatherRow]:
        return self._demo.weather_snapshot(season, week)

def get_vendor() -> VendorClient:
    key = os.environ.get("ODDSAPI__KEY")
    return OddsAPIClient(key)
