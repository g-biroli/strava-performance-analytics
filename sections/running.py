import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.db import load_all_activities
from utils.helpers import (
    _pdf_download_button,
    apply_base_layout,
    date_filter_with_download,
    donut_goal,
    empty_fig,
    fmt_pace,
    kpi,
)
from utils.palette import BLUE_DEPTH, CHART_BG, CREAM, GRAY_SECONDARY, ORANGE, SUNSET


def render_running() -> None:
    st.markdown(
        f'<div style="background:{CREAM};border-radius:12px;padding:22px 28px;'
        f'margin-bottom:18px;border-left:5px solid {ORANGE};">'
        f'<h2 style="color:{ORANGE};margin:0;">🏃‍♂️ Running Performance</h2>'
        f'<p style="color:{GRAY_SECONDARY};margin:4px 0 0;font-size:.9rem;">'
        f'Pace, volume, and progress analysis for running</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    d_start_r, d_end_r = date_filter_with_download("run", 400)
    df_all_r = load_all_activities(d_start_r, d_end_r)

    run_types = ["Run", "TrailRun", "VirtualRun"]
    df_run = df_all_r[df_all_r["sport_type"].isin(run_types)].copy()
    df_run = df_run[df_run["pace_min_km"].between(3.0, 20.0)]

    if df_run.empty:
        st.warning("No running data found for the selected period.")
        return

    df_5k  = df_run[df_run["distance"].between(4900, 5500)].copy()
    df_10k = df_run[df_run["distance"].between(9800, 10500)].copy()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    pr_5k  = df_5k["pace_min_km"].min()  if not df_5k.empty  else None
    avg_5k = df_5k["pace_min_km"].mean() if not df_5k.empty  else None
    pr_10k = df_10k["pace_min_km"].min() if not df_10k.empty else None
    hr_run = df_run["average_heartrate"].dropna()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi("PR — 5 km", fmt_pace(pr_5k), f"{len(df_5k)} sessions recorded")
    with k2:
        kpi("Average Pace — 5 km", fmt_pace(avg_5k), f"{len(df_5k)} sessions recorded")
    with k3:
        kpi("PR — 10 km", fmt_pace(pr_10k), f"{len(df_10k)} sessions recorded")
    with k4:
        kpi("Total Volume", f"{df_run['dist_km'].sum():,.1f} km", f"{len(df_run)} running sessions")
    with k5:
        kpi(
            "Average Running HR",
            f"{hr_run.mean():.0f} bpm" if not hr_run.empty else "N/A",
            f"across {len(hr_run)} runs with HR",
        )

    kpis_data = [
        ("PR — 5 km",           fmt_pace(pr_5k)),
        ("Average Pace 5 km",   fmt_pace(avg_5k)),
        ("PR — 10 km",          fmt_pace(pr_10k)),
        ("Total Volume",        f"{df_run['dist_km'].sum():,.1f} km"),
        ("Average HR",          f"{hr_run.mean():.0f} bpm" if not hr_run.empty else "N/A"),
    ]

    st.divider()
    figs: list = []

    # ── Weekly goal ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Weekly Running Goal</div>', unsafe_allow_html=True)
    week_str_r = pd.Timestamp.today().strftime("%Y-W%V")
    df_week_r  = df_run[df_run["year_week"] == week_str_r] if "year_week" in df_run.columns else pd.DataFrame()
    week_km_r  = df_week_r["dist_km"].sum() if not df_week_r.empty else 0.0

    mc1, mc2 = st.columns([1, 2], gap="large")
    with mc1:
        st.markdown(f"**Goal: 5 km accumulated this week** ({week_km_r:.1f} km completed)")
        fig_goal_r = donut_goal(week_km_r, 5.0, "km / 5km", color_fill=SUNSET, height=240)
        st.plotly_chart(fig_goal_r, use_container_width=True)
        figs.append(("Weekly Running Goal (5 km)", fig_goal_r))

    with mc2:
        st.markdown('<div class="section-title">Sports Tourism</div>', unsafe_allow_html=True)
        sp_keywords = ["são paulo", "sao paulo", "sp"]

        def _is_outside_sp(row):
            return not any(k in str(row.get("name", "") or "").lower() for k in sp_keywords)

        mask       = df_run.apply(_is_outside_sp, axis=1)
        n_outside  = int(mask.sum())
        km_outside = df_run.loc[mask, "dist_km"].sum()
        st.markdown(
            f'<div style="background:{CREAM};border-left:4px solid {ORANGE};'
            f'border-radius:8px;padding:16px 20px;margin-top:10px;">'
            f'<div style="font-size:.8rem;text-transform:uppercase;'
            f'color:{GRAY_SECONDARY};letter-spacing:.05em;">Runs outside São Paulo</div>'
            f'<div style="font-size:2rem;font-weight:700;color:{ORANGE};">{n_outside}</div>'
            f'<div style="font-size:.9rem;color:{GRAY_SECONDARY};">'
            f'{km_outside:.1f} km explored in other locations</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Pace evolution ────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Pace Evolution — 5 km and 10 km</div>',
        unsafe_allow_html=True,
    )
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
            hovertemplate=f"<b>{label}</b><br>Date: %{{x|%b %d, %Y}}<br>Pace: %{{text}}/km<extra></extra>",
        ))
        if len(ds) >= 3:
            x_num = np.arange(len(ds))
            z = np.polyfit(x_num, ds["pace_min_km"].values, 1)
            fig_pace.add_trace(go.Scatter(
                x=ds["start_date_local"], y=np.poly1d(z)(x_num),
                mode="lines", name=f"Trend {label}",
                line=dict(color=color, width=1, dash="dot"), showlegend=False,
            ))
    fig_pace.update_yaxes(autorange="reversed", tickformat=".2f", title_text="Pace (min/km)")
    fig_pace.update_xaxes(title_text="")
    fig_pace.add_annotation(
        text="Y-axis inverted: lower value = faster pace",
        xref="paper", yref="paper", x=1, y=0, showarrow=False,
        font=dict(size=9, color=GRAY_SECONDARY), xanchor="right",
    )
    apply_base_layout(fig_pace, height=360, title="Pace per Session (5 km and 10 km)")
    st.plotly_chart(fig_pace, use_container_width=True)
    figs.append(("Pace Evolution — 5 km and 10 km", fig_pace))

    # ── Monthly volume ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Monthly Training Volume</div>', unsafe_allow_html=True)
    vol_r = (
        df_run.groupby("month_str")["dist_km"].sum()
        .reset_index().sort_values("dist_km", ascending=False)
    )
    if not vol_r.empty:
        fig_vol_r = go.Figure(go.Bar(
            x=vol_r["month_str"], y=vol_r["dist_km"],
            marker_color=ORANGE,
            text=vol_r["dist_km"].apply(lambda v: f"{v:.1f}"),
            textposition="inside", textfont=dict(color="#fff", size=10),
            hovertemplate="Month: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
        ))
        fig_vol_r.update_xaxes(tickangle=-30, categoryorder="total descending")
        fig_vol_r.update_yaxes(title_text="km")
        apply_base_layout(fig_vol_r, height=300, title="Running km by Month")
        st.plotly_chart(fig_vol_r, use_container_width=True)
        figs.append(("Monthly Training Volume (km)", fig_vol_r))
    else:
        st.plotly_chart(empty_fig(), use_container_width=True)

    # ── Pace by Distance ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Pace by Distance</div>', unsafe_allow_html=True)
    fig_scatter_r = go.Figure()
    fig_scatter_r.add_trace(go.Scatter(
        x=df_run["dist_km"],
        y=df_run["pace_min_km"],
        mode="markers",
        marker=dict(size=9, color=ORANGE, opacity=0.65, line=dict(color=CREAM, width=1)),
        text=df_run["start_date_local"].dt.strftime("%b %d, %Y"),
        hovertemplate="Date: %{text}<br>Distance: %{x:.1f} km<br>Pace: %{customdata}/km<extra></extra>",
        customdata=df_run["pace_min_km"].apply(fmt_pace),
    ))
    avg_pace = df_run["pace_min_km"].mean()
    fig_scatter_r.add_hline(
        y=avg_pace, line_dash="dash", line_color=BLUE_DEPTH,
        annotation_text=f"Avg: {fmt_pace(avg_pace)}/km",
        annotation_position="top right",
        annotation_font=dict(size=9, color=BLUE_DEPTH),
    )
    fig_scatter_r.update_yaxes(autorange="reversed", title_text="Pace (min/km)", tickformat=".2f")
    fig_scatter_r.update_xaxes(title_text="Distance (km)")
    fig_scatter_r.update_layout(
        height=320, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=GRAY_SECONDARY), margin=dict(l=10, r=10, t=10, b=30),
    )
    st.plotly_chart(fig_scatter_r, use_container_width=True)
    figs.append(("Pace by Distance", fig_scatter_r))

    # ── Heart rate zones ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Heart Rate Distribution (Running)</div>',
        unsafe_allow_html=True,
    )
    df_run_hr = df_run.dropna(subset=["average_heartrate"]).copy()
    if not df_run_hr.empty:
        FC_MAX   = 195
        bins     = [0, 0.60*FC_MAX, 0.70*FC_MAX, 0.80*FC_MAX, 0.90*FC_MAX, FC_MAX+50]
        labels_z = ["Z1 — Recovery", "Z2 — Aerobic Base", "Z3 — Tempo", "Z4 — Threshold", "Z5 — VO2max"]
        colors_z = ["#4CAF50", "#8BC34A", ORANGE, "#FF5722", "#B71C1C"]
        df_run_hr["zone"] = pd.cut(df_run_hr["average_heartrate"], bins=bins, labels=labels_z)
        zone_counts = df_run_hr["zone"].value_counts().reindex(labels_z).fillna(0).reset_index()
        zone_counts.columns = ["zone", "count"]
        fig_zones = go.Figure(go.Bar(
            x=zone_counts["count"], y=zone_counts["zone"], orientation="h",
            marker_color=colors_z,
            text=zone_counts["count"].astype(int),
            textposition="inside", textfont=dict(color="#fff", size=11),
            hovertemplate="%{y}: %{x} sessions<extra></extra>",
        ))
        fig_zones.update_xaxes(title_text="Number of sessions")
        fig_zones.update_yaxes(autorange="reversed")
        apply_base_layout(
            fig_zones, height=300,
            title=f"HR Zones by Session (max HR ref: {FC_MAX} bpm)",
        )
        st.plotly_chart(fig_zones, use_container_width=True)
        figs.append(("Heart Rate Zone Distribution", fig_zones))
        st.caption(
            "Zones calculated from average session HR. Adjust `FC_MAX` to calibrate for your profile."
        )
    else:
        st.info("No heart rate data available for the running sessions in this period.")

    # ── Monthly pace evolution — 5k ───────────────────────────────────────────
    if not df_5k.empty:
        st.markdown(
            '<div class="section-title">Monthly Pace Evolution — 5 km</div>',
            unsafe_allow_html=True,
        )
        monthly_5k = (
            df_5k.groupby("month_str")["pace_min_km"]
            .agg(pr="min", avg="mean", worst="max", n="count")
            .reset_index().sort_values("month_str")
        )
        fig_m5k = go.Figure()
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["worst"],
            mode="lines", line=dict(width=0), showlegend=False, name="Worst",
        ))
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["pr"],
            fill="tonexty", fillcolor="rgba(252,76,2,0.12)",
            mode="lines+markers+text",
            line=dict(color=ORANGE, width=2), marker=dict(symbol="star", size=10, color=ORANGE),
            name="Monthly PR",
            text=monthly_5k["pr"].apply(fmt_pace),
            textposition="bottom center", textfont=dict(size=9),
            hovertemplate="Month: %{x}<br>PR: %{text}/km<extra></extra>",
        ))
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["avg"],
            mode="lines+markers",
            line=dict(color=SUNSET, width=1.5, dash="dash"), marker=dict(size=5),
            name="Monthly Average",
            text=monthly_5k["avg"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=8),
            hovertemplate="Month: %{x}<br>Average: %{text}/km<extra></extra>",
        ))
        fig_m5k.update_yaxes(autorange="reversed", title_text="Pace (min/km)", tickformat=".2f")
        apply_base_layout(fig_m5k, height=320)
        st.plotly_chart(fig_m5k, use_container_width=True)
        figs.append(("Monthly Pace Evolution — 5 km", fig_m5k))

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    _pdf_download_button("Running Performance", d_start_r, d_end_r,
                         kpis_data, figs, "running")
