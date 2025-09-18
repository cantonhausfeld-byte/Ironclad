"""Simple bet sizing helpers."""

from __future__ import annotations

from pandas import DataFrame

DEFAULT_KELLY_FRACTION = 0.0
DEFAULT_STAKE_UNITS = 0.0


def size_portfolio(
    picks: DataFrame,
    *,
    bankroll_units: float,
    kelly_scale: float,
    max_per_bet_u: float,
    max_per_game_u: float,
    max_total_u: float,
) -> DataFrame:
    """Return a sized portfolio based on the provided picks.

    This basic implementation preserves the incoming data and ensures the
    ``kelly_fraction`` and ``stake_units`` columns exist. The sizing knobs are
    accepted for API compatibility but the strategy is intentionally simple in
    this foundational build.
    """

    sized = picks.copy()
    if "kelly_fraction" in sized.columns:
        sized["kelly_fraction"] = sized["kelly_fraction"].fillna(DEFAULT_KELLY_FRACTION)
    else:
        sized["kelly_fraction"] = DEFAULT_KELLY_FRACTION

    if "stake_units" in sized.columns:
        sized["stake_units"] = sized["stake_units"].fillna(DEFAULT_STAKE_UNITS)
    else:
        sized["stake_units"] = DEFAULT_STAKE_UNITS

    return sized
