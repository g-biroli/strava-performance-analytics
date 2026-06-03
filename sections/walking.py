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
    kpi,
)
from utils.palette import CHART_BG, GRAY_SECONDARY, GREEN_OUTDOOR, ORANGE

WALK_GOAL_KM = 15.0


def render_walking() -> None:
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{GREEN_OUTDOOR} 0%,#1E3D2A 100%);'
        f'border-radius:12px;padding:22px 28px;margin-bottom:18px;'
        f'border-left:5px solid {ORANGE};">'
        f'<h2 style="color:#fff;margin:0;">🥾 Walking Performance</h2>'
        f'<p style="color:#A8D5B5;margin:4px 0 0;font-size:.9rem;">'
        f'Trails, urban walks, and active tourism</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    d_start_w, d_end_w = date_filter_with_download("walk", 500)
    df_all_w = load_all_activities(d_start_w, d_end_w)

    walk_types = ["Walk", "Hike"]
    df_walk = df_all_w[df_all_w["sport_type"].isin(walk_types)].copy()

    if df_walk.empty:
        st.warning("No walking data found for the selected period.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    elev = df_walk["total_elevation_gain"].dropna().sum()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Total Outings", str(len(df_walk)), "walking sessions", walk=True)
    with k2:
        kpi("Total Distance", f"{df_walk['dist_km'].sum():,.1f} km", "accumulated in period", walk=True)
    with k3:
        kpi("Hours Walking", f"{df_walk['duration_h'].sum():,.0f} h", "time in motion", walk=True)
    with k4:
        kpi("Elevation Gain", f"{elev:,.0f} m", "total accumulated", walk=True)

    kpis_data = [
        ("Total Outings",    str(len(df_walk))),
        ("Total Distance",   f"{df_walk['dist_km'].sum():,.1f} km"),
        ("Hours Walking",    f"{df_walk['duration_h'].sum():,.0f} h"),
        ("Elevation Gain",   f"{elev:,.0f} m"),
    ]

    st.divider()
    figs: list = []

    # ── Weekly goal ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-title walk">Weekly Walking Goal</div>', unsafe_allow_html=True)
    week_str_w = pd.Timestamp.today().strftime("%Y-W%V")
    df_week_w  = df_walk[df_walk["year_week"] == week_str_w] if "year_week" in df_walk.columns else pd.DataFrame()
    week_km_w  = df_week_w["dist_km"].sum() if not df_week_w.empty else 0.0

    wc1, wc2 = st.columns([1, 2])
    with wc1:
        st.markdown(f"**Goal: {WALK_GOAL_KM:.0f} km this week** ({week_km_w:.1f} km completed)")
        fig_goal_w = donut_goal(
            week_km_w, WALK_GOAL_KM, f"km / {WALK_GOAL_KM:.0f}km",
            color_fill=GREEN_OUTDOOR, height=240,
        )
        st.plotly_chart(fig_goal_w, use_container_width=True)
        figs.append((f"Weekly Walking Goal ({WALK_GOAL_KM:.0f} km)", fig_goal_w))

    with wc2:
        st.markdown('<div class="section-title walk">Walking Tourism</div>', unsafe_allow_html=True)
        sp_keywords_w = ["são paulo", "sao paulo", "sp"]

        def _is_outside_sp_w(row):
            return not any(k in str(row.get("name", "") or "").lower() for k in sp_keywords_w)

        mask_w       = df_walk.apply(_is_outside_sp_w, axis=1)
        n_outside_w  = int(mask_w.sum())
        km_outside_w = df_walk.loc[mask_w, "dist_km"].sum()
        st.markdown(
            f'<div style="background:#F0F7F3;border-left:4px solid {GREEN_OUTDOOR};'
            f'border-radius:8px;padding:16px 20px;margin-top:10px;">'
            f'<div style="font-size:.8rem;text-transform:uppercase;'
            f'color:{GRAY_SECONDARY};letter-spacing:.05em;">Walks outside São Paulo</div>'
            f'<div style="font-size:2rem;font-weight:700;color:{GREEN_OUTDOOR};">{n_outside_w}</div>'
            f'<div style="font-size:.9rem;color:{GRAY_SECONDARY};">'
            f'{km_outside_w:.1f} km explored on trails and other locations</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Monthly volume ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title walk">Monthly Volume (km)</div>', unsafe_allow_html=True)
    vol_w = (
        df_walk.groupby("month_str")["dist_km"].sum()
        .reset_index().sort_values("dist_km", ascending=False)
    )
    if not vol_w.empty:
        fig_vol_w = go.Figure(go.Bar(
            x=vol_w["month_str"], y=vol_w["dist_km"],
            marker_color=GREEN_OUTDOOR,
            text=vol_w["dist_km"].apply(lambda v: f"{v:.1f} km"),
            textposition="inside", textfont=dict(color="#fff", size=10),
            hovertemplate="Month: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
        ))
        fig_vol_w.update_xaxes(tickangle=-30, categoryorder="total descending")
        fig_vol_w.update_yaxes(title_text="km")
        apply_base_layout(
            fig_vol_w, height=320,
            title="Walking km by Month (descending order)",
            title_color=GREEN_OUTDOOR,
        )
        st.plotly_chart(fig_vol_w, use_container_width=True)
        figs.append(("Monthly Walking Volume (km)", fig_vol_w))
    else:
        st.plotly_chart(
            empty_fig("No walking volume available for the selected period."),
            use_container_width=True,
        )

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    _pdf_download_button("Walking Performance", d_start_w, d_end_w,
                         kpis_data, figs, "walking", accent_hex="#3B6E4C")
