import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.palette import CHART_BG, GRAY_ICE, GRAY_SECONDARY, GRID_COLOR, ORANGE, SUNSET


def fmt_pace(p) -> str:
    if p is None or (isinstance(p, float) and (np.isnan(p) or p <= 0)):
        return "N/A"
    m = int(p)
    s = int(round((p - m) * 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


def kpi(label: str, value: str, sub: str = "", swim: bool = False, walk: bool = False):
    cls = "kpi-card swim" if swim else ("kpi-card walk" if walk else "kpi-card")
    st.markdown(
        f"""<div class="{cls}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
        </div>""",
        unsafe_allow_html=True,
    )


def empty_fig(msg: str = "Sem dados para o período selecionado") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color=GRAY_SECONDARY),
    )
    fig.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        xaxis_visible=False, yaxis_visible=False, height=280,
    )
    return fig


def apply_base_layout(
    fig: go.Figure,
    height: int = 340,
    title: str = "",
    title_color: str = GRAY_SECONDARY,
) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14, color=title_color), x=0),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family="sans-serif", color=GRAY_SECONDARY),
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", orientation="h",
            yanchor="bottom", y=1.01, xanchor="left", x=0,
        ),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def _stub_pdf(title: str) -> bytes:
    content = (
        f"%PDF-1.4\n"
        f"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        f"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        f"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        f"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        f"4 0 obj<</Length 80>>stream\nBT /F1 18 Tf 50 750 Td ({title}) Tj ET\nendstream\nendobj\n"
        f"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        f"xref\n0 6\n0000000000 65535 f\ntrailer<</Size 6/Root 1 0 R>>\n%%EOF"
    )
    return content.encode("latin-1")


def date_filter_with_download(key_prefix: str, default_days: int, pdf_title: str):
    today = pd.Timestamp.today().normalize()
    default_start = today - pd.Timedelta(days=default_days)
    c1, c2, c3, _ = st.columns([1, 1, 1, 1])
    with c1:
        d_start = st.date_input("De", value=default_start.date(), key=f"{key_prefix}_start")
    with c2:
        d_end = st.date_input("Até", value=today.date(), key=f"{key_prefix}_end")
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="⬇ Baixar PDF",
            data=_stub_pdf(pdf_title),
            file_name=f"relatorio_{key_prefix}.pdf",
            mime="application/pdf",
            key=f"{key_prefix}_pdf",
        )
    return str(d_start), str(d_end)


def donut_goal(
    current: float,
    goal: float,
    label: str,
    color_fill: str = SUNSET,
    height: int = 260,
) -> go.Figure:
    pct = min(current / goal, 1.0) if goal > 0 else 0
    remaining = max(goal - current, 0)
    fig = go.Figure(go.Pie(
        values=[current, remaining],
        labels=["Realizado", "Restante"],
        hole=0.65,
        marker=dict(colors=[color_fill, GRAY_ICE], line=dict(color="#ffffff", width=2)),
        textinfo="none",
        hovertemplate="%{label}: %{value:.1f}<extra></extra>",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{pct*100:.0f}%</b><br><span style='font-size:10px'>{label}</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=18, color=color_fill),
    )
    fig.update_layout(
        height=height, showlegend=False,
        paper_bgcolor=CHART_BG, margin=dict(l=0, r=0, t=10, b=0),
    )
    return fig
