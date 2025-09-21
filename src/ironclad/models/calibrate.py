def clamp(p: float, lo: float = 0.02, hi: float = 0.98) -> float:
    return max(min(p, hi), lo)
