
from ..settings import settings
import json
def main():
    cfg = {
        "profile": settings.profile,
        "duckdb_path": settings.duckdb_path,
        "demo": settings.demo,
        "oddsapi_key": bool(settings.oddsapi_key),
        "sgo_key": bool(settings.sgo_key),
        "weather_key": bool(settings.weather_key),
    }
    print(json.dumps(cfg, indent=2))
if __name__ == "__main__":
    main()
