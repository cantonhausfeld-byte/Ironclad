import pathlib

import click
import duckdb

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS picks_sized(
    run_id TEXT,
    season INTEGER,
    week INTEGER,
    game_id TEXT,
    market TEXT,
    side TEXT,
    line DOUBLE,
    price_american INTEGER,
    model_prob DOUBLE,
    ev_percent DOUBLE,
    grade TEXT,
    book TEXT,
    kelly_fraction DOUBLE,
    stake_units DOUBLE,
    ts_created TIMESTAMP
)
"""


@click.command()
@click.option("--duck", default="out/ironclad.duckdb")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--kelly-multiplier", default=100.0, show_default=True)
def main(duck: str, season: int, week: int, kelly_multiplier: float) -> None:
    db_path = pathlib.Path(duck)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(SCHEMA_SQL)
    con.execute("DELETE FROM picks_sized WHERE season=? AND week=?", [season, week])
    con.execute(
        """
        INSERT INTO picks_sized
        SELECT
            run_id,
            season,
            week,
            game_id,
            market,
            side,
            line,
            price_american,
            model_prob,
            ev_percent,
            grade,
            book,
            kelly_fraction,
            ROUND(GREATEST(COALESCE(stake_units, 0), kelly_fraction * ?), 4) AS stake_units,
            ts_created
        FROM picks
        WHERE season = ? AND week = ?
        """,
        [kelly_multiplier, season, week],
    )
    con.close()


if __name__ == "__main__":
    main()
