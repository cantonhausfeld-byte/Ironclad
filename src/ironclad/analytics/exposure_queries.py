from __future__ import annotations
import duckdb
import pandas as pd
from pathlib import Path


def _connect(duck_path: str):
    Path(duck_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(duck_path, read_only=True)


def seasons_weeks(duck_path: str) -> pd.DataFrame:
    con = _connect(duck_path)
    q = """
    WITH base AS (
      SELECT season, week FROM picks
      UNION ALL
      SELECT season, week FROM picks_sized
    )
    SELECT season, week
    FROM base
    WHERE season IS NOT NULL AND week IS NOT NULL
    GROUP BY season, week
    ORDER BY season DESC, week DESC
    """
    return con.execute(q).df()


def board(duck_path: str, season: int | None = None, week: int | None = None, sized: bool = True) -> pd.DataFrame:
    con = _connect(duck_path)
    table = "picks_sized" if sized else "picks"
    q = f"""
    SELECT
      run_id, season, week, game_id, market, side, line, price_american,
      model_prob, ev_percent, grade, book,
      kelly_fraction, stake_units, ts_created
    FROM {table}
    """
    if season is not None and week is not None:
        q += " WHERE season = ? AND week = ?"
        return con.execute(q, [season, week]).df()
    return con.execute(q).df()


def exposure_by_team(duck_path: str, season: int | None, week: int | None, sized: bool = True) -> pd.DataFrame:
    df = board(duck_path, season, week, sized)
    if df.empty:
        return df
    df["team_key"] = df["side"].astype(str).str.split(":").str[0]
    out = (
        df.groupby("team_key", dropna=False)["stake_units"]
          .sum()
          .sort_values(ascending=False)
          .reset_index()
    )
    return out


def exposure_by_market(duck_path: str, season: int | None, week: int | None, sized: bool = True) -> pd.DataFrame:
    df = board(duck_path, season, week, sized)
    if df.empty:
        return df
    out = (
        df.groupby("market", dropna=False)["stake_units"]
          .sum()
          .sort_values(ascending=False)
          .reset_index()
    )
    return out


def exposure_by_book(duck_path: str, season: int | None, week: int | None, sized: bool = True) -> pd.DataFrame:
    df = board(duck_path, season, week, sized)
    if df.empty:
        return df
    out = (
        df.groupby("book", dropna=False)["stake_units"]
          .sum()
          .sort_values(ascending=False)
          .reset_index()
    )
    return out


def top_picks(duck_path: str, season: int | None, week: int | None, sized: bool = True, k:int=20) -> pd.DataFrame:
    df = board(duck_path, season, week, sized)
    if df.empty:
        return df
    return df.sort_values("stake_units", ascending=False).head(k).reset_index(drop=True)
