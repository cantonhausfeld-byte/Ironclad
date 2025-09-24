import click, duckdb, pandas as pd


@click.command()
@click.option("--duck", default="out/ironclad.duckdb")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--sized/--no-sized", default=True, help="Use picks_sized if True else picks")
@click.option("--out_prefix", default="out/analytics/exposure")
def main(duck, season, week, sized, out_prefix):
    con = duckdb.connect(duck, read_only=True)
    table = "picks_sized" if sized else "picks"
    df = con.execute(f"SELECT * FROM {table} WHERE season=? AND week=?", [season, week]).df()
    if df.empty:
        print("No rows; nothing to export."); return
    df["team_key"] = df["side"].astype(str).str.split(":").str[0]
    # team / market / book summaries
    exp_team = df.groupby("team_key", dropna=False)["stake_units"].sum().sort_values(ascending=False).reset_index()
    exp_mkt  = df.groupby("market", dropna=False)["stake_units"].sum().sort_values(ascending=False).reset_index()
    exp_book = df.groupby("book", dropna=False)["stake_units"].sum().sort_values(ascending=False).reset_index()

    exp_team.to_csv(f"{out_prefix}_team_{season}_W{week}.csv", index=False)
    exp_mkt.to_csv(f"{out_prefix}_market_{season}_W{week}.csv", index=False)
    exp_book.to_csv(f"{out_prefix}_book_{season}_W{week}.csv", index=False)
    print("Wrote:", f"{out_prefix}_team_{season}_W{week}.csv", f"{out_prefix}_market_{season}_W{week}.csv", f"{out_prefix}_book_{season}_W{week}.csv")


if __name__ == "__main__":
    main()
