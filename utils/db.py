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
    # Parse as UTC then strip timezone → timezone-naive local datetime
    # Required: Plotly 5.22 fails to serialize tz-aware datetime64[us,UTC] to JS
    df["start_date_local"] = (
        pd.to_datetime(df["start_date_local"], utc=True).dt.tz_localize(None)
    )
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


@st.cache_data(ttl=300)
def load_min_date() -> str:
    """Returns the earliest activity date as 'YYYY-MM-DD'."""
    conn = get_conn()
    row = conn.execute("SELECT DATE(MIN(start_date_local)) FROM activities").fetchone()
    return row[0] if (row and row[0]) else "2020-01-01"


@st.cache_data(ttl=300)
def load_activity_coords(sport_types: tuple, date_start: str, date_end: str) -> pd.DataFrame:
    """Returns DataFrame with lat/lon parsed from start_latlng for map visualization."""
    import json as _json
    conn = get_conn()
    placeholders = ",".join("?" * len(sport_types))
    q = f"""
        SELECT sport_type, name, start_latlng
        FROM activities
        WHERE sport_type IN ({placeholders})
          AND start_date_local >= ? AND start_date_local <= ?
          AND start_latlng IS NOT NULL AND start_latlng != ''
    """
    df = pd.read_sql(q, conn, params=[*sport_types, date_start, date_end + "T23:59:59"])
    if df.empty:
        return pd.DataFrame(columns=["lat", "lon", "sport_type", "name"])

    def _parse(s):
        try:
            c = _json.loads(s)
            if isinstance(c, (list, tuple)) and len(c) >= 2:
                return float(c[0]), float(c[1])
        except Exception:
            pass
        try:
            s = s.strip().strip("[]")
            p = s.split(",")
            if len(p) >= 2:
                return float(p[0].strip()), float(p[1].strip())
        except Exception:
            pass
        return None, None

    parsed = df["start_latlng"].apply(_parse)
    df["lat"] = parsed.apply(lambda x: x[0])
    df["lon"] = parsed.apply(lambda x: x[1])
    df = df.dropna(subset=["lat", "lon"])
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]
    return df[["lat", "lon", "sport_type", "name"]]
