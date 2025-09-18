import argparse, json, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--closers", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("out/analytics/clv_summary.json"))
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"closers": str(args.closers), "summary": []}, indent=2))

if __name__ == "__main__":
    main()
