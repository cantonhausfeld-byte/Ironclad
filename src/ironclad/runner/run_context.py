from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, os, socket, uuid
from typing import Any, Dict
from ironclad.settings import get_settings

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class RunContext:
    run_id: str
    season: int
    week: int
    profile: str
    seed: int
    started_at: str
    code_version: str
    host: str
    settings_json: Dict[str, Any]

    @staticmethod
    def new(season: int, week: int, profile: str, seed: int) -> "RunContext":
        s = get_settings()
        # Run ID: short UUID + hash of key params
        salt = f"{season}-{week}-{profile}-{seed}-{_now_iso()}-{uuid.uuid4()}"
        rid = "run_" + hashlib.sha1(salt.encode()).hexdigest()[:12]
        code_version = os.getenv("IRONCLAD_VERSION", "dev")
        return RunContext(
            run_id=rid,
            season=season,
            week=week,
            profile=profile,
            seed=seed,
            started_at=_now_iso(),
            code_version=code_version,
            host=socket.gethostname(),
            settings_json={
                "profile": profile,
                "seed": seed,
                "caps": {
                    "max_total_u": getattr(s, "CAPS__MAX_TOTAL_U", 25.0),
                    "max_team_u": getattr(s, "CAPS__MAX_TEAM_U", 10.0),
                    "max_market_u": getattr(s, "CAPS__MAX_MARKET_U", 15.0),
                    "max_game_u": getattr(s, "CAPS__MAX_GAME_U", 10.0),
                },
                "sizing": {
                    "bankroll_units": getattr(s, "SIZING__BANKROLL_UNITS", 100.0),
                    "kelly_scale": getattr(s, "SIZING__KELLY_SCALE", 0.25),
                },
            },
        )

    def manifest(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "season": self.season,
            "week": self.week,
            "profile": self.profile,
            "started_at": self.started_at,
            "code_version": self.code_version,
            "host": self.host,
            "settings_json": self.settings_json,
        }
