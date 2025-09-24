import json
import os
import sys
import time

import click
import pandas as pd


def _load_picks_csv() -> pd.DataFrame:
    path = "out/picks"
    if not os.path.isdir(path):
        return pd.DataFrame()

    files = sorted(f for f in os.listdir(path) if f.endswith("_picks.csv"))
    if not files:
        return pd.DataFrame()

    return pd.concat(
        [pd.read_csv(os.path.join(path, filename)) for filename in files],
        ignore_index=True,
    )


@click.command()
@click.option("--sheet", required=False, help="Google Sheet name (tab will be 'Picks').")
@click.option(
    "--creds_json",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    help="Path to service-account JSON.",
)
@click.option("--csv_out", default="out/picks/picks_latest.csv", help="Always writes CSV here.")
def main(sheet: str | None, creds_json: str | None, csv_out: str):
    started = time.time()
    df = _load_picks_csv()
    os.makedirs(os.path.dirname(csv_out), exist_ok=True)
    df.to_csv(csv_out, index=False)
    duration = time.time() - started
    print(f"Wrote CSV: {csv_out} (rows={len(df)}) in {duration:.2f}s")

    if not sheet:
        print("No --sheet provided → skipping Google Sheets.")
        return
    if not creds_json or not os.path.exists(creds_json):
        print("No Google creds JSON → skipping Google Sheets.")
        return

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(creds_json, scopes=scopes)
        gc = gspread.authorize(creds)
        try:
            sh = gc.open(sheet)
        except gspread.SpreadsheetNotFound:
            sh = gc.create(sheet)
        try:
            ws = sh.worksheet("Picks")
            sh.del_worksheet(ws)
        except Exception:
            pass
        ws = sh.add_worksheet(title="Picks", rows=str(max(1000, len(df)+10)), cols="30")
        if df.empty:
            ws.update("A1", [["No picks"]])
            print("Sheet updated (empty).")
            return
        ws.update([df.columns.tolist()] + df.astype(str).values.tolist())
        print(f"Sheet '{sheet}' → tab 'Picks' updated. Rows={len(df)}")
        print(
            "Sheet update metadata:",
            json.dumps({"sheet": sheet, "tab": "Picks", "rows": len(df)}),
        )
    except Exception as e:
        print("Sheets export failed, but CSV is written. Error:", e, file=sys.stderr)


if __name__ == "__main__":
    main()
