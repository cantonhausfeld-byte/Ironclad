import duckdb, pandas as pd, click, yaml, sys

def _load(con, run_id):
    q = """
    SELECT run_id, season, week, game_id, market, side, line, book,
           price_american, grade, stake_units
    FROM picks WHERE run_id = ?
    """
    return con.execute(q, [run_id]).df()

def _grade_mix(df):
    if df.empty: return {}
    g = df["grade"].astype(str).value_counts(normalize=True).to_dict()
    for k in ["A","B","C","NO_PICK","nan","None"]:
        g.setdefault(k, 0.0)
    return g

def _sum_by(df, cols):
    return df.groupby(cols, dropna=False)["stake_units"].sum().reset_index()

@click.command()
@click.option("--duck", default="out/ironclad.duckdb", show_default=True)
@click.option("--a", "run_a", required=True)
@click.option("--b", "run_b", required=True)
@click.option("--policy", default="config/guardrails.yaml", show_default=True)
def main(duck, run_a, run_b, policy):
    with open(policy, "r") as f:
        cfg = yaml.safe_load(f)

    con = duckdb.connect(duck, read_only=True)
    A = _load(con, run_a)
    B = _load(con, run_b)

    # Basic
    if cfg.get("require_non_empty", True) and B.empty:
        print("FAIL: challenger has no picks"); sys.exit(2)

    # Totals
    totA = A["stake_units"].fillna(0).sum()
    totB = B["stake_units"].fillna(0).sum()

    # Hard caps (B-alone)
    if totB > cfg["max_total_units"]:
        print(f"FAIL: total units {totB:.2f} > cap {cfg['max_total_units']}"); sys.exit(2)

    by_game = _sum_by(B, ["game_id"])
    if (by_game["stake_units"] > cfg["max_units_per_game"]).any():
        row = by_game.sort_values("stake_units", ascending=False).iloc[0]
        print(f"FAIL: game {row['game_id']} units {row['stake_units']:.2f} > per-game cap {cfg['max_units_per_game']}"); sys.exit(2)

    by_mkt = _sum_by(B, ["market"])
    if (by_mkt["stake_units"] > cfg["max_units_per_market"]).any():
        row = by_mkt.sort_values("stake_units", ascending=False).iloc[0]
        print(f"FAIL: market {row['market']} units {row['stake_units']:.2f} > cap {cfg['max_units_per_market']}"); sys.exit(2)

    by_side = _sum_by(B, ["market","side"])
    if (by_side["stake_units"] > cfg["max_units_per_side"]).any():
        row = by_side.sort_values("stake_units", ascending=False).iloc[0]
        print(f"FAIL: {row['market']}:{row['side']} units {row['stake_units']:.2f} > cap {cfg['max_units_per_side']}"); sys.exit(2)

    # Relative deltas
    inc_units = max(0.0, totB - totA)
    if inc_units > cfg["max_exposure_increase_units"]:
        print(f"FAIL: exposure increase {inc_units:.2f}u > {cfg['max_exposure_increase_units']}u"); sys.exit(2)
    if totA > 0 and (inc_units / totA) > cfg["max_exposure_increase_pct"]:
        print(f"FAIL: exposure increase ratio {(inc_units/totA):.2%} > {cfg['max_exposure_increase_pct']:.0%}"); sys.exit(2)

    # Grade mix
    mixB = _grade_mix(B)
    for grade, lim in cfg.get("grade_caps", {}).items():
        share = mixB.get(grade, 0.0)
        if "min" in lim and share < lim["min"]:
            print(f"FAIL: grade {grade} share {share:.1%} < min {lim['min']:.0%}"); sys.exit(2)
        if "max" in lim and share > lim["max"]:
            print(f"FAIL: grade {grade} share {share:.1%} > max {lim['max']:.0%}"); sys.exit(2)

    # Price sanity
    if ((B["price_american"] < cfg["min_abs_price"]) | (B["price_american"] > cfg["max_abs_price"])).any():
        print("FAIL: price outside sanity bounds"); sys.exit(2)

    print("PASS: guardrails satisfied")
    print(f"Total units A={totA:.2f}, B={totB:.2f}, Δ={inc_units:.2f}u")
    sys.exit(0)

if __name__ == "__main__":
    main()
