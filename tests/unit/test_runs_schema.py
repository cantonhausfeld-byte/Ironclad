import duckdb
from ironclad.persist.duckdb_connector import connect

def test_runs_tables_exist(tmp_path):
    path = tmp_path/"t.duckdb"
    con = connect(str(path))
    for tbl in ["runs","picks","picks_sized","odds_snapshots","injury_snapshots","weather_snapshots","model_outputs","features","ledger","change_log"]:
        assert con.execute(f"SELECT * FROM information_schema.tables WHERE table_name='{tbl}'").fetchone() is not None
