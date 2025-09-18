import duckdb, json
from pathlib import Path
from pandas import DataFrame

DDL = """
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY,
  season INT, week INT, profile TEXT,
  started_at TIMESTAMP, code_version TEXT, host TEXT,
  settings_json JSON
);

CREATE TABLE IF NOT EXISTS odds_snapshots(
  run_id TEXT, ts_utc TIMESTAMP, book TEXT, game_id TEXT, market TEXT,
  line DOUBLE, price_american INT, source TEXT, season INT, week INT
);

CREATE TABLE IF NOT EXISTS injury_snapshots(
  run_id TEXT, ts_utc TIMESTAMP, player_id TEXT, player_name TEXT, team TEXT,
  status TEXT, prob_active DOUBLE, game_id TEXT, season INT, week INT
);

CREATE TABLE IF NOT EXISTS weather_snapshots(
  run_id TEXT, ts_utc TIMESTAMP, venue_id TEXT, game_id TEXT,
  temp_f DOUBLE, wind_mph DOUBLE, precip_prob DOUBLE, season INT, week INT
);

CREATE TABLE IF NOT EXISTS features(
  run_id TEXT, game_id TEXT, key TEXT, blob JSON
);

CREATE TABLE IF NOT EXISTS model_outputs(
  run_id TEXT, game_id TEXT, market TEXT, side TEXT, line DOUBLE,
  model_prob DOUBLE, fair_price_american INT, sd DOUBLE, blob JSON
);

CREATE TABLE IF NOT EXISTS picks(
  run_id TEXT, game_id TEXT, season INT, week INT, market TEXT, side TEXT, line DOUBLE,
  price_american INT, model_prob DOUBLE, fair_price_american INT, ev_percent DOUBLE,
  z_score DOUBLE, robust_ev_percent DOUBLE, grade TEXT, kelly_fraction DOUBLE,
  stake_units DOUBLE, book TEXT, ts_created TIMESTAMP
);

CREATE TABLE IF NOT EXISTS picks_sized(
  run_id TEXT, game_id TEXT, season INT, week INT, market TEXT, side TEXT, line DOUBLE,
  price_american INT, model_prob DOUBLE, fair_price_american INT, ev_percent DOUBLE,
  grade TEXT, book TEXT,
  kelly_fraction DOUBLE, stake_units DOUBLE,
  ts_created TIMESTAMP
);

CREATE TABLE IF NOT EXISTS change_log(
  run_id TEXT, game_id TEXT, reason TEXT, delta_json JSON, ts TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledger(
  bet_id TEXT, run_id TEXT, pick_key TEXT, stake_u DOUBLE,
  placed_price INT, ts_placed TIMESTAMP, ts_closed TIMESTAMP, closing_price INT, clv DOUBLE
);
"""

def connect(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(path)
    con.execute(DDL)
    return con

def write_run(con, manifest: dict):
    con.execute(
        "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            manifest["run_id"],
            manifest["season"],
            manifest["week"],
            manifest.get("profile","local"),
            manifest.get("started_at"),
            manifest.get("code_version","dev"),
            manifest.get("host",""),
            json.dumps(manifest.get("settings_json", {})),
        ],
    )

def _insert_df(con, table: str, df: DataFrame):
    if df is None or len(df)==0: return
    con.register("df_tmp", df)
    con.execute(f"INSERT INTO {table} SELECT * FROM df_tmp")
    con.unregister("df_tmp")

def write_odds_snapshots(con, df: DataFrame): _insert_df(con, "odds_snapshots", df)
def write_injury_snapshots(con, df: DataFrame): _insert_df(con, "injury_snapshots", df)
def write_weather_snapshots(con, df: DataFrame): _insert_df(con, "weather_snapshots", df)
def write_features(con, df: DataFrame): _insert_df(con, "features", df)
def write_model_outputs(con, df: DataFrame): _insert_df(con, "model_outputs", df)
def write_picks(con, df: DataFrame): _insert_df(con, "picks", df)
def write_picks_sized(con, df: DataFrame): _insert_df(con, "picks_sized", df)
def write_change_log(con, df: DataFrame): _insert_df(con, "change_log", df)
def write_ledger(con, df: DataFrame): _insert_df(con, "ledger", df)
