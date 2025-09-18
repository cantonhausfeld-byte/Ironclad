import pandas as pd, duckdb, os
from ironclad.analytics.guardrails import check_exposure, ExposureCaps

def _prep_db(tmp_path):
    path = tmp_path / "t.duckdb"
    con = duckdb.connect(str(path))
    con.execute("""
    CREATE TABLE picks_sized(
      run_id TEXT, season INT, week INT, game_id TEXT, market TEXT, side TEXT, line DOUBLE,
      price_american INT, model_prob DOUBLE, ev_percent DOUBLE, grade TEXT, book TEXT,
      kelly_fraction DOUBLE, stake_units DOUBLE, ts_created TIMESTAMP
    );
    """)
    con.execute("INSERT INTO picks_sized VALUES "
                "('r1',2025,1,'G1','ATS','PHI',-2.5,-110,0.55,2.0,'A','DK',0.1,6.0,now()),"
                "('r1',2025,1,'G1','ATS','DAL',+2.5,-110,0.52,1.0,'B','DK',0.05,5.0,now()),"
                "('r1',2025,1,'G2','ML','NYG',NULL,130,0.45,1.0,'C','DK',0.03,1.0,now())")
    con.close()
    return str(path)

def test_guardrails_total_violation(tmp_path):
    duck = _prep_db(tmp_path)
    caps = ExposureCaps(max_total_u=10.0, max_team_u=100, max_market_u=100, max_game_u=100)
    ok, violations = check_exposure(duck, 2025, 1, caps, sized=True)
    assert not ok
    assert any(v["type"] == "total_u" for v in violations)

def test_guardrails_game_violation(tmp_path):
    duck = _prep_db(tmp_path)
    caps = ExposureCaps(max_total_u=100, max_team_u=100, max_market_u=100, max_game_u=8.0)
    ok, violations = check_exposure(duck, 2025, 1, caps, sized=True)
    assert not ok
    assert any(v["type"] == "game_u" for v in violations)
