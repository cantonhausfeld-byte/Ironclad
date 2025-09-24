from __future__ import annotations

from ironclad.persist.duckdb_connector import connect, write_sized_picks


def test_write_sized_picks(tmp_path):
    db_path = tmp_path / "test.duckdb"
    con = connect(str(db_path))

    rows = [
        {
            "run_id": "run-1",
            "game_id": "game-1",
            "season": 2025,
            "week": 1,
            "market": "ML",
            "side": "NYG",
            "line": None,
            "price_american": -110,
            "model_prob": 0.55,
            "fair_price_american": -120,
            "ev_percent": 2.5,
            "z_score": 0.0,
            "robust_ev_percent": 2.4,
            "grade": "A",
            "kelly_fraction": 0.05,
            "stake_units": 1.5,
            "book": "DraftKings",
            "ts_created": "2024-09-01T00:00:00",
        }
    ]

    write_sized_picks(
        con,
        rows,
        input_csv="foo_picks.csv",
        output_csv="foo_picks_sized.csv",
        sizing_config={"bankroll_units": 100, "kelly_scale": 0.25},
    )

    result = con.execute(
        """
        SELECT input_csv, output_csv, sizing_config_json, run_id, stake_units
        FROM picks_sized
        """
    ).fetchone()

    assert result[0] == "foo_picks.csv"
    assert result[1] == "foo_picks_sized.csv"
    assert "\"bankroll_units\": 100" in result[2]
    assert result[3] == "run-1"
    assert result[4] == 1.5
