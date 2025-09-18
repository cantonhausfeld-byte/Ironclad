import argparse, datetime, json, pathlib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minute_offset", type=int, default=60)
    ap.add_argument("--emit_crontab", action="store_true")
    ap.add_argument("--outdir", type=pathlib.Path, required=True)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    target = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(minutes=args.minute_offset)
    recommended = {
        "recommended_run_utc": {
            "iso": target.isoformat().replace("+00:00", "Z"),
            "epoch": int(target.timestamp()),
        }
    }
    (args.outdir / "recommended_runs.json").write_text(json.dumps(recommended, indent=2))

    if args.emit_crontab:
        cron_line = f"{target.minute} {target.hour} * * * python scripts/ic.py run-preslate"
        (args.outdir / "cron_line_utc.txt").write_text(cron_line + "\n")


if __name__ == "__main__":
    main()
