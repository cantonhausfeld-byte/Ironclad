import os, shutil, datetime, pathlib, sys, json
from ironclad.settings import get_settings

def main():
    s = get_settings()
    src = pathlib.Path(s.DUCKDB__PATH)
    if not src.exists():
        print(json.dumps({"ok": False, "msg": f"no db at {src}"}))
        sys.exit(0)
    backups = pathlib.Path("out/backups"); backups.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    dst = backups / f"ironclad-{ts}.duckdb"
    shutil.copy2(src, dst)
    print(json.dumps({"ok": True, "src": str(src), "dst": str(dst)}))

if __name__ == "__main__":
    main()
