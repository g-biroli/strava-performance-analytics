import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.db import load_all_activities
from utils.helpers import (
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
        f"""<div style="background:{CREAM};border-radius:12px;padding:22px 28px;
                margin-bottom:18px;border-left:5px solid {ORANGE};">
            <h2 style="color:{ORANGE};margin:0;">🏃‍♂️ Performance em Corrida</h2>
            <p style="color:{GRAY_SECONDARY};margin:4px 0 0;font-size:.9rem;">
            Análise de ritmo, volume e evolução nas corridas</p>
        </div>""",
        unsafe_allow_html=True,
    )

    d_start_r, d_end_r = date_filter_with_download("run", 400, "Relatório de Corrida")
    df_all_r = load_all_activities(d_start_r, d_end_r)

    run_types = ["Run", "TrailRun", "VirtualRun"]
    df_run = df_all_r[df_all_r["sport_type"].isin(run_types)].copy()
    df_run = df_run[df_run["pace_min_km"].between(3.0, 20.0)]

    if df_run.empty:
        st.warning("Sem dados de corrida para o período selecionado.")
        return

    df_5k  = df_run[df_run["distance"].between(4900, 5500)].copy()
    df_10k = df_run[df_run["distance"].between(9800, 10500)].copy()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        pr_5k = df_5k["pace_min_km"].min() if not df_5k.empty else None
        kpi("PR — 5 km", fmt_pace(pr_5k), f"{len(df_5k)} corridas registradas")
    with k2:
        avg_5k = df_5k["pace_min_km"].mean() if not df_5k.empty else None
        kpi("Pace Médio — 5 km", fmt_pace(avg_5k))
    with k3:
        pr_10k = df_10k["pace_min_km"].min() if not df_10k.empty else None
        kpi("PR — 10 km", fmt_pace(pr_10k), f"{len(df_10k)} corridas registradas")
    with k4:
        kpi("Volume Total", f"{df_run['dist_km'].sum():,.1f} km", f"{len(df_run)} sessões de corrida")
    with k5:
        hr_run = df_run["average_heartrate"].dropna()
        kpi(
            "FC Média Corrida",
            f"{hr_run.mean():.0f} bpm" if not hr_run.empty else "N/A",
            f"em {len(hr_run)} corridas c/ HR",
        )

    st.divider()

    # ── Meta semanal ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Meta Semanal de Corrida</div>', unsafe_allow_html=True)
    week_str_r = pd.Timestamp.today().strftime("%Y-W%V")
    df_week_r  = df_run[df_run["year_week"] == week_str_r] if "year_week" in df_run.columns else pd.DataFrame()
    week_km_r  = df_week_r["dist_km"].sum() if not df_week_r.empty else 0.0

    mc1, mc2 = st.columns([1, 2], gap="large")
    with mc1:
        st.markdown(f"**Meta: 5 km acumulados na semana** ({week_km_r:.1f} km realizados)")
        st.plotly_chart(
            donut_goal(week_km_r, 5.0, "km / 5km", color_fill=SUNSET, height=240),
            use_container_width=True,
        )
    with mc2:
        st.markdown('<div class="section-title">Turismo Esportivo</div>', unsafe_allow_html=True)
        sp_keywords = ["são paulo", "sao paulo", "sp", "são paulo"]

        def _is_outside_sp(row):
            return not any(k in str(row.get("name", "") or "").lower() for k in sp_keywords)

        mask       = df_run.apply(_is_outside_sp, axis=1)
        n_outside  = int(mask.sum())
        km_outside = df_run.loc[mask, "dist_km"].sum()
        st.markdown(
            f"""<div style="background:{CREAM};border-left:4px solid {ORANGE};
                    border-radius:8px;padding:16px 20px;margin-top:10px;">
                <div style="font-size:.8rem;text-transform:uppercase;
                     color:{GRAY_SECONDARY};letter-spacing:.05em;">Corridas fora de São Paulo</div>
                <div style="font-size:2rem;font-weight:700;color:{ORANGE};">{n_outside}</div>
                <div style="font-size:.9rem;color:{GRAY_SECONDARY};">
                {km_outside:.1f} km explorados em outras localidades</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Evolução de pace ───────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Evolução do Pace — 5 km e 10 km</div>', unsafe_allow_html=True)
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
            hovertemplate=f"<b>{label}</b><br>Data: %{{x|%d/%m/%Y}}<br>Pace: %{{text}}/km<extra></extra>",
        ))
        if len(ds) >= 3:
            x_num = np.arange(len(ds))
            z = np.polyfit(x_num, ds["pace_min_km"].values, 1)
            fig_pace.add_trace(go.Scatter(
                x=ds["start_date_local"], y=np.poly1d(z)(x_num),
                mode="lines", name=f"Tendência {label}",
                line=dict(color=color, width=1, dash="dot"), showlegend=False,
            ))
    fig_pace.update_yaxes(autorange="reversed", tickformat=".2f", title_text="Pace (min/km)")
    fig_pace.update_xaxes(title_text="")
    fig_pace.add_annotation(
        text="Eixo Y invertido: menor valor = ritmo mais rápido",
        xref="paper", yref="paper", x=1, y=0, showarrow=False,
        font=dict(size=9, color=GRAY_SECONDARY), xanchor="right",
    )
    apply_base_layout(fig_pace, height=360, title="Pace por Sessão (5 km e 10 km)")
    st.plotly_chart(fig_pace, use_container_width=True)

    # ── Volume mensal ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Volume Mensal de Rodagem</div>', unsafe_allow_html=True)
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
            hovertemplate="Mês: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
        ))
        fig_vol_r.update_xaxes(tickangle=-30, categoryorder="total descending")
        fig_vol_r.update_yaxes(title_text="km")
        apply_base_layout(fig_vol_r, height=300, title="km de Corrida por Mês")
        st.plotly_chart(fig_vol_r, use_container_width=True)
    else:
        st.plotly_chart(empty_fig(), use_container_width=True)

    # ── Zonas de FC ────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Distribuição de Frequência Cardíaca (Corrida)</div>',
        unsafe_allow_html=True,
    )
    df_run_hr = df_run.dropna(subset=["average_heartrate"]).copy()
    if not df_run_hr.empty:
        FC_MAX   = 195
        bins     = [0, 0.60*FC_MAX, 0.70*FC_MAX, 0.80*FC_MAX, 0.90*FC_MAX, FC_MAX+50]
        labels_z = ["Z1 — Recuperação", "Z2 — Base Aeróbica", "Z3 — Tempo", "Z4 — Limiar", "Z5 — VO2max"]
        colors_z = ["#4CAF50", "#8BC34A", ORANGE, "#FF5722", "#B71C1C"]
        df_run_hr["zona"] = pd.cut(df_run_hr["average_heartrate"], bins=bins, labels=labels_z)
        zona_counts = df_run_hr["zona"].value_counts().reindex(labels_z).fillna(0).reset_index()
        zona_counts.columns = ["zona", "count"]
        fig_zones = go.Figure(go.Bar(
            x=zona_counts["count"], y=zona_counts["zona"], orientation="h",
            marker_color=colors_z,
            text=zona_counts["count"].astype(int),
            textposition="inside", textfont=dict(color="#fff", size=11),
            hovertemplate="%{y}: %{x} sessões<extra></extra>",
        ))
        fig_zones.update_xaxes(title_text="Número de sessões")
        fig_zones.update_yaxes(autorange="reversed")
        apply_base_layout(fig_zones, height=300, title=f"Zonas de FC por Sessão (FCmax ref: {FC_MAX} bpm)")
        st.plotly_chart(fig_zones, use_container_width=True)
        st.caption("Zonas calculadas sobre a FC média da atividade. Ajuste `FC_MAX` para calibrar ao seu perfil.")
    else:
        st.info("Sem dados de frequência cardíaca nas corridas do período.")

    # ── Evolução mensal pace 5k ────────────────────────────────────────────────
    if not df_5k.empty:
        st.markdown('<div class="section-title">Evolução Mensal do Pace — 5 km</div>', unsafe_allow_html=True)
        monthly_5k = (
            df_5k.groupby("month_str")["pace_min_km"]
            .agg(pr="min", media="mean", pior="max", n="count")
            .reset_index().sort_values("month_str")
        )
        fig_m5k = go.Figure()
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["pior"],
            mode="lines", line=dict(width=0), showlegend=False, name="Pior",
        ))
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["pr"],
            fill="tonexty", fillcolor="rgba(252,76,2,0.12)",
            mode="lines+markers+text",
            line=dict(color=ORANGE, width=2), marker=dict(symbol="star", size=10, color=ORANGE),
            name="PR Mensal",
            text=monthly_5k["pr"].apply(fmt_pace),
            textposition="bottom center", textfont=dict(size=9),
            hovertemplate="Mês: %{x}<br>PR: %{text}/km<extra></extra>",
        ))
        fig_m5k.add_trace(go.Scatter(
            x=monthly_5k["month_str"], y=monthly_5k["media"],
            mode="lines+markers",
            line=dict(color=SUNSET, width=1.5, dash="dash"), marker=dict(size=5),
            name="Média Mensal",
            text=monthly_5k["media"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=8),
            hovertemplate="Mês: %{x}<br>Média: %{text}/km<extra></extra>",
        ))
        fig_m5k.update_yaxes(autorange="reversed", title_text="Pace (min/km)", tickformat=".2f")
        apply_base_layout(fig_m5k, height=320)
        st.plotly_chart(fig_m5k, use_container_width=True)
