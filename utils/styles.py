import streamlit as st

from utils.palette import (
    CREAM, DARK_TITLE, GRAY_SECONDARY, GREEN_OUTDOOR, ORANGE, SUNSET, SWIM_DARK,
)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        /* ── Botões ── */
        .stButton > button {{
            border: 1.5px solid {ORANGE}; color: {ORANGE}; background: transparent;
            font-weight: 600;
        }}
        .stButton > button:hover {{ background: {ORANGE}; color: #fff; }}

        /* ── KPI cards ── */
        .kpi-card {{
            background: var(--secondary-background-color);
            border-left: 4px solid {ORANGE};
            border-radius: 8px; padding: 14px 18px; margin-bottom: 6px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }}
        .kpi-card.swim {{ border-left-color: {SWIM_DARK}; }}
        .kpi-card.walk {{ border-left-color: {GREEN_OUTDOOR}; }}
        .kpi-label {{
            font-size:.78rem; opacity:.55; margin-bottom:2px;
            text-transform:uppercase; letter-spacing:.05em; color:var(--text-color);
        }}
        .kpi-value {{ font-size:1.65rem; font-weight:700; color:{ORANGE}; }}
        .kpi-card.swim .kpi-value {{ color:{SWIM_DARK}; }}
        .kpi-card.walk .kpi-value {{ color:{GREEN_OUTDOOR}; }}
        .kpi-sub {{ font-size:.8rem; opacity:.5; color:var(--text-color); }}

        /* ── Section title ── */
        .section-title {{
            font-size:1.05rem; font-weight:700; color:{ORANGE};
            border-bottom:2px solid {ORANGE}30;
            padding-bottom:5px; margin:20px 0 12px; letter-spacing:.01em;
        }}
        .section-title.swim {{ color:{SWIM_DARK}; border-bottom-color:{SWIM_DARK}30; }}
        .section-title.walk {{ color:{GREEN_OUTDOOR}; border-bottom-color:{GREEN_OUTDOOR}30; }}

        /* ── Profile card ── */
        .profile-card {{
            background: var(--secondary-background-color);
            border-radius: 12px; padding: 28px 24px; text-align: center;
        }}
        .profile-card img {{
            border-radius:50%; width:120px; height:120px; object-fit:cover;
            border:3px solid {ORANGE};
        }}
        .profile-name {{ font-size:1.3rem; font-weight:700; margin-top:12px; color:{DARK_TITLE}; }}
        .profile-links a {{
            display:inline-block; margin:6px 4px 0; padding:7px 16px;
            border-radius:6px; font-size:.83rem; font-weight:600;
            text-decoration:none; border:1.5px solid {ORANGE}; color:{ORANGE};
        }}
        .profile-links a:hover {{ background:{ORANGE}; color:#fff; }}
        .strava-cta a {{
            display:inline-block; margin-top:12px; padding:10px 22px;
            background:{ORANGE}; color:#fff !important; border-radius:8px;
            font-weight:700; text-decoration:none; font-size:.93rem;
        }}

        /* ── Date input customizado ── */
        div[data-baseweb="input"] {{
            border: 2px solid {ORANGE} !important;
            border-radius: 8px !important;
        }}
        div[data-baseweb="input"]:focus-within {{
            box-shadow: 0 0 0 3px {ORANGE}40 !important;
        }}
        div[data-baseweb="input"] input {{
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: {DARK_TITLE} !important;
        }}
        label[data-testid="stWidgetLabel"] p {{
            font-size: .88rem !important;
            font-weight: 700 !important;
            color: {ORANGE} !important;
            text-transform: uppercase;
            letter-spacing: .04em;
        }}
        div[data-baseweb="calendar"] {{
            border: 2px solid {ORANGE} !important;
            border-radius: 10px !important;
        }}

        /* ── Download button ── */
        .stDownloadButton > button {{
            background: {ORANGE}; color: #fff; border: none;
            font-weight: 700; border-radius: 8px; padding: 8px 20px;
        }}
        .stDownloadButton > button:hover {{ background: {SUNSET}; color: #fff; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
