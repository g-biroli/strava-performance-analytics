import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db import load_activity_coords, load_all_activities
from utils.helpers import (
    _pdf_download_button,
    _today_local,
    apply_base_layout,
    date_filter_with_download,
    donut_goal,
    empty_fig,
    fmt_duration,
    kpi,
    render_activity_map,
)
from utils.palette import (
    CHART_BG,
    GRAY_SECONDARY,
    HEATMAP_COLORSCALE,
    ORANGE,
    SPORT_COLORS,
    SUNSET,
)


def render_overview() -> None:
    st.markdown(
        f'<div style="background:#fff;border-radius:12px;padding:20px 28px;'
        f'margin-bottom:18px;border-bottom:4px solid {ORANGE};">'
        f'<h2 style="color:{ORANGE};margin:0;">📊 Performance Overview</h2>'
        f'<p style="color:{GRAY_SECONDARY};margin:4px 0 0;font-size:.9rem;">'
        f'Complete snapshot across all sports and time periods</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    d_start, d_end = date_filter_with_download("overview", 365)
    df_all = load_all_activities(d_start, d_end)

    if df_all.empty:
        st.warning("No activities found for the selected period.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    gps_types  = ["Run", "TrailRun", "Swim", "OpenWaterSwim", "Ride", "Walk", "Rowing"]
    total_km   = df_all[df_all["sport_type"].isin(gps_types)]["dist_km"].sum()
    total_acts = len(df_all)
    total_h    = df_all["duration_h"].sum()
    avg_hr     = df_all["average_heartrate"].dropna()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Total Activities", str(total_acts), "in the selected period")
    with k2:
        kpi("Accumulated Kilometers", f"{total_km:,.1f} km", "all GPS sports")
    with k3:
        kpi("Moving Hours", f"{total_h:,.0f} h", "time in motion")
    with k4:
        kpi(
            "Average Heart Rate",
            f"{avg_hr.mean():.0f} bpm" if not avg_hr.empty else "N/A",
            f"across {avg_hr.count()} activities with HR",
        )

    kpis_data = [
        ("Total Activities",        str(total_acts)),
        ("Kilometers (GPS)",        f"{total_km:,.1f} km"),
        ("Moving Hours",            f"{total_h:,.0f} h"),
        ("Average Heart Rate",      f"{avg_hr.mean():.0f} bpm" if not avg_hr.empty else "N/A"),
    ]

    st.divider()
    figs: list = []

    # ── Top 3 sports ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Top 3 Sports</div>', unsafe_allow_html=True)
    top3 = (
        df_all.groupby("sport_type").agg(n=("id", "count"))
        .reset_index().sort_values("n", ascending=False).head(3)
        .sort_values("n", ascending=True)
    )
    if not top3.empty:
        fig_top3 = go.Figure(go.Bar(
            x=top3["n"], y=top3["sport_type"], orientation="h",
            marker_color=[SPORT_COLORS.get(s, GRAY_SECONDARY) for s in top3["sport_type"]],
            text=top3["n"].astype(str) + " sessions",
            textposition="inside",
            textfont=dict(color="#fff", size=13, family="sans-serif"),
            hovertemplate="%{y}: %{x} sessions<extra></extra>",
        ))
        apply_base_layout(fig_top3, height=200)
        st.plotly_chart(fig_top3, use_container_width=True)
        figs.append(("Top 3 Sports", fig_top3))

    st.divider()

    # ── Weekly goals ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Current Week Goals</div>', unsafe_allow_html=True)
    week_str  = _today_local().strftime("%Y-W%V")
    df_week   = df_all[df_all["year_week"] == week_str] if "year_week" in df_all.columns else pd.DataFrame()
    week_h    = df_week["duration_h"].sum() if not df_week.empty else 0.0
    week_acts = len(df_week) if not df_week.empty else 0

    m1, m2 = st.columns(2, gap="large")
    with m1:
        st.markdown(f"**Time Goal — 5h per week** ({week_h:.1f}h completed)")
        fig_t = donut_goal(week_h, 5.0, "hours / 5h", color_fill=ORANGE, height=220)
        st.plotly_chart(fig_t, use_container_width=True)
    with m2:
        st.markdown(f"**Frequency Goal — 5 activities** ({week_acts} completed)")
        fig_f = donut_goal(float(week_acts), 5.0, "activities / 5", color_fill=SUNSET, height=220)
        st.plotly_chart(fig_f, use_container_width=True)
    figs.append([("Weekly Goal — Time (5h)", fig_t), ("Weekly Goal — Frequency (5 activities)", fig_f)])

    st.divider()

    col_heatmap, col_donut = st.columns([3, 1.4], gap="large")

    # ── Activity calendar ─────────────────────────────────────────────────────
    with col_heatmap:
        st.markdown('<div class="section-title">Activity Calendar</div>', unsafe_allow_html=True)
        daily = (
            df_all.groupby("date_only")
            .agg(count=("id", "count"), km=("dist_km", "sum"))
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
        fig_heat = go.Figure(go.Heatmap(
            z=grid_pivot.values,
            x=list(grid_pivot.columns),
            y=[day_names[i] for i in grid_pivot.index],
            colorscale=HEATMAP_COLORSCALE,
            showscale=False,
            hovertemplate="Week: %{x}<br>Day: %{y}<br>Sessions: %{z}<extra></extra>",
            xgap=2, ygap=2,
        ))
        n_weeks = len(week_order)
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
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Sport mix donut ───────────────────────────────────────────────────────
    with col_donut:
        st.markdown('<div class="section-title">Sport Mix</div>', unsafe_allow_html=True)
        mix = (
            df_all.groupby("sport_type").agg(n=("id", "count"))
            .reset_index().sort_values("n", ascending=False)
        )
        colors_donut = [SPORT_COLORS.get(s, GRAY_SECONDARY) for s in mix["sport_type"]]
        fig_donut = go.Figure(go.Pie(
            labels=mix["sport_type"], values=mix["n"], hole=0.55,
            marker=dict(colors=colors_donut, line=dict(color="#ffffff", width=2)),
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
        st.plotly_chart(fig_donut, use_container_width=True)
    figs.append([("Activity Calendar", fig_heat), ("Sport Mix", fig_donut)])

    # ── Monthly volume by sport ────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Monthly Volume by Sport (minutes)</div>',
        unsafe_allow_html=True,
    )
    all_types = list(SPORT_COLORS.keys())
    vol_m = (
        df_all[df_all["sport_type"].isin(all_types)]
        .groupby(["month_str", "sport_type"])["duration_min"]
        .sum().reset_index().sort_values("month_str")
    )
    if not vol_m.empty:
        THRESHOLD_MIN = 10   # hide label for sessions under 10 minutes
        vol_m["text_label"] = vol_m["duration_min"].apply(
            lambda v: fmt_duration(v) if v >= THRESHOLD_MIN else ""
        )
        fig_bar_vol = px.bar(
            vol_m, x="month_str", y="duration_min", color="sport_type",
            color_discrete_map=SPORT_COLORS,
            text="text_label",
            labels={"month_str": "", "duration_min": "Minutes", "sport_type": ""},
        )
        fig_bar_vol.update_traces(textposition="inside", textfont_size=9)
        fig_bar_vol.update_xaxes(categoryorder="category ascending", tickangle=-30)
        apply_base_layout(fig_bar_vol, height=340)
        st.plotly_chart(fig_bar_vol, use_container_width=True)
        figs.append(("Monthly Volume by Sport (min)", fig_bar_vol))
    else:
        st.plotly_chart(empty_fig(), use_container_width=True)

    # ── Activity Map ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-title">Activity Map</div>', unsafe_allow_html=True)
    gps_map_types = ("Run", "TrailRun", "Swim", "OpenWaterSwim", "Ride", "Walk", "Hike", "Rowing")
    df_coords = load_activity_coords(gps_map_types, d_start, d_end)
    render_activity_map(df_coords, accent_color=ORANGE)

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    _pdf_download_button("Performance Overview", d_start, d_end, kpis_data, figs,
                         "overview", accent_hex="#FC4C02")
