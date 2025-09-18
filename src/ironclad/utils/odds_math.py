def american_to_prob(american: int) -> float:
    return (100 / (american + 100)) if american > 0 else (-american) / (-american + 100)


def prob_to_american(p: float) -> int:
    p = max(min(p, 0.98), 0.02)
    return int(round(100 * p / (1 - p))) if p >= 0.5 else int(round(-100 * (1 - p) / p))
