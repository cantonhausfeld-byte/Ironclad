PY?=python
run:
	IRONCLAD_PROFILE=$(PROFILE) $(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)
lint:
	ruff check src
	black --check src
	mypy src
test:
	pytest -q
format:
	black src tests
ci: format lint test

preslate-size:
	. .venv/bin/activate && IRONCLAD_DEMO=1 python -m ironclad.runner.run_board --season $${SEASON:-2025} --week $${WEEK:-1}
	. .venv/bin/activate && python scripts/analytics/preslate_size.py --season $${SEASON:-2025} --week $${WEEK:-1}

guardrails:
	. .venv/bin/activate && python scripts/analytics/guardrail_check.py --season 2025 --week 1 --sized

ci-guardrails:
	. .venv/bin/activate && python scripts/analytics/guardrail_check.py --season $${SEASON:-2025} --week $${WEEK:-1} --sized --max_total_u $${MAX_TOTAL_U:-25} --max_team_u $${MAX_TEAM_U:-10} --max_market_u $${MAX_MARKET_U:-15} --max_game_u $${MAX_GAME_U:-10}

# Example GitHub Actions step (paste into your workflow if desired):
# - name: Guardrails
#   run: |
#     SEASON=2025 WEEK=1 MAX_TOTAL_U=25 MAX_TEAM_U=10 MAX_MARKET_U=15 MAX_GAME_U=10 make ci-guardrails
