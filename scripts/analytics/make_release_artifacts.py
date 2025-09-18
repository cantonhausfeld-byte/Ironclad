import argparse, json, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default="auto")
    ap.add_argument("--outdir", type=pathlib.Path, default=pathlib.Path("out/releases"))
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"week": args.week, "artifacts": []}
    (args.outdir / "release_manifest.json").write_text(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
