import duckdb, json
from pathlib import Path
from pandas import DataFrame

DDL = """
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY,
  season INT, week INT, profile TEXT, started_at TIMESTAMP, settings_json JSON
);
CREATE TABLE IF NOT EXISTS picks(
  run_id TEXT, game_id TEXT, season INT, week INT, market TEXT, side TEXT, line DOUBLE,
  price_american INT, model_prob DOUBLE, fair_price_american INT, ev_percent DOUBLE,
  z_score DOUBLE, robust_ev_percent DOUBLE, grade TEXT, kelly_fraction DOUBLE,
  stake_units DOUBLE, book TEXT, ts_created TIMESTAMP
);
CREATE TABLE IF NOT EXISTS odds_snapshots(
  ts_utc TIMESTAMP, book TEXT, game_id TEXT, market TEXT, line DOUBLE, price_american INT,
  source TEXT, season INT, week INT
);
-- NEW: sized stakes history
CREATE TABLE IF NOT EXISTS picks_sized(
  run_id TEXT, game_id TEXT, season INT, week INT, market TEXT, side TEXT, line DOUBLE,
  price_american INT, model_prob DOUBLE, fair_price_american INT, ev_percent DOUBLE,
  grade TEXT, book TEXT,
  kelly_fraction DOUBLE, stake_units DOUBLE,
  ts_created TIMESTAMP
);
"""

def connect(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(path)
    con.execute(DDL)
    return con

def write_run(con, manifest: dict):
    con.execute(
        "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, now(), ?)",
        [
            manifest["run_id"],
            manifest["season"],
            manifest["week"],
            manifest.get("profile","local"),
            json.dumps(manifest.get("settings_json", {})),
        ],
    )

def write_picks(con, df: DataFrame):
    if df is None or len(df)==0: return
    con.register("picks_df", df)
    con.execute("INSERT INTO picks SELECT * FROM picks_df")
    con.unregister("picks_df")

def write_odds_snapshots(con, df: DataFrame):
    if df is None or len(df)==0: return
    con.register("odds_df", df)
    con.execute("INSERT INTO odds_snapshots SELECT * FROM odds_df")
    con.unregister("odds_df")

def write_picks_sized(con, df: DataFrame):
    """
    Expects columns at least:
      ['run_id','game_id','season','week','market','side','line','price_american',
       'model_prob','fair_price_american','ev_percent','grade','book',
       'kelly_fraction','stake_units','ts_created']
    Extra columns are ignored; missing columns should be filled by caller.
    """
    if df is None or len(df)==0: return
    # Ensure all required columns exist (tolerate CSVs that lack some fields)
    required = ["run_id","game_id","season","week","market","side","line","price_american",
                "model_prob","fair_price_american","ev_percent","grade","book",
                "kelly_fraction","stake_units","ts_created"]
    for c in required:
        if c not in df.columns:
            df[c] = None
    df2 = df[required].copy()
    con.register("picks_sized_df", df2)
    con.execute("INSERT INTO picks_sized SELECT * FROM picks_sized_df")
    con.unregister("picks_sized_df")
