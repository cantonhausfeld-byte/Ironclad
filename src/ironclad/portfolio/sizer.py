from __future__ import annotations

import pandas as pd


def _ensure_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def size_portfolio(
    picks: pd.DataFrame,
    *,
    bankroll_units: float,
    kelly_scale: float,
    max_per_bet_u: float,
    max_per_game_u: float,
    max_total_u: float,
) -> pd.DataFrame:
    """Apply simple Kelly-based sizing with exposure guardrails.

    The algorithm:
    1. Computes the unbounded Kelly stake (bankroll * kelly_fraction * kelly_scale).
    2. Clamps each bet to ``max_per_bet_u``.
    3. Scales bets within a game proportionally if they exceed ``max_per_game_u``.
    4. Scales the entire portfolio if total exposure exceeds ``max_total_u``.
    """

    df = picks.copy()
    if "kelly_fraction" not in df.columns:
        df["kelly_fraction"] = 0.0

    base = _ensure_numeric(df["kelly_fraction"]) * float(bankroll_units) * float(kelly_scale)
    df["stake_units"] = base.clip(lower=0.0, upper=float(max_per_bet_u))

    if max_per_game_u is not None and max_per_game_u > 0:
        grouped = df.groupby("game_id", dropna=False)["stake_units"].sum()
        for gid, total in grouped.items():
            if total > max_per_game_u and total > 0:
                factor = max_per_game_u / total
                df.loc[df["game_id"] == gid, "stake_units"] *= factor

    total_units = float(df["stake_units"].sum())
    if max_total_u is not None and max_total_u > 0 and total_units > max_total_u and total_units > 0:
        factor = max_total_u / total_units
        df["stake_units"] *= factor

    df["stake_units"] = df["stake_units"].round(4)
    return df
