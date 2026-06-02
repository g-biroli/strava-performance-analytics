import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DB_PATH = Path("data/strava.db")


@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    df["dist_km"]      = df["distance"] / 1000
    df["duration_min"] = df["moving_time"] / 60
    df["duration_h"]   = df["moving_time"] / 3600
    df["speed_kmh"]    = np.where(
        df["moving_time"] > 0, df["distance"] / df["moving_time"] * 3.6, np.nan
    )
    df["pace_min_km"] = np.where(
        (df["dist_km"] > 0) & (df["moving_time"] > 0),
        df["duration_min"] / df["dist_km"],
        np.nan,
    )
    df["month_str"] = df["start_date_local"].dt.to_period("M").astype(str)
    df["week"]      = df["start_date_local"].dt.isocalendar().week.astype(int)
    df["dayofweek"] = df["start_date_local"].dt.dayofweek
    df["date_only"] = df["start_date_local"].dt.date
    df["year_week"] = df["start_date_local"].dt.strftime("%Y-W%V")
    return df


@st.cache_data(ttl=300)
def load_all_activities(date_start: str, date_end: str) -> pd.DataFrame:
    conn = get_conn()
    q = """
        SELECT id, name, sport_type, start_date_local,
               distance, moving_time, elapsed_time,
               total_elevation_gain, average_heartrate, max_heartrate,
               average_speed, average_cadence, average_watts,
               achievement_count, pr_count, calories,
               start_latlng, end_latlng
        FROM activities
        WHERE start_date_local >= ? AND start_date_local <= ?
        ORDER BY start_date_local
    """
    df = pd.read_sql(q, conn, params=[date_start, date_end + "T23:59:59"])
    return _enrich(df)


@st.cache_data(ttl=300)
def load_athlete() -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT firstname, lastname, city, country, profile_medium, weight FROM athlete LIMIT 1"
    ).fetchone()
    if row:
        return dict(zip(["firstname", "lastname", "city", "country", "profile", "weight"], row))
    return {}
