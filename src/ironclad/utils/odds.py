
def american_to_prob(price: int) -> float:
    if price == 0:
        raise ValueError("Price cannot be 0")
    return 100.0/(price+100.0) if price>0 else (-price)/((-price)+100.0)
def prob_to_american(p: float) -> int:
    if not (0 < p < 1):
        raise ValueError("p must be in (0,1)")
    return int(round(100*p/(1-p))) if p>=0.5 else int(round(-100*(1-p)/p))
