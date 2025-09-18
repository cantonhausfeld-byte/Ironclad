import os, json
from dataclasses import asdict
from pathlib import Path
from typing import List
import pandas as pd
from ironclad.services.vendor_client import get_vendor, OddsRow, InjuryRow, WeatherRow
from ironclad.settings import get_settings
from ironclad.persist.duckdb_connector import (
    connect, write_odds_snapshots, write_injury_snapshots, write_weather_snapshots
)

def to_df(rows):
    if not rows: return pd.DataFrame()
    return pd.DataFrame([asdict(r) for r in rows])

def main(run_id: str, season: int, week: int):
    s = get_settings()
    duck = s.DUCKDB__PATH
    con = connect(duck)

    vendor = get_vendor()

    odds_rows: List[OddsRow] = vendor.odds_snapshot(season, week)
    inj_rows:  List[InjuryRow] = vendor.injuries_snapshot(season, week)
    wx_rows:   List[WeatherRow] = vendor.weather_snapshot(season, week)

    odds_df = to_df(odds_rows); inj_df = to_df(inj_rows); wx_df = to_df(wx_rows)

    # Write to DuckDB
    if not odds_df.empty: write_odds_snapshots(con, odds_df)
    if not inj_df.empty:  write_injury_snapshots(con, inj_df)
    if not wx_df.empty:   write_weather_snapshots(con, wx_df)

    # Also write CSV artifacts for human inspection
    out_dir = Path("out/snapshots")/run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    if not odds_df.empty: odds_df.to_csv(out_dir/"odds.csv", index=False)
    if not inj_df.empty:  inj_df.to_csv(out_dir/"injuries.csv", index=False)
    if not wx_df.empty:   wx_df.to_csv(out_dir/"weather.csv", index=False)
    (out_dir/"manifest.json").write_text(json.dumps({"run_id": run_id, "season": season, "week": week}, indent=2))

    print("Snapshot CSVs →", out_dir)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--run_id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week", type=int, required=True)
    args = p.parse_args()
    main(args.run_id, args.season, args.week)
