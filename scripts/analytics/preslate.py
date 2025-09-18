import os
from datetime import datetime

import click
import pandas as pd

from ironclad.runner.run_board import synthesize_picks
from ironclad.schemas.pick import Pick

def _picks_to_frame(picks: list[Pick]) -> pd.DataFrame:
    return pd.DataFrame([p.model_dump() for p in picks]) if picks else pd.DataFrame()

@click.command()
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--outdir", type=str, default="out/picks")
def main(season: int, week: int, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    run_id = f"preslate-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    picks = synthesize_picks(run_id, season, week)
    if not picks:
        print("No picks produced.")
        return
    df = _picks_to_frame(picks)
    out_path = os.path.join(outdir, f"{season}W{week}_picks.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote picks: {out_path} rows={len(df)}")

if __name__ == "__main__":
    main()
