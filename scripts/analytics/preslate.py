import os
import pandas as pd
from ironclad.runner.run_board import synthesize_picks


def main():
    season = int(os.environ.get("SEASON", "2025"))
    week = int(os.environ.get("WEEK", "1"))
    run_id = f"preslate-{season}W{week}"
    picks = synthesize_picks(run_id, season, week)
    os.makedirs("out/picks", exist_ok=True)
    if not picks:
        print("No picks produced.")
        return
    df = pd.DataFrame([p.model_dump() for p in picks])
    path = f"out/picks/{season}W{week}_picks.csv"
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} picks to {path}")


if __name__ == "__main__":
    main()
