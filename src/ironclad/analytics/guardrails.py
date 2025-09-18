from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import duckdb
import pandas as pd

from ironclad.settings import get_settings

_BOARD_COLUMNS = [
    "run_id",
    "season",
    "week",
    "game_id",
    "market",
    "side",
    "line",
    "price_american",
    "model_prob",
    "ev_percent",
    "grade",
    "book",
    "kelly_fraction",
    "stake_units",
    "ts_created",
]


@dataclass
class ExposureCaps:
    max_total_u: float = 25.0
    max_team_u: float = 10.0
    max_market_u: float = 15.0
    max_game_u: float = 10.0
    require_min_picks: int = 1


def caps_from_settings() -> ExposureCaps:
    s = get_settings()
    return ExposureCaps(
        max_total_u=s.CAPS__MAX_TOTAL_U,
        max_team_u=s.CAPS__MAX_TEAM_U,
        max_market_u=s.CAPS__MAX_MARKET_U,
        max_game_u=s.CAPS__MAX_GAME_U,
        require_min_picks=s.CAPS__REQUIRE_MIN_PICKS,
    )


def _con(duck_path: str):
    path = Path(duck_path)
    if not path.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(duck_path, read_only=True)


def _load_board(con, season: int, week: int, sized: bool = True) -> pd.DataFrame:
    table = "picks_sized" if sized else "picks"
    q = f"""
    SELECT run_id, season, week, game_id, market, side, line, price_american,
           model_prob, ev_percent, grade, book,
           kelly_fraction, stake_units, ts_created
    FROM {table}
    WHERE season = ? AND week = ?
    """
    return con.execute(q, [season, week]).df()


def check_exposure(
    duck_path: str,
    season: int,
    week: int,
    caps: ExposureCaps | None = None,
    *,
    sized: bool = True,
) -> Tuple[bool, List[Dict[str, Any]]]:
    if caps is None:
        caps = caps_from_settings()
    con = _con(duck_path)
    if con is None:
        board = pd.DataFrame(columns=_BOARD_COLUMNS)
    else:
        try:
            board = _load_board(con, season, week, sized=sized)
        except duckdb.Error:
            board = pd.DataFrame(columns=_BOARD_COLUMNS)
    violations: List[Dict[str, Any]] = []

    if board.empty or len(board) < caps.require_min_picks:
        violations.append(
            {
                "type": "insufficient_picks",
                "have": len(board),
                "need": caps.require_min_picks,
            }
        )
        return False, violations

    total_u = float(board["stake_units"].fillna(0).sum())
    if total_u > caps.max_total_u:
        violations.append({"type": "total_u", "value": total_u, "cap": caps.max_total_u})

    by_game = board.groupby("game_id", dropna=False)["stake_units"].sum().sort_values(ascending=False)
    for gid, u in by_game.items():
        if u > caps.max_game_u:
            violations.append(
                {"type": "game_u", "key": gid, "value": float(u), "cap": caps.max_game_u}
            )

    tmp = board.copy()
    tmp["team_key"] = tmp["side"].astype(str).str.split(":").str[0]
    by_team = tmp.groupby("team_key", dropna=False)["stake_units"].sum().sort_values(ascending=False)
    for team, u in by_team.items():
        if u > caps.max_team_u:
            violations.append(
                {
                    "type": "team_u",
                    "key": None if pd.isna(team) else str(team),
                    "value": float(u),
                    "cap": caps.max_team_u,
                }
            )

    by_market = board.groupby("market", dropna=False)["stake_units"].sum().sort_values(ascending=False)
    for mkt, u in by_market.items():
        if u > caps.max_market_u:
            violations.append(
                {
                    "type": "market_u",
                    "key": None if pd.isna(mkt) else str(mkt),
                    "value": float(u),
                    "cap": caps.max_market_u,
                }
            )

    return (len(violations) == 0), violations
