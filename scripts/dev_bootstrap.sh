#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p out/picks out/schedules out/analytics out/odds_history out/releases
echo "OK. Run:  make schedule && make preslate"
