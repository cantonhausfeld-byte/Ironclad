from ironclad.utils.odds_math import american_to_prob, prob_to_american


def test_roundtrip():
    for american in [-110, -120, 100, 150]:
        probability = american_to_prob(american)
        converted = prob_to_american(probability)
        assert isinstance(converted, int)
