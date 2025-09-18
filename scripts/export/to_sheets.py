import argparse, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="")
    ap.add_argument("--csv_out", type=pathlib.Path, required=True)
    args = ap.parse_args()
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.write_text("game_id,market\n")
    if args.sheet:
        print(f"Would push to sheet {args.sheet} with data {args.csv_out}")
    else:
        print(f"Wrote CSV export to {args.csv_out}")

if __name__ == "__main__":
    main()
