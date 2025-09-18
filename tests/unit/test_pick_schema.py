from ironclad.schemas.pick import Pick, Market, Grade


def test_pick_schema():
    p = Pick(
        run_id="r1",
        game_id="g1",
        season=2025,
        week=1,
        market=Market.ML,
        side="WAS",
        line=None,
        price_american=-110,
        model_prob=0.55,
        fair_price_american=-122,
        ev_percent=1.0,
        z_score=0.0,
        robust_ev_percent=0.8,
        grade=Grade.B,
        kelly_fraction=0.05,
        stake_units=0.0,
    )
    assert p.market == Market.ML and 0 <= p.model_prob <= 1
