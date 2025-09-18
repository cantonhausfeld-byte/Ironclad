import logging, json, os, sys, time, pathlib, structlog
from logging import handlers

LOG_DIR = pathlib.Path("out/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "app.jsonl"

def _json_serializer(_, __, event_dict):
    return json.dumps(event_dict, separators=(",", ":"))

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console (human-ish)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    root.addHandler(console)

    # File (JSON lines)
    fileh = handlers.RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=5)
    fileh.setLevel(logging.INFO)
    root.addHandler(fileh)

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _json_serializer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()

# ---------- end logging ----------
