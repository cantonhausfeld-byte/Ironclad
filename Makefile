
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

ui:
	. .venv/bin/activate && streamlit run streamlit_app.py

sheets:
	. .venv/bin/activate && python scripts/export/to_sheets.py --csv_out out/picks/picks_latest.csv

sheets-push:
	. .venv/bin/activate && python scripts/export/to_sheets.py --sheet "Ironclad Picks" --csv_out out/picks/picks_latest.csv
