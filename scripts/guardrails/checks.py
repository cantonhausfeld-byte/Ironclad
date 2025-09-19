from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ironclad.schemas.pick import Grade, Pick

DEFAULT_GRADE_CAPS: dict[Grade, int] = {
    Grade.A: 5,
    Grade.B: 10,
    Grade.C: 15,
}


def grade_caps(picks: Iterable[Pick], caps: dict[Grade, int] | None = None) -> dict[str, object]:
    caps = caps or DEFAULT_GRADE_CAPS
    counts: Counter[Grade] = Counter(pick.grade for pick in picks)
    failures = {
        grade.value: counts.get(grade, 0)
        for grade, cap in caps.items()
        if counts.get(grade, 0) > cap
    }
    return {
        "name": "grade_caps",
        "passed": not failures,
        "counts": {grade.value: counts.get(grade, 0) for grade in Grade},
        "caps": {grade.value: caps.get(grade, float("inf")) for grade in Grade},
        "failures": failures,
    }


def price_sanity(
    picks: Iterable[Pick],
    *,
    min_price: int = -2000,
    max_price: int = 2000,
) -> dict[str, object]:
    out_of_range = [
        {
            "game_id": pick.game_id,
            "side": pick.side,
            "price_american": pick.price_american,
        }
        for pick in picks
        if pick.price_american < min_price or pick.price_american > max_price
    ]
    return {
        "name": "price_sanity",
        "passed": not out_of_range,
        "min_price": min_price,
        "max_price": max_price,
        "violations": out_of_range,
    }


def run_guardrails(picks: Iterable[Pick]) -> list[dict[str, object]]:
    picks_list = list(picks)
    return [
        grade_caps(picks_list),
        price_sanity(picks_list),
    ]
