from __future__ import annotations
import numpy as np
import pandas as pd


def american_to_decimal(a: int | float) -> float:
    a = float(a)
    if a > 0:
        return 1 + a / 100.0
    return 1 + 100.0 / (-a)


def kelly_fraction(p: float, d: float) -> float:
    # Kelly for decimal odds d: f* = (p*(d-1) - (1-p)) / (d-1)
    edge = p * (d - 1) - (1 - p)
    denom = (d - 1) if (d - 1) != 0 else 1e-9
    return max(edge / denom, 0.0)


def size_portfolio(
    picks: pd.DataFrame,
    *,
    bankroll_units: float = 100.0,
    kelly_scale: float = 0.25,
    max_per_bet_u: float = 3.0,
    max_per_game_u: float = 10.0,
    max_total_u: float = 25.0,
) -> pd.DataFrame:
    """
    Input columns: ['game_id','price_american','model_prob','ev_percent','grade','side','market',...]
    Returns a copy with 'kelly_fraction' and 'stake_units' sized under caps.
    """
    if picks.empty:
        return picks.assign(kelly_fraction=0.0, stake_units=0.0)

    d = picks["price_american"].astype(float).map(american_to_decimal)
    p = picks["model_prob"].astype(float).clip(0, 1)
    kf = p.combine(d, lambda pp, dd: kelly_fraction(pp, dd)) * kelly_scale
    stake = (kf * bankroll_units).clip(lower=0)

    # Per-bet cap
    stake = np.minimum(stake, max_per_bet_u)

    # Per-game cap (proportional scaling within each game)
    df = picks.copy()
    df["kelly_fraction"] = kf
    df["stake_units_raw"] = stake
    out_stake = []
    for gid, grp in df.groupby("game_id"):
        s = grp["stake_units_raw"].sum()
        if s > max_per_game_u and s > 0:
            scale = max_per_game_u / s
            out_stake.extend(list(grp["stake_units_raw"] * scale))
        else:
            out_stake.extend(list(grp["stake_units_raw"]))
    stake = np.array(out_stake)

    # Global cap
    tot = stake.sum()
    if tot > max_total_u and tot > 0:
        stake = stake * (max_total_u / tot)

    df["stake_units"] = np.round(stake, 3)
    grade_weight = df["grade"].map({"A": 1.0, "B": 0.8, "C": 0.6, "NO_PICK": 0.0}).fillna(1.0)
    df["stake_units"] = np.round(df["stake_units"] * grade_weight, 3)
    return df.drop(columns=["stake_units_raw"])
