from scripts.guardrails.checks import grade_caps, price_sanity, run_guardrails

from ironclad.schemas.pick import Grade, Market, Pick


def make_pick(grade: Grade, price: int) -> Pick:
    return Pick(
        run_id="run-1",
        game_id="game-1",
        season=2025,
        week=1,
        market=Market.ML,
        side="WAS",
        line=None,
        price_american=price,
        model_prob=0.55,
        fair_price_american=-120,
        ev_percent=2.0,
        z_score=0.0,
        robust_ev_percent=2.0,
        grade=grade,
        kelly_fraction=0.05,
        stake_units=1.0,
    )


def test_grade_caps_and_price_sanity():
    picks = [make_pick(Grade.A, -110) for _ in range(3)] + [make_pick(Grade.B, 2500)]
    caps_result = grade_caps(picks, {Grade.A: 2, Grade.B: 5, Grade.C: 5})
    assert caps_result["passed"] is False
    sanity_result = price_sanity(picks, min_price=-2000, max_price=2000)
    assert sanity_result["passed"] is False

    combined = run_guardrails(picks)
    assert len(combined) == 2
    assert any(not result["passed"] for result in combined)
