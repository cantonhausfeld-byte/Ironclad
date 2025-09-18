import argparse, csv, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_csv", type=pathlib.Path, required=True)
    args = ap.parse_args()
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["game_id", "market", "price_american"])
    print(f"Wrote placeholder closers to {args.out_csv}")

if __name__ == "__main__":
    main()
