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
    """Renders a styled KPI card. Fixed HTML generation — no nested f-string conditional."""
    cls = "kpi-card swim" if swim else ("kpi-card walk" if walk else "kpi-card")
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def empty_fig(msg: str = "No data available for the selected period") -> go.Figure:
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
    # t=68 when title is set so legend (y=1.01) and title don't overlap
    top_margin = 68 if title else 12
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14, color=title_color), x=0),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family="sans-serif", color=GRAY_SECONDARY),
        margin=dict(l=10, r=10, t=top_margin, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", orientation="h",
            yanchor="bottom", y=1.01, xanchor="left", x=0,
        ),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def date_filter_with_download(key_prefix: str, default_days: int = 0, pdf_title: str = ""):
    """Returns (d_start, d_end). Default start = earliest date in DB (fixes missing data bug)."""
    from utils.db import load_min_date
    today = pd.Timestamp.today().normalize()
    min_date = pd.Timestamp(load_min_date())
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        d_start = st.date_input("From", value=min_date.date(), key=f"{key_prefix}_start")
    with c2:
        d_end = st.date_input("To", value=today.date(), key=f"{key_prefix}_end")
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
        labels=["Achieved", "Remaining"],
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


def fmt_duration(minutes: float) -> str:
    """Formats a duration in minutes as a readable string.
    < 60 min  → '48m'
    >= 60 min → '1h30m' or '2h'
    """
    if minutes is None or (isinstance(minutes, float) and np.isnan(minutes)):
        return "N/A"
    total = int(round(minutes))
    if total < 60:
        return f"{total}m"
    h = total // 60
    m = total % 60
    return f"{h}h{m}m" if m else f"{h}h"


def _pdf_download_button(
    title: str,
    d_start: str,
    d_end: str,
    kpis: list,
    figs: list = None,       # accepted for API compatibility, not used
    key_prefix: str = "",
    accent_hex: str = "#FC4C02",
) -> None:
    """Single-click PDF download — generates instantly (no kaleido)."""
    from utils.pdf import build_pdf
    try:
        pdf_bytes = build_pdf(title, d_start, d_end, kpis, accent_hex=accent_hex)
        st.download_button(
            label="⬇ Download PDF Report",
            data=pdf_bytes,
            file_name=f"{key_prefix}_{d_start}_{d_end}.pdf",
            mime="application/pdf",
            key=f"dl_{key_prefix}",
        )
    except Exception as exc:
        st.error(f"Could not generate PDF: {exc}")


_SE_BRAZIL_LAT = -23.5505   # São Paulo — default map center
_SE_BRAZIL_LON = -46.6333


def render_activity_map(
    df_coords: pd.DataFrame,
    accent_color: str = ORANGE,
    zoom: int = 9,
) -> None:
    """Renders an activity map using st.map (pydeck/deck.gl — CSP-safe).
    Always starts centered on Southeast Brazil (São Paulo area).
    """
    if df_coords.empty or "lat" not in df_coords.columns or len(df_coords) == 0:
        # Show SE Brazil even with no data so the user sees the correct region
        dummy = pd.DataFrame({"lat": [_SE_BRAZIL_LAT], "lon": [_SE_BRAZIL_LON]})
        st.map(dummy, latitude="lat", longitude="lon", zoom=zoom,
               use_container_width=True)
        st.caption("No GPS data recorded for these activities in this period.")
        return
    st.map(
        df_coords,
        latitude="lat",
        longitude="lon",
        color=accent_color,
        zoom=zoom,
        use_container_width=True,
    )
