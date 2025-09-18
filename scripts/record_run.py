import glob, pandas as pd, click
from datetime import datetime, timezone
from ironclad.settings import get_settings
from ironclad.runner.run_context import RunContext
from ironclad.persist.duckdb_connector import (
    connect, write_run, write_picks, write_picks_sized
)

def _latest(globpat: str) -> str | None:
    files = sorted(glob.glob(globpat))
    return files[-1] if files else None

def _coerce_cols(df: pd.DataFrame, run_id: str, season: int, week: int) -> pd.DataFrame:
    # Ensure minimum columns exist for picks table
    need = ["run_id","game_id","season","week","market","side","line",
            "price_american","model_prob","fair_price_american","ev_percent",
            "z_score","robust_ev_percent","grade","kelly_fraction","stake_units",
            "book","ts_created"]
    out = df.copy()
    if "run_id" not in out.columns: out["run_id"] = run_id
    if "season" not in out.columns: out["season"] = season
    if "week" not in out.columns: out["week"] = week
    if "ts_created" not in out.columns:
        out["ts_created"] = datetime.now(timezone.utc).isoformat()
    for c in need:
        if c not in out.columns: out[c] = None
    return out[need]

@click.command()
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--profile", type=str, default="local")
@click.option("--seed", type=int, default=42)
def main(season: int, week: int, profile: str, seed: int):
    s = get_settings()
    ctx = RunContext.new(season=season, week=week, profile=profile, seed=seed)
    print("Run ID:", ctx.run_id)

    duck = getattr(s, 'DUCKDB__PATH', None) or getattr(s, 'duckdb_path', 'out/ironclad.duckdb')
    con = connect(duck)
    write_run(con, ctx.manifest())

    # Picks (required output for a board)
    picks_csv = _latest("out/picks/*_picks.csv")
    if not picks_csv:
        print("No base picks CSV found in out/picks. Aborting persist (manifest written).")
        return
    base = pd.read_csv(picks_csv)
    base2 = _coerce_cols(base, ctx.run_id, season, week)
    write_picks(con, base2)
    print("Inserted picks rows:", len(base2))

    # Sized picks (optional)
    sized_csv = _latest("out/picks/*_picks_sized.csv")
    if sized_csv:
        sized = pd.read_csv(sized_csv)
        # Ensure run_id/season/week present
        if "run_id" not in sized.columns: sized["run_id"] = ctx.run_id
        if "season" not in sized.columns: sized["season"] = season
        if "week" not in sized.columns: sized["week"] = week
        if "ts_created" not in sized.columns:
            sized["ts_created"] = base2["ts_created"]
        sized_need = ["run_id","game_id","season","week","market","side","line",
                       "price_american","model_prob","fair_price_american","ev_percent","grade","book",
                       "kelly_fraction","stake_units","ts_created"]
        for col in sized_need:
            if col not in sized.columns:
                sized[col] = None
        sized = sized[sized_need]
        write_picks_sized(con, sized)
        print("Inserted sized rows:", len(sized))
    else:
        print("No sized CSV found; skipping picks_sized.")

    print("Persisted run →", duck)

if __name__ == "__main__":
    main()
