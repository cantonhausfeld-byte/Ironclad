import argparse
import duckdb
from ironclad.settings import settings

DDL = """
CREATE TABLE IF NOT EXISTS picks_sized(
  run_id TEXT,
  season INT,
  week INT,
  game_id TEXT,
  market TEXT,
  side TEXT,
  line DOUBLE,
  price_american INT,
  model_prob DOUBLE,
  ev_percent DOUBLE,
  grade TEXT,
  book TEXT,
  kelly_fraction DOUBLE,
  stake_units DOUBLE,
  ts_created TIMESTAMP
);
"""

INSERT = """
INSERT INTO picks_sized
SELECT
  run_id,
  season,
  week,
  game_id,
  market,
  side,
  line,
  price_american,
  model_prob,
  ev_percent,
  grade,
  book,
  kelly_fraction,
  CASE
    WHEN stake_units IS NULL OR stake_units = 0 THEN ROUND(COALESCE(kelly_fraction, 0) * 100, 2)
    ELSE stake_units
  END AS stake_units,
  ts_created
FROM picks
WHERE season = ? AND week = ?;
"""

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    args = parser.parse_args()

    con = duckdb.connect(settings.duckdb_path)
    con.execute(DDL)
    con.execute("DELETE FROM picks_sized WHERE season = ? AND week = ?;", [args.season, args.week])
    con.execute(INSERT, [args.season, args.week])
    con.close()

if __name__ == "__main__":
    main()
