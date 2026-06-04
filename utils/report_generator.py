"""
Standalone chart+PDF generation for all 4 sections.
No Streamlit dependency — used by automate_email.py.
"""
import logging
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.db import load_all_activities, load_min_date
from utils.helpers import _today_local, apply_base_layout, donut_goal, fmt_duration, fmt_pace
from utils.palette import (
    BLUE_DEPTH,
    CHART_BG,
    CREAM,
    GRAY_SECONDARY,
    GREEN_OUTDOOR,
    HEATMAP_COLORSCALE,
    ORANGE,
    SPORT_COLORS,
    SUNSET,
    SWIM_DARK,
)
from utils.pdf import build_pdf

log = logging.getLogger(__name__)

SWIM_MID     = "#2A6496"
WALK_GOAL_KM = 15.0


def _default_dates() -> tuple:
    return str(load_min_date()), str(date.today())


# ─── Overview ────────────────────────────────────────────────────────────────

def build_overview_report(d_start: str = None, d_end: str = None):
    if not d_start or not d_end:
        d_start, d_end = _default_dates()

    df = load_all_activities(d_start, d_end)
    if df.empty:
        return [], []

    gps_types  = ["Run", "TrailRun", "Swim", "OpenWaterSwim", "Ride", "Walk", "Rowing"]
    total_km   = df[df["sport_type"].isin(gps_types)]["dist_km"].sum()
    total_acts = len(df)
    total_h    = df["duration_h"].sum()
    avg_hr     = df["average_heartrate"].dropna()

    kpis = [
        ("Total Activities",   str(total_acts)),
        ("Kilometers (GPS)",   f"{total_km:,.1f} km"),
        ("Moving Hours",       f"{total_h:,.0f} h"),
        ("Average Heart Rate", f"{avg_hr.mean():.0f} bpm" if not avg_hr.empty else "N/A"),
    ]
    figs = []

    # Top 3 sports
    top3 = (
        df.groupby("sport_type").agg(n=("id", "count"))
        .reset_index().sort_values("n", ascending=False).head(3)
        .sort_values("n", ascending=True)
    )
    if not top3.empty:
        fig_top3 = go.Figure(go.Bar(
            x=top3["n"], y=top3["sport_type"], orientation="h",
            marker_color=[SPORT_COLORS.get(s, GRAY_SECONDARY) for s in top3["sport_type"]],
            text=top3["n"].astype(str) + " sessions", textposition="inside",
            textfont=dict(color="#fff", size=13),
            hovertemplate="%{y}: %{x} sessions<extra></extra>",
        ))
        apply_base_layout(fig_top3, height=200)
        figs.append(("Top 3 Sports", fig_top3))

    # Weekly goals — pair
    week_str = _today_local().strftime("%Y-W%V")
    df_week  = df[df["year_week"] == week_str] if "year_week" in df.columns else pd.DataFrame()
    week_h   = df_week["duration_h"].sum() if not df_week.empty else 0.0
    week_n   = len(df_week) if not df_week.empty else 0
    fig_t = donut_goal(week_h, 5.0, "hours / 5h", color_fill=ORANGE, height=220)
    fig_f = donut_goal(float(week_n), 5.0, "activities / 5", color_fill=SUNSET, height=220)
    figs.append([("Weekly Goal — Time (5h)", fig_t), ("Weekly Goal — Frequency (5 activities)", fig_f)])

    # Activity calendar
    daily = (
        df.groupby("date_only").agg(count=("id", "count"), km=("dist_km", "sum"))
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date_only"])
    idx  = pd.date_range(d_start, d_end, freq="D")
    grid = pd.DataFrame({"date": idx})
    grid["dayofweek"] = grid["date"].dt.dayofweek
    grid["date_only"] = grid["date"].dt.date
    grid = grid.merge(daily[["date_only", "count", "km"]], on="date_only", how="left")
    grid["count"]      = grid["count"].fillna(0)
    grid["week_label"] = grid["date"].dt.strftime("W%V/%g")
    week_order = (
        grid[["week_label", "date"]].groupby("week_label")["date"]
        .min().sort_values().index.tolist()
    )
    grid["week_cat"] = pd.Categorical(grid["week_label"], categories=week_order, ordered=True)
    grid_pivot = grid.pivot_table(
        index="dayofweek", columns="week_cat", values="count", aggfunc="sum"
    ).fillna(0)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    n_weeks   = len(week_order)
    fig_heat  = go.Figure(go.Heatmap(
        z=grid_pivot.values,
        x=list(grid_pivot.columns),
        y=[day_names[i] for i in grid_pivot.index],
        colorscale=HEATMAP_COLORSCALE, showscale=False,
        hovertemplate="Week: %{x}<br>Day: %{y}<br>Sessions: %{z}<extra></extra>",
        xgap=2, ygap=2,
    ))
    fig_heat.update_layout(
        height=220, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        margin=dict(l=40, r=10, t=10, b=30),
        font=dict(color=GRAY_SECONDARY, size=11),
        xaxis=dict(
            tickmode="array",
            tickvals=week_order[::max(1, n_weeks // 8)],
            ticktext=week_order[::max(1, n_weeks // 8)],
            tickangle=-30, gridcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
    )

    # Sport mix — pair with calendar
    mix = (
        df.groupby("sport_type").agg(n=("id", "count"))
        .reset_index().sort_values("n", ascending=False)
    )
    fig_donut = go.Figure(go.Pie(
        labels=mix["sport_type"], values=mix["n"], hole=0.55,
        marker=dict(colors=[SPORT_COLORS.get(s, GRAY_SECONDARY) for s in mix["sport_type"]],
                    line=dict(color="#ffffff", width=2)),
        textinfo="percent", textposition="inside",
        hovertemplate="%{label}: %{value} sessions (%{percent})<extra></extra>",
    ))
    fig_donut.add_annotation(
        text=f"<b>{total_acts}</b><br><span style='font-size:10px'>sessions</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=ORANGE),
    )
    fig_donut.update_layout(
        height=260, showlegend=True,
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor=CHART_BG, margin=dict(l=0, r=0, t=0, b=0),
    )
    figs.append([("Activity Calendar", fig_heat), ("Sport Mix", fig_donut)])

    # Monthly volume by sport
    vol_m = (
        df[df["sport_type"].isin(SPORT_COLORS)]
        .groupby(["month_str", "sport_type"])["duration_min"]
        .sum().reset_index().sort_values("month_str")
    )
    if not vol_m.empty:
        vol_m["text_label"] = vol_m["duration_min"].apply(
            lambda v: fmt_duration(v) if v >= 10 else ""
        )
        fig_bar = px.bar(
            vol_m, x="month_str", y="duration_min", color="sport_type",
            color_discrete_map=SPORT_COLORS, text="text_label",
            labels={"month_str": "", "duration_min": "Minutes", "sport_type": ""},
        )
        fig_bar.update_traces(textposition="inside", textfont_size=9)
        fig_bar.update_xaxes(categoryorder="category ascending", tickangle=-30)
        apply_base_layout(fig_bar, height=340)
        figs.append(("Monthly Volume by Sport (min)", fig_bar))

    return kpis, figs


# ─── Running ──────────────────────────────────────────────────────────────────

def build_running_report(d_start: str = None, d_end: str = None):
    if not d_start or not d_end:
        d_start, d_end = _default_dates()

    df_all = load_all_activities(d_start, d_end)
    df_run = df_all[df_all["sport_type"].isin(["Run", "TrailRun", "VirtualRun"])].copy()
    df_run = df_run[df_run["pace_min_km"].between(3.0, 20.0)]

    if df_run.empty:
        return [], []

    df_5k  = df_run[df_run["distance"].between(4900, 5500)].copy()
    df_10k = df_run[df_run["distance"].between(9800, 10500)].copy()

    pr_5k  = df_5k["pace_min_km"].min()  if not df_5k.empty  else None
    avg_5k = df_5k["pace_min_km"].mean() if not df_5k.empty  else None
    pr_10k = df_10k["pace_min_km"].min() if not df_10k.empty else None
    hr_run = df_run["average_heartrate"].dropna()

    kpis = [
        ("PR — 5 km",         fmt_pace(pr_5k)),
        ("Average Pace 5 km", fmt_pace(avg_5k)),
        ("PR — 10 km",        fmt_pace(pr_10k)),
        ("Total Volume",      f"{df_run['dist_km'].sum():,.1f} km"),
        ("Average HR",        f"{hr_run.mean():.0f} bpm" if not hr_run.empty else "N/A"),
    ]
    figs = []

    # Weekly goal
    week_str = _today_local().strftime("%Y-W%V")
    df_week  = df_run[df_run["year_week"] == week_str] if "year_week" in df_run.columns else pd.DataFrame()
    week_km  = df_week["dist_km"].sum() if not df_week.empty else 0.0
    figs.append(("Weekly Running Goal (5 km)", donut_goal(week_km, 5.0, "km / 5km", color_fill=SUNSET, height=240)))

    # Pace evolution
    fig_pace = go.Figure()
    for df_seg, label, color in [(df_5k, "5 km", ORANGE), (df_10k, "10 km", BLUE_DEPTH)]:
        if df_seg.empty:
            continue
        ds = df_seg.sort_values("start_date_local")
        fig_pace.add_trace(go.Scatter(
            x=ds["start_date_local"], y=ds["pace_min_km"],
            mode="markers+lines", name=label,
            line=dict(color=color, width=1.5), marker=dict(size=7, color=color),
            text=ds["pace_min_km"].apply(fmt_pace), textposition="top center",
            textfont=dict(size=8),
            hovertemplate=f"<b>{label}</b><br>%{{x|%b %d, %Y}}<br>%{{text}}/km<extra></extra>",
        ))
        if len(ds) >= 3:
            x_num = np.arange(len(ds))
            z = np.polyfit(x_num, ds["pace_min_km"].values, 1)
            fig_pace.add_trace(go.Scatter(
                x=ds["start_date_local"], y=np.poly1d(z)(x_num),
                mode="lines", line=dict(color=color, width=1, dash="dot"), showlegend=False,
            ))
    fig_pace.update_yaxes(autorange="reversed", tickformat=".2f", title_text="Pace (min/km)")
    apply_base_layout(fig_pace, height=360, title="Pace per Session (5 km and 10 km)")
    figs.append(("Pace Evolution — 5 km and 10 km", fig_pace))

    # Monthly volume
    vol_r = df_run.groupby("month_str")["dist_km"].sum().reset_index().sort_values("dist_km", ascending=False)
    if not vol_r.empty:
        fig_vol = go.Figure(go.Bar(
            x=vol_r["month_str"], y=vol_r["dist_km"], marker_color=ORANGE,
            text=vol_r["dist_km"].apply(lambda v: f"{v:.1f}"),
            textposition="inside", textfont=dict(color="#fff", size=10),
            hovertemplate="Month: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
        ))
        fig_vol.update_xaxes(tickangle=-30, categoryorder="total descending")
        fig_vol.update_yaxes(title_text="km")
        apply_base_layout(fig_vol, height=300, title="Running km by Month")
        figs.append(("Monthly Training Volume (km)", fig_vol))

    # Pace by distance
    fig_scat = go.Figure(go.Scatter(
        x=df_run["dist_km"], y=df_run["pace_min_km"], mode="markers",
        marker=dict(size=9, color=ORANGE, opacity=0.65, line=dict(color=CREAM, width=1)),
        text=df_run["start_date_local"].dt.strftime("%b %d, %Y"),
        hovertemplate="Date: %{text}<br>Dist: %{x:.1f} km<br>Pace: %{customdata}/km<extra></extra>",
        customdata=df_run["pace_min_km"].apply(fmt_pace),
    ))
    avg_pace = df_run["pace_min_km"].mean()
    fig_scat.add_hline(
        y=avg_pace, line_dash="dash", line_color=BLUE_DEPTH,
        annotation_text=f"Avg: {fmt_pace(avg_pace)}/km",
        annotation_position="top right",
        annotation_font=dict(size=9, color=BLUE_DEPTH),
    )
    fig_scat.update_yaxes(autorange="reversed", title_text="Pace (min/km)", tickformat=".2f")
    fig_scat.update_xaxes(title_text="Distance (km)")
    fig_scat.update_layout(
        height=320, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=30),
    )
    figs.append(("Pace by Distance", fig_scat))

    # HR zones
    df_hr = df_run.dropna(subset=["average_heartrate"]).copy()
    if not df_hr.empty:
        FC_MAX   = 195
        bins     = [0, 0.60*FC_MAX, 0.70*FC_MAX, 0.80*FC_MAX, 0.90*FC_MAX, FC_MAX+50]
        labels_z = ["Z1 — Recovery", "Z2 — Aerobic Base", "Z3 — Tempo", "Z4 — Threshold", "Z5 — VO2max"]
        colors_z = ["#4CAF50", "#8BC34A", ORANGE, "#FF5722", "#B71C1C"]
        df_hr["zone"] = pd.cut(df_hr["average_heartrate"], bins=bins, labels=labels_z)
        zone_cts = df_hr["zone"].value_counts().reindex(labels_z).fillna(0).reset_index()
        zone_cts.columns = ["zone", "count"]
        fig_zones = go.Figure(go.Bar(
            x=zone_cts["count"], y=zone_cts["zone"], orientation="h",
            marker_color=colors_z,
            text=zone_cts["count"].astype(int),
            textposition="inside", textfont=dict(color="#fff", size=11),
            hovertemplate="%{y}: %{x} sessions<extra></extra>",
        ))
        fig_zones.update_xaxes(title_text="Sessions")
        fig_zones.update_yaxes(autorange="reversed")
        apply_base_layout(fig_zones, height=300, title=f"HR Zones (max HR ref: {FC_MAX} bpm)")
        figs.append(("Heart Rate Zone Distribution", fig_zones))

    # Monthly 5k pace
    if not df_5k.empty:
        m5k = (
            df_5k.groupby("month_str")["pace_min_km"]
            .agg(pr="min", avg="mean", worst="max")
            .reset_index().sort_values("month_str")
        )
        fig_m5k = go.Figure()
        fig_m5k.add_trace(go.Scatter(
            x=m5k["month_str"], y=m5k["worst"], mode="lines",
            line=dict(width=0), showlegend=False,
        ))
        fig_m5k.add_trace(go.Scatter(
            x=m5k["month_str"], y=m5k["pr"], fill="tonexty",
            fillcolor="rgba(252,76,2,0.12)", mode="lines+markers+text",
            line=dict(color=ORANGE, width=2), marker=dict(symbol="star", size=10, color=ORANGE),
            name="Monthly PR", text=m5k["pr"].apply(fmt_pace),
            textposition="bottom center", textfont=dict(size=9),
            hovertemplate="Month: %{x}<br>PR: %{text}/km<extra></extra>",
        ))
        fig_m5k.add_trace(go.Scatter(
            x=m5k["month_str"], y=m5k["avg"], mode="lines+markers",
            line=dict(color=SUNSET, width=1.5, dash="dash"), marker=dict(size=5),
            name="Monthly Average", text=m5k["avg"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=8),
            hovertemplate="Month: %{x}<br>Average: %{text}/km<extra></extra>",
        ))
        fig_m5k.update_yaxes(autorange="reversed", title_text="Pace (min/km)", tickformat=".2f")
        apply_base_layout(fig_m5k, height=320)
        figs.append(("Monthly Pace Evolution — 5 km", fig_m5k))

    return kpis, figs


# ─── Swimming ─────────────────────────────────────────────────────────────────

def build_swimming_report(d_start: str = None, d_end: str = None):
    if not d_start or not d_end:
        d_start, d_end = _default_dates()

    df_all = load_all_activities(d_start, d_end)
    df     = df_all[df_all["sport_type"].isin(["Swim", "OpenWaterSwim"])].copy()

    if not df.empty:
        df["pace_100m"] = np.where(
            (df["distance"] > 0) & (df["moving_time"] > 0),
            (df["moving_time"] / 60) / (df["distance"] / 100),
            np.nan,
        )
        df = df[df["pace_100m"].between(0.8, 10.0)]

    if df.empty:
        return [], []

    df_1k = df[df["distance"].between(900, 1100)]
    df_2k = df[df["distance"].between(1900, 2100)]

    pr_1k  = df_1k["pace_100m"].min()  if not df_1k.empty else None
    avg_1k = df_1k["pace_100m"].mean() if not df_1k.empty else None
    pr_2k  = df_2k["pace_100m"].min()  if not df_2k.empty else None

    kpis = [
        ("PR Pace 1 km",      (fmt_pace(pr_1k)  + "/100m") if pr_1k  else "N/A"),
        ("Average Pace 1 km", (fmt_pace(avg_1k) + "/100m") if avg_1k else "N/A"),
        ("PR Pace 2 km",      (fmt_pace(pr_2k)  + "/100m") if pr_2k  else "N/A"),
        ("Total Volume",      f"{df['dist_km'].sum():,.1f} km"),
    ]
    figs = []

    # Weekly goal
    week_str = _today_local().strftime("%Y-W%V")
    df_week  = df[df["year_week"] == week_str] if "year_week" in df.columns else pd.DataFrame()
    week_km  = df_week["dist_km"].sum() if not df_week.empty else 0.0
    figs.append(("Weekly Swimming Goal (2 km)", donut_goal(week_km, 2.0, "km / 2km", color_fill=SWIM_DARK, height=240)))

    # Volume + pace evolution
    swim_m = (
        df.groupby("month_str")
        .agg(dist_km=("dist_km", "sum"), pace_med=("pace_100m", "mean"), n=("id", "count"))
        .reset_index().sort_values("month_str")
    )
    fig_ev = go.Figure()
    fig_ev.add_trace(go.Bar(
        x=swim_m["month_str"], y=swim_m["dist_km"], name="Volume (km)",
        marker_color=SWIM_DARK, opacity=0.85,
        text=swim_m["dist_km"].apply(lambda v: f"{v:.1f}"),
        textposition="inside", textfont=dict(color="#fff", size=10),
        hovertemplate="Month: %{x}<br>Volume: %{y:.2f} km<extra></extra>",
        yaxis="y",
    ))
    fig_ev.add_trace(go.Scatter(
        x=swim_m["month_str"], y=swim_m["pace_med"], name="Average Pace /100m",
        mode="lines+markers+text",
        line=dict(color=ORANGE, width=2.5), marker=dict(size=8, color=ORANGE),
        text=swim_m["pace_med"].apply(fmt_pace),
        textposition="top center", textfont=dict(size=9, color=ORANGE),
        hovertemplate="Month: %{x}<br>Pace: %{text}/100m<extra></extra>",
        yaxis="y2",
    ))
    fig_ev.update_layout(
        yaxis=dict(title="Volume (km)", gridcolor="rgba(26,46,64,0.12)", color=SWIM_DARK),
        yaxis2=dict(title="Pace (min/100m)", overlaying="y", side="right",
                    autorange="reversed", gridcolor="rgba(0,0,0,0)", color=ORANGE),
        xaxis=dict(tickangle=-30, categoryorder="category ascending"),
        height=360, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=GRAY_SECONDARY, family="sans-serif"),
        margin=dict(l=10, r=10, t=68, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        title=dict(text="Monthly Volume vs. Average Pace", font=dict(size=13, color=SWIM_DARK), x=0),
    )
    figs.append(("Volume vs. Average Pace Evolution", fig_ev))

    # Session frequency + pace by distance — pair
    fig_freq = go.Figure(go.Bar(
        x=swim_m["month_str"], y=swim_m["n"],
        marker_color=SWIM_DARK, text=swim_m["n"], textposition="inside",
        textfont=dict(color="#fff", size=11),
        hovertemplate="Month: %{x}<br>Sessions: %{y}<extra></extra>",
    ))
    avg_n = swim_m["n"].mean()
    fig_freq.add_hline(
        y=avg_n, line_dash="dot", line_color=ORANGE,
        annotation_text=f"Average: {avg_n:.1f}/month",
        annotation_position="top right",
        annotation_font=dict(size=10, color=ORANGE),
    )
    fig_freq.update_xaxes(tickangle=-30, categoryorder="category ascending")
    fig_freq.update_yaxes(title_text="Sessions")
    fig_freq.update_layout(
        height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=30),
    )

    fig_scat = go.Figure(go.Scatter(
        x=df["dist_km"]*1000, y=df["pace_100m"], mode="markers+text",
        marker=dict(size=10, color=SWIM_MID, opacity=0.75, line=dict(color=SWIM_DARK, width=1)),
        text=df["pace_100m"].apply(fmt_pace),
        textposition="top center", textfont=dict(size=7, color=SWIM_DARK),
        hovertemplate="Dist: %{x:.0f} m<br>Pace: %{text}/100m<extra></extra>",
    ))
    fig_scat.add_hline(
        y=2.0, line_dash="dash", line_color=ORANGE,
        annotation_text="Ref: 2:00/100m", annotation_position="bottom right",
        annotation_font=dict(size=9, color=ORANGE),
    )
    fig_scat.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
    fig_scat.update_xaxes(title_text="Distance (m)")
    fig_scat.update_layout(
        height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=30),
    )
    figs.append([("Pool Session Frequency", fig_freq), ("Pace by Distance Swum", fig_scat)])

    # Pace evolution ~1k sessions
    if not df_1k.empty:
        ds = df_1k.sort_values("start_date_local")
        fig_1k = go.Figure()
        if len(ds) >= 3:
            x_num = np.arange(len(ds))
            z = np.polyfit(x_num, ds["pace_100m"].values, 1)
            fig_1k.add_trace(go.Scatter(
                x=ds["start_date_local"], y=np.poly1d(z)(x_num),
                mode="lines", name="Trend",
                line=dict(color=ORANGE, width=1.5, dash="dot"),
            ))
        fig_1k.add_trace(go.Scatter(
            x=ds["start_date_local"], y=ds["pace_100m"],
            mode="markers+lines", name="Actual Pace",
            line=dict(color=SWIM_DARK, width=1.5),
            marker=dict(size=8, color=SWIM_DARK, line=dict(color=ORANGE, width=1.5)),
            text=ds["pace_100m"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=8, color=SWIM_DARK),
            hovertemplate="%{x|%b %d, %Y}<br>Pace: %{text}/100m<extra></extra>",
        ))
        fig_1k.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
        fig_1k.update_layout(
            height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig_1k.update_xaxes(gridcolor="rgba(26,46,64,0.12)")
        fig_1k.update_yaxes(gridcolor="rgba(26,46,64,0.12)")
        figs.append(("Pace Evolution — ~1000m Sessions", fig_1k))

    return kpis, figs


# ─── Walking ──────────────────────────────────────────────────────────────────

def build_walking_report(d_start: str = None, d_end: str = None):
    if not d_start or not d_end:
        d_start, d_end = _default_dates()

    df_all = load_all_activities(d_start, d_end)
    df     = df_all[df_all["sport_type"].isin(["Walk", "Hike"])].copy()

    if df.empty:
        return [], []

    elev = df["total_elevation_gain"].dropna().sum()
    kpis = [
        ("Total Outings",  str(len(df))),
        ("Total Distance", f"{df['dist_km'].sum():,.1f} km"),
        ("Hours Walking",  f"{df['duration_h'].sum():,.0f} h"),
        ("Elevation Gain", f"{elev:,.0f} m"),
    ]
    figs = []

    # Weekly goal
    week_str = _today_local().strftime("%Y-W%V")
    df_week  = df[df["year_week"] == week_str] if "year_week" in df.columns else pd.DataFrame()
    week_km  = df_week["dist_km"].sum() if not df_week.empty else 0.0
    figs.append((
        f"Weekly Walking Goal ({WALK_GOAL_KM:.0f} km)",
        donut_goal(week_km, WALK_GOAL_KM, f"km / {WALK_GOAL_KM:.0f}km", color_fill=GREEN_OUTDOOR, height=240),
    ))

    # Monthly volume
    vol_w = df.groupby("month_str")["dist_km"].sum().reset_index().sort_values("dist_km", ascending=False)
    if not vol_w.empty:
        fig_vol = go.Figure(go.Bar(
            x=vol_w["month_str"], y=vol_w["dist_km"], marker_color=GREEN_OUTDOOR,
            text=vol_w["dist_km"].apply(lambda v: f"{v:.1f} km"),
            textposition="inside", textfont=dict(color="#fff", size=10),
            hovertemplate="Month: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
        ))
        fig_vol.update_xaxes(tickangle=-30, categoryorder="total descending")
        fig_vol.update_yaxes(title_text="km")
        apply_base_layout(fig_vol, height=320, title="Walking km by Month", title_color=GREEN_OUTDOOR)
        figs.append(("Monthly Walking Volume (km)", fig_vol))

    return kpis, figs


# ─── Master generator ─────────────────────────────────────────────────────────

_SECTIONS = [
    ("overview",  "Performance Overview",  build_overview_report,  "#FC4C02"),
    ("running",   "Running Performance",   build_running_report,   "#FC4C02"),
    ("swimming",  "Swimming Performance",  build_swimming_report,  "#1A2E40"),
    ("walking",   "Walking Performance",   build_walking_report,   "#3B6E4C"),
]


def generate_all_pdfs(d_start: str = None, d_end: str = None) -> dict:
    """
    Build all 4 section PDFs. Returns:
        { section_key: (pdf_bytes, filename), ... }
    Only includes sections that have data.
    """
    if not d_start or not d_end:
        d_start, d_end = _default_dates()

    results = {}
    for key, title, builder, accent in _SECTIONS:
        try:
            kpis, figs = builder(d_start, d_end)
            if kpis or figs:
                pdf_bytes = build_pdf(title, d_start, d_end, kpis, fig_sections=figs, accent_hex=accent)
                results[key] = (pdf_bytes, f"{key}_{d_start}_{d_end}.pdf")
                log.info("Generated PDF: %s (%d KPIs, %d chart entries)", key, len(kpis), len(figs))
        except Exception as exc:
            log.error("Failed to generate %s PDF: %s", key, exc, exc_info=True)

    return results
