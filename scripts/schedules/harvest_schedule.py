import csv, os
from datetime import datetime, timezone
import click
from ironclad.settings import get_settings
from ironclad.services.schedule_client import harvest_schedule_from_oddsapi


@click.command()
@click.option("--season", type=int, default=2025)
@click.option("--week", type=str, default="auto", help="auto or int")
@click.option("--outdir", type=str, default="out/schedules")
def main(season: int, week: str, outdir: str):
    """
    Harvest the week's schedule. Uses OddsAPI commence_time if ODDSAPI__KEY is set,
    else writes a deterministic demo schedule.
    """
    s = get_settings()
    os.makedirs(outdir, exist_ok=True)
    wk = 1 if week=="auto" else int(week)

    rows = []
    if s.ODDSAPI__KEY:
        games, status = harvest_schedule_from_oddsapi(api_key=s.ODDSAPI__KEY, season=season, week=wk)
        print("Schedule status:", status.state, "-", status.message)
        for g in games:
            rows.append(dict(season=g.season, week=g.week, game_id=g.game_id, home=g.home, away=g.away, kickoff_utc_iso=g.kickoff_utc_iso, venue=g.venue))

    if not rows:
        # Fallback: 1pm ET (17:00Z) Sunday demo kickoff
        kt = "2025-09-21T17:00:00Z"
        rows = [dict(season=season, week=wk, game_id=f"W{wk}_DEMO1", home="PHI", away="DAL", kickoff_utc_iso=kt, venue="LFF")]
        print("No API schedule available → wrote demo schedule.")

    rows = sorted(rows, key=lambda r: r["kickoff_utc_iso"])
    with open(f"{outdir}/master_schedule.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["season","week","game_id","home","away","kickoff_utc_iso","venue"])
        w.writeheader(); w.writerows(rows)

    earliest = rows[0]["kickoff_utc_iso"]
    with open(f"{outdir}/kickoffs.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["season","week","kickoff_utc_iso","earliest_flag"])
        w.writeheader(); w.writerow({"season":season,"week":wk,"kickoff_utc_iso":earliest,"earliest_flag":1})

    print(f"Wrote master_schedule.csv and kickoffs.csv to {outdir}")


if __name__ == "__main__":
    main()
