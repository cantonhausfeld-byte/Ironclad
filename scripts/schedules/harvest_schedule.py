import argparse, csv, json, pathlib, datetime


def generate_schedule(season: int, week: int):
    kickoff = datetime.datetime(season, 9, 1, 17, 0, tzinfo=datetime.timezone.utc)
    kickoff = kickoff + datetime.timedelta(days=max(0, week - 1))
    return [{
        "game_id": f"W{week}_DEMO1",
        "season": season,
        "week": week,
        "home": "PHI",
        "away": "DAL",
        "kickoff_utc_iso": kickoff.isoformat().replace("+00:00", "Z"),
        "venue": "LFF"
    }]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", required=True)
    ap.add_argument("--week", required=True)
    ap.add_argument("--outdir", type=pathlib.Path, required=True)
    args = ap.parse_args()

    season = int(args.season)
    week = 1 if args.week == "auto" else int(args.week)

    args.outdir.mkdir(parents=True, exist_ok=True)
    schedule = generate_schedule(season, week)
    csv_path = args.outdir / "master_schedule.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(schedule[0].keys()))
        writer.writeheader()
        writer.writerows(schedule)
    meta_path = args.outdir / "meta.json"
    meta_path.write_text(json.dumps({"season": season, "week": week, "rows": len(schedule)}))


if __name__ == "__main__":
    main()
