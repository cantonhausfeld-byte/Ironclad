"""Simple portfolio sizing helpers."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"kelly_fraction", "game_id"}


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for sizing: {sorted(missing)}")
    out = df.copy()
    if "stake_units" not in out.columns:
        out["stake_units"] = 0.0
    return out


def _clip(values: pd.Series, limit: float) -> pd.Series:
    if limit <= 0:
        return values * 0.0
    return values.clip(lower=0.0, upper=limit)


def size_portfolio(
    df: pd.DataFrame,
    *,
    bankroll_units: float,
    kelly_scale: float,
    max_per_bet_u: float,
    max_per_game_u: float,
    max_total_u: float,
) -> pd.DataFrame:
    """Apply a handful of sizing rules to a picks DataFrame.

    The goal is to produce intuitive stake sizes without over-engineering the
    math. We scale Kelly fractions by the bankroll and kelly_scale, clip at the
    per-bet cap, then enforce per-game and overall exposure limits.
    """

    if bankroll_units <= 0:
        raise ValueError("bankroll_units must be positive")
    if kelly_scale < 0:
        raise ValueError("kelly_scale must be non-negative")

    sized = _ensure_columns(df)
    base = sized["kelly_fraction"].fillna(0.0) * bankroll_units * kelly_scale
    sized["stake_units"] = _clip(base, max_per_bet_u)

    if max_per_game_u >= 0:
        per_game = sized.groupby("game_id")["stake_units"].sum()
        for game_id, total in per_game.items():
            if total > max_per_game_u and total > 0:
                factor = max_per_game_u / total
                sized.loc[sized["game_id"] == game_id, "stake_units"] *= factor

    total_units = sized["stake_units"].sum()
    if max_total_u >= 0 and total_units > max_total_u and total_units > 0:
        sized["stake_units"] *= max_total_u / total_units

    return sized
