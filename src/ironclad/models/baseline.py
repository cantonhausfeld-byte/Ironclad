from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from ..schemas.pick import Grade, Market
from ..utils.odds_math import prob_to_american


class BaselineConfig(BaseModel):
    confidence_floor: float = 0.52
    kelly_scale: float = 0.25


def predict(games: pd.DataFrame, cfg: BaselineConfig) -> pd.DataFrame:
    rows: list[dict] = []
    for _, game in games.iterrows():
        probability = max(cfg.confidence_floor, 0.5 + 0.02)
        fair = prob_to_american(probability)
        rows.append(
            dict(
                game_id=game["game_id"],
                season=int(game["season"]),
                week=int(game["week"]),
                market=Market.ATS.value,
                side=game["home"],
                line=-2.5,
                model_prob=probability,
                fair_price_american=fair,
                price_american=-110,
                ev_percent=(probability * 1.9091 - (1 - probability)) * 100,
                z_score=0.0,
                robust_ev_percent=0.0,
                grade=Grade.B.value,
                kelly_fraction=(probability * 1.9091 - (1 - probability)) / 1.9091 * cfg.kelly_scale,
                stake_units=1.0,
                book="DraftKings",
            )
        )
    return pd.DataFrame(rows)
