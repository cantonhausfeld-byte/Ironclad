"""FastAPI Slack slash command proxy for Ironclad automation."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import parse_qs

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

# ---- Rate limiting (very simple, in-memory) ----
RL_WINDOW_SEC = int(os.getenv("RL_WINDOW_SEC", "60"))  # 1 minute window
RL_MAX_CALLS = int(os.getenv("RL_MAX_CALLS", "6"))  # 6 requests / user / minute
_user_calls: dict[str, deque[float]] = {}


def check_rate_limit(user_id: str) -> None:
    now = time.time()
    dq = _user_calls.setdefault(user_id, deque())
    # drop old entries
    while dq and now - dq[0] > RL_WINDOW_SEC:
        dq.popleft()
    if len(dq) >= RL_MAX_CALLS:
        # too many calls in window
        raise HTTPException(429, f"Rate limit: {RL_MAX_CALLS}/{RL_WINDOW_SEC}s. Try again shortly.")
    dq.append(now)


app = FastAPI()

SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_REF = os.getenv("GITHUB_REF", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ALLOWED_USER_IDS = {
    item.strip() for item in os.getenv("ALLOWED_USER_IDS", "").split(",") if item.strip()
}

WF_PROMOTE = "promote_and_smoke.yml"
WF_SMOKE = "nightly_smoke.yml"


def _require_env(value: str | None, name: str) -> str:
    if not value:
        raise HTTPException(500, f"Missing required configuration: {name}")
    return value


def _verify_slack(headers: Dict[str, str], body: bytes) -> None:
    secret = _require_env(SLACK_SIGNING_SECRET, "SLACK_SIGNING_SECRET")
    timestamp = headers.get("x-slack-request-timestamp")
    signature = headers.get("x-slack-signature")
    if not timestamp or not signature:
        raise HTTPException(401, "Missing Slack signature headers")
    try:
        ts = int(timestamp)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(401, "Invalid Slack timestamp") from exc
    if abs(time.time() - ts) > 60 * 5:
        raise HTTPException(401, "Slack signature expired")

    basestring = f"v0:{timestamp}:{body.decode()}".encode()
    digest = hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Slack signature mismatch")


async def gh_dispatch(workflow_file: str, inputs: dict[str, str] | None = None) -> None:
    owner = _require_env(GITHUB_OWNER, "GITHUB_OWNER")
    repo = _require_env(GITHUB_REPO, "GITHUB_REPO")
    token = _require_env(GITHUB_TOKEN, "GITHUB_TOKEN")

    url = (
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
    )
    payload: dict[str, Any] = {"ref": GITHUB_REF}
    if inputs:
        payload["inputs"] = {k: v for k, v in inputs.items() if v is not None}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code not in (200, 201, 202, 204):
        raise HTTPException(response.status_code, f"GitHub dispatch failed: {response.text}")


async def gh_list_runs(workflow_file: str, per_page: int = 5) -> list[dict[str, Any]]:
    owner = _require_env(GITHUB_OWNER, "GITHUB_OWNER")
    repo = _require_env(GITHUB_REPO, "GITHUB_REPO")
    token = _require_env(GITHUB_TOKEN, "GITHUB_TOKEN")

    url = (
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs"
        f"?per_page={per_page}"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(response.status_code, f"GitHub list runs failed: {response.text}")
    return response.json().get("workflow_runs", [])


def _fmt_run(run: dict[str, Any]) -> str:
    name = run.get("name") or run.get("display_title") or "run"
    status = run.get("status")
    conclusion = run.get("conclusion") or "-"
    updated_at = run.get("updated_at")
    html_url = run.get("html_url")
    stamp = updated_at
    if updated_at:
        try:
            ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
            stamp = ts.strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            stamp = updated_at
    return f"- {name}: {status}/{conclusion} · {stamp}\n  {html_url}"


def _parse_command(text: str) -> dict[str, str]:
    tokens = [tok for tok in text.strip().split() if tok]
    if not tokens:
        return {"verb": ""}
    cmd: dict[str, str] = {"verb": tokens[0].lower()}
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            cmd[key.upper()] = value
    return cmd


@app.post("/slash")
async def slash(request: Request) -> Response:
    raw_body = await request.body()
    _verify_slack(request.headers, raw_body)
    data = parse_qs(raw_body.decode())

    user_id = data.get("user_id", [""])[0]
    text = data.get("text", [""])[0]

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        raise HTTPException(403, "User not allowed")

    check_rate_limit(user_id)

    cmd = _parse_command(text)
    verb = cmd.get("verb")

    if verb == "promote":
        await gh_dispatch(WF_PROMOTE)
        return Response(
            "✅ Dispatched promote_and_smoke workflow. Check Actions → Promote & Smoke.",
            media_type="text/plain",
        )
    if verb == "smoke":
        inputs = {
            "PROFILE": cmd.get("PROFILE", "prod"),
            "SEASON": cmd.get("SEASON", ""),
            "WEEK": cmd.get("WEEK", ""),
        }
        await gh_dispatch(WF_SMOKE, inputs)
        prof = inputs["PROFILE"]
        sea = inputs.get("SEASON") or "(auto)"
        wk = inputs.get("WEEK") or "(auto)"
        return Response(
            f"✅ Dispatched smoke (PROFILE={prof}, SEASON={sea}, WEEK={wk}). Check Actions → Nightly Smoke.",
            media_type="text/plain",
        )
    if verb == "status":
        promo = await gh_list_runs(WF_PROMOTE)
        smoke = await gh_list_runs(WF_SMOKE)
        lines = ["*Ironclad CI status*"]
        lines.append("\n*Promote & Smoke (latest)*")
        if promo:
            for run in promo:
                lines.append(_fmt_run(run))
        else:
            lines.append("- no recent runs")
        lines.append("\n*Nightly/On-Demand Smoke (latest)*")
        if smoke:
            for run in smoke:
                lines.append(_fmt_run(run))
        else:
            lines.append("- no recent runs")
        return Response("\n".join(lines), media_type="text/plain")

    help_text = (
        "Usage: /ironclad <promote|smoke|status> [KEY=VALUE ...]\n"
        "- promote: trigger promote_and_smoke workflow\n"
        "- smoke PROFILE=<name> [SEASON=<year>] [WEEK=<n>]\n"
        "- status: show latest workflow runs"
    )
    return Response(help_text, media_type="text/plain")
