
from ironclad.utils.odds import american_to_prob, prob_to_american
def test_roundtrip_not_extreme():
    for price in [-150, -110, -105, 100, 120, 220, 350]:
        p = american_to_prob(price)
        if 0.01 < p < 0.99 and p != 0.5:
            _ = prob_to_american(p)
