import os, hmac, hashlib, time, json, re
from typing import Dict
from urllib.parse import parse_qs

import httpx
from fastapi import FastAPI, Request, Response, HTTPException

# ---- Config (env) ----
GITHUB_OWNER      = os.getenv("GITHUB_OWNER", "")        # e.g. your-org
GITHUB_REPO       = os.getenv("GITHUB_REPO", "")         # e.g. ironclad
GITHUB_REF        = os.getenv("GITHUB_REF", "main")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN", "")        # fine-grained PAT with Actions:write
SLACK_SIGNING_KEY = os.getenv("SLACK_SIGNING_SECRET", "")
ALLOWED_USERS     = set(filter(None, os.getenv("ALLOWED_USER_IDS", "").split(",")))  # optional Slack user IDs

WF_PROMOTE = "promote_and_smoke.yml"
WF_SMOKE   = "nightly_smoke.yml"

app = FastAPI()


def verify_slack(req: Request, body: bytes):
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        raise HTTPException(401, "Missing Slack headers")
    # 5 min tolerance
    if abs(time.time() - int(ts)) > 60 * 5:
        raise HTTPException(401, "Stale Slack signature")
    base = f"v0:{ts}:{body.decode('utf-8')}".encode("utf-8")
    mac = "v0=" + hmac.new(SLACK_SIGNING_KEY.encode("utf-8"), base, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, sig):
        raise HTTPException(401, "Bad Slack signature")


def parse_slash(text: str) -> Dict[str, str]:
    # Very small parser: tokens like KEY=VALUE, plus leading verb
    # Examples:
    #   promote RUN_A=abc RUN_B=def PROFILE=prod FORCE=1
    #   smoke PROFILE=prod SEASON=2025 WEEK=3
    parts = text.strip().split()
    if not parts:
        return {"verb": ""}
    verb = parts[0].lower()
    kv = {"verb": verb}
    for tok in parts[1:]:
        m = re.match(r"([A-Za-z_]+)=(.+)", tok)
        if m:
            kv[m.group(1).upper()] = m.group(2)
    return kv


async def gh_dispatch(workflow_file: str, inputs: Dict[str, str]):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"ref": GITHUB_REF, "inputs": inputs}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code not in (201, 204):
            raise HTTPException(r.status_code, f"GitHub dispatch failed: {r.text}")


@app.post("/slash")
async def slash(request: Request):
    body = await request.body()
    verify_slack(request, body)

    data = parse_qs(body.decode("utf-8"))
    user_id = (data.get("user_id", [""])[0])
    text    = (data.get("text", [""])[0])

    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        raise HTTPException(403, "User not allowed")

    cmd = parse_slash(text)

    if cmd["verb"] == "promote":
        run_a = cmd.get("RUN_A", "")
        run_b = cmd.get("RUN_B", "")
        if not run_a or not run_b:
            return Response("Usage: /ironclad promote RUN_A=<id> RUN_B=<id> [PROFILE=prod] [FORCE=1]", media_type="text/plain")
        inputs = {
            "RUN_A": run_a,
            "RUN_B": run_b,
            "PROFILE": cmd.get("PROFILE", "prod"),
            "SEASON": cmd.get("SEASON", ""),
            "WEEK": cmd.get("WEEK", ""),
            "FORCE": "true" if cmd.get("FORCE", "0") in ("1", "true", "True") else "false",
        }
        await gh_dispatch(WF_PROMOTE, inputs)
        return Response(f"✅ Dispatched promote-and-smoke for {run_b} (baseline {run_a}) → profile {inputs['PROFILE']}", media_type="text/plain")

    elif cmd["verb"] == "smoke":
        # use nightly_smoke.yml (supports workflow_dispatch) for smoke-only
        inputs = {}  # we’ll pass PROFILE/SEASON/WEEK via env in that workflow or keep empty
        # If you want to pass profile over inputs, add to workflow and include here.
        await gh_dispatch(WF_SMOKE, inputs)
        prof = cmd.get("PROFILE", "prod")
        return Response(f"✅ Dispatched smoke (profile {prof}). Check Actions → Nightly Smoke.", media_type="text/plain")

    else:
        help_msg = (
            "Ironclad slash usage:\n"
            "• /ironclad promote RUN_A=<id> RUN_B=<id> [PROFILE=prod] [SEASON=YYYY] [WEEK=W] [FORCE=1]\n"
            "• /ironclad smoke [PROFILE=prod] [SEASON=YYYY] [WEEK=W]"
        )
        return Response(help_msg, media_type="text/plain")
