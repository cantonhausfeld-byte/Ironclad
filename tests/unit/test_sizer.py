import pandas as pd
from ironclad.portfolio.sizer import size_portfolio

def test_size_caps():
    df = pd.DataFrame([
        {"game_id":"G1","price_american":-110,"model_prob":0.55,"ev_percent":2.0,"grade":"A","side":"PHI","market":"ATS"},
        {"game_id":"G1","price_american":-110,"model_prob":0.54,"ev_percent":1.2,"grade":"B","side":"DAL","market":"ATS"},
        {"game_id":"G2","price_american":+130,"model_prob":0.45,"ev_percent":1.0,"grade":"C","side":"NYG","market":"ML"},
    ])
    sized = size_portfolio(df, bankroll_units=100.0, kelly_scale=0.25, max_per_bet_u=3.0, max_per_game_u=5.0, max_total_u=6.0)
    assert "stake_units" in sized.columns
    assert sized["stake_units"].ge(0).all()
    assert sized.groupby("game_id")["stake_units"].sum().max() <= 5.0 + 1e-6
    assert sized["stake_units"].sum() <= 6.0 + 1e-6
