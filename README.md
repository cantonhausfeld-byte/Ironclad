
# Ironclad v2.1 Foundation (Phase 1)
Foundation hotfixes:
- Canonical schemas (Pydantic) for Picks/Game/Odds/RunManifest
- Single config (pydantic-settings) with strict validation
- Typed service clients + explicit ServiceState (no silent failures)
- Minimal DuckDB persistence (runs, picks)
- `src/` repo layout, linting, typing
- CI (GitHub Actions), unit/integration/smoke tests
- Minimal Streamlit Picks page with error banners

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
cp .env.example .env
python -m ironclad.runner.config_doctor
make run PROFILE=local SEASON=2025 WEEK=1
```
