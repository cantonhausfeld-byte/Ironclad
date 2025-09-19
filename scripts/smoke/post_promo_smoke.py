import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import requests

DUCK = os.environ.get("DUCK", "out/ironclad.duckdb")
PROFILE = os.environ.get("PROFILE", "prod")
SEASON = os.environ.get("SEASON")
WEEK = os.environ.get("WEEK")
SEED = os.environ.get("SEED", "123")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "")


def _run(cmd, extra_env=None, fail_ok=False):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print("→", " ".join(cmd))
    rc = subprocess.call(cmd, env=env)
    if rc != 0 and not fail_ok:
        print(f"Command failed: {' '.join(cmd)}")
        sys.exit(rc)
    return rc


def _latest_run_id(con):
    q = "SELECT run_id FROM runs ORDER BY started_at DESC NULLS LAST LIMIT 1"
    row = con.execute(q).fetchone()
    return row[0] if row else None


def _summarize(con, run_id):
    # basic totals + grade mix + top exposure
    s = {}
    picks = con.execute(
        """
        SELECT grade, COUNT(*) AS n, SUM(stake_units) AS stake
        FROM picks WHERE run_id = ?
        GROUP BY grade
    """,
        [run_id],
    ).df()
    totals = (
        con.execute("SELECT SUM(stake_units) FROM picks WHERE run_id = ?", [run_id]).fetchone()[0]
        or 0.0
    )
    s["totals_units"] = float(totals)
    s["by_grade"] = {
        str(r["grade"]): {"n": int(r["n"]), "stake": float(r["stake"] or 0.0)}
        for _, r in picks.iterrows()
    }

    exposure = con.execute(
        """
        SELECT market, side, SUM(stake_units) AS stake
        FROM picks WHERE run_id = ?
        GROUP BY market, side
        ORDER BY stake DESC NULLS LAST
        LIMIT 10
    """,
        [run_id],
    ).df()
    s["top_exposure"] = [
        {"market": market, "side": side, "stake": float(stake)}
        for market, side, stake in exposure.itertuples(index=False)
    ]
    return s


def _format_markdown(run_id, summary, profile):
    lines = []
    lines.append(f"*Ironclad post-promotion smoke — profile `{profile}`*")
    lines.append(f"Run: `{run_id}`")
    lines.append(f"Total stake: *{summary['totals_units']:.2f}u*")
    if summary.get("by_grade"):
        parts = []
        for grade, obj in summary["by_grade"].items():
            parts.append(f"{grade}: {obj['n']} (∑ {obj['stake']:.2f}u)")
        lines.append("Grades → " + " | ".join(parts))
    if summary.get("top_exposure"):
        lines.append("_Top exposure:_")
        for row in summary["top_exposure"]:
            lines.append(f"• {row['market']}:{row['side']} — {row['stake']:.2f}u")
    return "\n".join(lines)


def _maybe_slack(md):
    if not SLACK_WEBHOOK:
        print("No SLACK_WEBHOOK set; skipping Slack.")
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": md}, timeout=10)
        print("Posted smoke summary to Slack.")
    except Exception as exc:  # pragma: no cover - best effort notification
        print("Slack webhook failed:", exc)


def main():
    # 1) preslate with prod
    extra = {"PROFILE": PROFILE, "SEED": SEED}
    if SEASON:
        extra["SEASON"] = SEASON
    if WEEK:
        extra["WEEK"] = WEEK
    _run(["make", "preslate"], extra_env=extra)
    _run(["make", "size"], extra_env=extra, fail_ok=True)  # sizing might be a no-op early on
    _run(["make", "record-run"], extra_env=extra)

    # 2) read latest run and summarize
    with duckdb.connect(DUCK, read_only=True) as con:
        run_id = _latest_run_id(con)
        if not run_id:
            print("No run found after smoke.")
            sys.exit(2)

        summary = _summarize(con, run_id)
    md = _format_markdown(run_id, summary, PROFILE)

    # 3) write report
    outdir = Path("out/reports")
    outdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    (outdir / f"smoke_{PROFILE}_{ts}.md").write_text(md, encoding="utf-8")
    (outdir / f"smoke_{PROFILE}_{ts}.json").write_text(
        json.dumps({"run_id": run_id, "summary": summary}, indent=2),
        encoding="utf-8",
    )
    print("\n=== Smoke Summary ===\n" + md)

    # 4) optional Slack
    _maybe_slack(md)


if __name__ == "__main__":
    main()
