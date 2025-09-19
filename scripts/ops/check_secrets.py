import os
import sys

REQUIRED = [
    # add/remove as your pipeline needs
    # "ODDSAPI_KEY",
    # "SPORTSGAMEODDS_KEY",
    # "RAPIDAPI_KEY",
    # "SLACK_WEBHOOK",
]

missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    print("WARNING: Missing secrets:", ", ".join(missing))
    sys.exit(1)  # non-zero so CI shows the warning step as not OK
else:
    print("All required secrets present.")
    sys.exit(0)
