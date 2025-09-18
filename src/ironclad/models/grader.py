def grade_row(ev_percent: float) -> str:
    if ev_percent >= 3.0:
        return "A"
    if ev_percent >= 1.0:
        return "B"
    if ev_percent >= 0.0:
        return "C"
    return "NO_PICK"
