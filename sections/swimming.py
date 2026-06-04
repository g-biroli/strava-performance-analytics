import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.db import load_all_activities
from utils.helpers import (
    _pdf_download_button,
    _today_local,
    apply_base_layout,
    date_filter_with_download,
    donut_goal,
    fmt_pace,
    kpi,
)
from utils.palette import CHART_BG, GRAY_SECONDARY, ORANGE, SWIM_DARK

SWIM_MID = "#2A6496"


def render_swimming() -> None:
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{SWIM_DARK} 0%,#001F3F 100%);'
        f'border-radius:12px;padding:22px 28px;margin-bottom:18px;'
        f'border-left:5px solid {ORANGE};">'
        f'<h2 style="color:#fff;margin:0;">🏊‍♂️ Swimming Performance</h2>'
        f'<p style="color:#8EC8E8;margin:4px 0 0;font-size:.9rem;">'
        f'Pace and volume analysis in the pool</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    d_start_s, d_end_s = date_filter_with_download("swim", 500)
    df_all_s = load_all_activities(d_start_s, d_end_s)

    swim_types = ["Swim", "OpenWaterSwim"]
    df_swim = df_all_s[df_all_s["sport_type"].isin(swim_types)].copy()

    if not df_swim.empty:
        df_swim["pace_100m"] = np.where(
            (df_swim["distance"] > 0) & (df_swim["moving_time"] > 0),
            (df_swim["moving_time"] / 60) / (df_swim["distance"] / 100),
            np.nan,
        )
        df_swim = df_swim[df_swim["pace_100m"].between(0.8, 10.0)]

    df_1k_swim = df_swim[df_swim["distance"].between(900, 1100)]  if not df_swim.empty else pd.DataFrame()
    df_2k_swim = df_swim[df_swim["distance"].between(1900, 2100)] if not df_swim.empty else pd.DataFrame()

    if df_swim.empty:
        st.warning("No swimming data found for the selected period.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    pr_1k  = df_1k_swim["pace_100m"].min()  if not df_1k_swim.empty else None
    avg_1k = df_1k_swim["pace_100m"].mean() if not df_1k_swim.empty else None
    pr_2k  = df_2k_swim["pace_100m"].min()  if not df_2k_swim.empty else None

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("PR Pace — 1 km", (fmt_pace(pr_1k)+"/100m") if pr_1k else "N/A",
            f"{len(df_1k_swim)} sessions ~1000m", swim=True)
    with k2:
        kpi("Average Pace — 1 km", (fmt_pace(avg_1k)+"/100m") if avg_1k else "N/A", swim=True)
    with k3:
        kpi("PR Pace — 2 km", (fmt_pace(pr_2k)+"/100m") if pr_2k else "N/A",
            f"{len(df_2k_swim)} sessions ~2000m", swim=True)
    with k4:
        kpi("Total Volume Swum", f"{df_swim['dist_km'].sum():,.1f} km",
            f"{len(df_swim)} sessions", swim=True)

    kpis_data = [
        ("PR Pace 1 km",      (fmt_pace(pr_1k)+"/100m")  if pr_1k  else "N/A"),
        ("Average Pace 1 km", (fmt_pace(avg_1k)+"/100m") if avg_1k else "N/A"),
        ("PR Pace 2 km",      (fmt_pace(pr_2k)+"/100m")  if pr_2k  else "N/A"),
        ("Total Volume",      f"{df_swim['dist_km'].sum():,.1f} km"),
    ]

    st.divider()
    figs: list = []

    # ── Weekly goal ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-title swim">Weekly Swimming Goal</div>', unsafe_allow_html=True)
    week_str_s = _today_local().strftime("%Y-W%V")
    df_week_s  = df_swim[df_swim["year_week"] == week_str_s] if "year_week" in df_swim.columns else pd.DataFrame()
    week_km_s  = df_week_s["dist_km"].sum() if not df_week_s.empty else 0.0

    sc1, _ = st.columns([1, 2])
    with sc1:
        st.markdown(f"**Goal: 2 km swum this week** ({week_km_s:.2f} km completed)")
        fig_goal_s = donut_goal(week_km_s, 2.0, "km / 2km", color_fill=SWIM_DARK, height=240)
        st.plotly_chart(fig_goal_s, use_container_width=True)
        figs.append(("Weekly Swimming Goal (2 km)", fig_goal_s))

    st.divider()

    # ── Volume and pace evolution ─────────────────────────────────────────────
    st.markdown(
        '<div class="section-title swim">Volume and Pace Evolution</div>',
        unsafe_allow_html=True,
    )
    swim_m = (
        df_swim.groupby("month_str")
        .agg(dist_km=("dist_km", "sum"), pace_med=("pace_100m", "mean"), n=("id", "count"))
        .reset_index().sort_values("month_str")
    )
    fig_swim_ev = go.Figure()
    fig_swim_ev.add_trace(go.Bar(
        x=swim_m["month_str"], y=swim_m["dist_km"], name="Volume (km)",
        marker_color=SWIM_DARK, opacity=0.85,
        text=swim_m["dist_km"].apply(lambda v: f"{v:.1f}"),
        textposition="inside", textfont=dict(color="#fff", size=10),
        hovertemplate="Month: %{x}<br>Volume: %{y:.2f} km<extra></extra>",
        yaxis="y",
    ))
    fig_swim_ev.add_trace(go.Scatter(
        x=swim_m["month_str"], y=swim_m["pace_med"], name="Average Pace /100m",
        mode="lines+markers+text",
        line=dict(color=ORANGE, width=2.5), marker=dict(size=8, color=ORANGE),
        text=swim_m["pace_med"].apply(fmt_pace),
        textposition="top center", textfont=dict(size=9, color=ORANGE),
        hovertemplate="Month: %{x}<br>Pace: %{text}/100m<extra></extra>",
        yaxis="y2",
    ))
    fig_swim_ev.update_layout(
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
    st.plotly_chart(fig_swim_ev, use_container_width=True)
    figs.append(("Volume vs. Average Pace Evolution", fig_swim_ev))

    # ── Session frequency and pace by distance ────────────────────────────────
    col_freq, col_pace_dist = st.columns([1, 1.4], gap="large")

    with col_freq:
        st.markdown(
            '<div class="section-title swim">Pool Session Frequency</div>',
            unsafe_allow_html=True,
        )
        freq_m = swim_m[["month_str", "n"]].copy()
        fig_freq = go.Figure(go.Bar(
            x=freq_m["month_str"], y=freq_m["n"],
            marker_color=SWIM_DARK,
            text=freq_m["n"], textposition="inside",
            textfont=dict(color="#fff", size=11),
            hovertemplate="Month: %{x}<br>Sessions: %{y}<extra></extra>",
        ))
        avg_n = freq_m["n"].mean()
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
        st.plotly_chart(fig_freq, use_container_width=True)

    with col_pace_dist:
        st.markdown(
            '<div class="section-title swim">Pace by Distance Swum</div>',
            unsafe_allow_html=True,
        )
        fig_scatter_s = go.Figure()
        fig_scatter_s.add_trace(go.Scatter(
            x=df_swim["dist_km"]*1000, y=df_swim["pace_100m"],
            mode="markers+text",
            marker=dict(size=10, color=SWIM_MID, opacity=0.75,
                        line=dict(color=SWIM_DARK, width=1)),
            text=df_swim["pace_100m"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=7, color=SWIM_DARK),
            hovertemplate="Date: %{customdata}<br>Dist: %{x:.0f} m<br>Pace: %{text}/100m<extra></extra>",
            customdata=df_swim["start_date_local"].dt.strftime("%b %d, %Y"),
        ))
        fig_scatter_s.add_hline(
            y=2.0, line_dash="dash", line_color=ORANGE,
            annotation_text="Ref: 2:00/100m",
            annotation_position="bottom right",
            annotation_font=dict(size=9, color=ORANGE),
        )
        fig_scatter_s.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
        fig_scatter_s.update_xaxes(title_text="Distance (m)")
        fig_scatter_s.update_layout(
            height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=30),
        )
        st.plotly_chart(fig_scatter_s, use_container_width=True)
    figs.append([("Pool Session Frequency", fig_freq), ("Pace by Distance Swum", fig_scatter_s)])

    # ── Pace evolution ~1000m sessions ────────────────────────────────────────
    if not df_1k_swim.empty:
        st.markdown(
            '<div class="section-title swim">Pace Evolution — ~1000m Sessions</div>',
            unsafe_allow_html=True,
        )
        ds_1k = df_1k_swim.sort_values("start_date_local")
        fig_pace_1k = go.Figure()
        if len(ds_1k) >= 3:
            x_num = np.arange(len(ds_1k))
            z = np.polyfit(x_num, ds_1k["pace_100m"].values, 1)
            fig_pace_1k.add_trace(go.Scatter(
                x=ds_1k["start_date_local"], y=np.poly1d(z)(x_num),
                mode="lines", name="Trend",
                line=dict(color=ORANGE, width=1.5, dash="dot"),
            ))
        fig_pace_1k.add_trace(go.Scatter(
            x=ds_1k["start_date_local"], y=ds_1k["pace_100m"],
            mode="markers+lines", name="Actual Pace",
            line=dict(color=SWIM_DARK, width=1.5),
            marker=dict(size=8, color=SWIM_DARK, line=dict(color=ORANGE, width=1.5)),
            text=ds_1k["pace_100m"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=8, color=SWIM_DARK),
            hovertemplate="Date: %{x|%b %d, %Y}<br>Pace: %{text}/100m<extra></extra>",
        ))
        fig_pace_1k.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
        fig_pace_1k.update_layout(
            height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=dict(color=GRAY_SECONDARY),
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig_pace_1k.update_xaxes(gridcolor="rgba(26,46,64,0.12)")
        fig_pace_1k.update_yaxes(gridcolor="rgba(26,46,64,0.12)")
        st.plotly_chart(fig_pace_1k, use_container_width=True)
        figs.append(("Pace Evolution — ~1000m Sessions", fig_pace_1k))

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    _pdf_download_button("Swimming Performance", d_start_s, d_end_s,
                         kpis_data, figs, "swimming", accent_hex="#1A2E40")
