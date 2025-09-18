from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..utils.odds import american_to_prob, prob_to_american


@dataclass(slots=True)
class BaselineConfig:
    """Static knobs for the demo baseline model."""

    market: str = "ATS"
    line: float = -2.5
    price_american: int = -110
    model_prob: float = 0.52
    book: str = "DemoSportsbook"
    kelly_fraction: float = 0.05


def _grade_from_ev(ev_percent: float) -> str:
    if ev_percent >= 2.5:
        return "A"
    if ev_percent >= 1.5:
        return "B"
    if ev_percent > 0:
        return "C"
    return "NO_PICK"


def predict(games: pd.DataFrame, config: BaselineConfig | None = None) -> pd.DataFrame:
    """Generate deterministic demo picks for the provided games."""

    config = config or BaselineConfig()
    columns = [
        "game_id",
        "season",
        "week",
        "market",
        "side",
        "line",
        "price_american",
        "model_prob",
        "fair_price_american",
        "ev_percent",
        "z_score",
        "robust_ev_percent",
        "grade",
        "kelly_fraction",
        "stake_units",
        "book",
    ]
    if games is None or games.empty:
        return pd.DataFrame(columns=columns)

    games = games.copy()
    implied_prob = american_to_prob(config.price_american)
    fair_price = prob_to_american(config.model_prob)
    ev_percent = (config.model_prob - implied_prob) * 100.0

    picks = pd.DataFrame({
        "game_id": games["game_id"],
        "season": games["season"].astype(int),
        "week": games["week"].astype(int),
        "market": config.market,
        "side": games["home"],
        "line": float(config.line),
        "price_american": int(config.price_american),
        "model_prob": float(config.model_prob),
        "fair_price_american": int(fair_price),
        "ev_percent": float(ev_percent),
    })
    picks["z_score"] = 0.0
    picks["robust_ev_percent"] = picks["ev_percent"]
    picks["grade"] = picks["ev_percent"].apply(_grade_from_ev)
    picks["kelly_fraction"] = picks["grade"].map(
        {"A": config.kelly_fraction, "B": config.kelly_fraction / 2, "C": config.kelly_fraction / 4}
    ).fillna(0.0)
    picks["stake_units"] = 0.0
    picks["book"] = config.book
    return picks[columns]
