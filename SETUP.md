
# Setup & Profiles
Env precedence: env vars > .env > defaults.

Minimal vars:
```
IRONCLAD_PROFILE=local
DUCKDB_PATH=./data/ironclad.duckdb
IRONCLAD_DEMO=1
ODDSAPI__KEY=
SPORTSGAMEODDS__KEY=
WEATHER__KEY=
```

Run:
```
make run PROFILE=local SEASON=2025 WEEK=1
```
