import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Strava Performance Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Paleta oficial ───────────────────────────────────────────────────────────
ORANGE        = "#FC4C02"   # Laranja Strava — destaque principal
BLUE_DEPTH    = "#005C66"   # Azul Profundidade — métricas complementares
SWIM_DARK     = "#1A2E40"   # Azul Marinho Atlético — Natação principal
GREEN_OUTDOOR = "#3B6E4C"   # Verde Outdoor — Caminhada principal
PURPLE_UV     = "#4A154B"   # Roxo Ultravioleta — categorias menores
SUNSET        = "#FF763D"   # Laranja Pôr do Sol — metas/progresso
YELLOW_ENERGY = "#FFB800"   # Amarelo Energia — conquistas e pódios
CREAM         = "#FFF4ED"   # Creme Suave — fundo premium / corrida
DARK_TITLE    = "#242428"   # Cinza Asfalto Escuro — títulos
GRAY_SECONDARY = "#8E8E93"  # Cinza Neblina — rótulos secundários
GRAY_ICE      = "#F4F4F6"   # Cinza Gelo — estruturas e barras vazias

CHART_BG  = "rgba(0,0,0,0)"
GRID_COLOR = "#EBEBEB"

SPORT_COLORS = {
    "Run":           ORANGE,
    "TrailRun":      SUNSET,
    "Walk":          GREEN_OUTDOOR,
    "Swim":          SWIM_DARK,
    "OpenWaterSwim": BLUE_DEPTH,
    "Ride":          BLUE_DEPTH,
    "WeightTraining": PURPLE_UV,
    "Soccer":        YELLOW_ENERGY,
    "Workout":       GRAY_SECONDARY,
    "Racquetball":   "#80CBC4",
    "Tennis":        "#AED581",
    "RockClimbing":  "#BCAAA4",
    "Rowing":        "#4DD0E1",
}

HEATMAP_COLORSCALE = [
    [0.0,  "#F4F4F6"],
    [0.01, "#FFD5C2"],
    [0.4,  "#FF763D"],
    [1.0,  ORANGE],
]

# ─── CSS global ───────────────────────────────────────────────────────────────
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
    .kpi-card.swim   {{ border-left-color: {SWIM_DARK}; }}
    .kpi-card.walk   {{ border-left-color: {GREEN_OUTDOOR}; }}
    .kpi-label  {{ font-size:.78rem; opacity:.55; margin-bottom:2px;
                   text-transform:uppercase; letter-spacing:.05em; color:var(--text-color); }}
    .kpi-value  {{ font-size:1.65rem; font-weight:700; color:{ORANGE}; }}
    .kpi-card.swim .kpi-value {{ color:{SWIM_DARK}; }}
    .kpi-card.walk .kpi-value {{ color:{GREEN_OUTDOOR}; }}
    .kpi-sub    {{ font-size:.8rem; opacity:.5; color:var(--text-color); }}

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

# ─── DB connection ─────────────────────────────────────────────────────────────
DB_PATH = Path("data/strava.db")


@st.cache_resource
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ─── Loaders ──────────────────────────────────────────────────────────────────
def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    df["dist_km"]       = df["distance"] / 1000
    df["duration_min"]  = df["moving_time"] / 60
    df["duration_h"]    = df["moving_time"] / 3600
    df["speed_kmh"]     = np.where(df["moving_time"] > 0, df["distance"] / df["moving_time"] * 3.6, np.nan)
    df["pace_min_km"]   = np.where(
        (df["dist_km"] > 0) & (df["moving_time"] > 0),
        df["duration_min"] / df["dist_km"], np.nan,
    )
    df["month_str"]  = df["start_date_local"].dt.to_period("M").astype(str)
    df["week"]       = df["start_date_local"].dt.isocalendar().week.astype(int)
    df["dayofweek"]  = df["start_date_local"].dt.dayofweek
    df["date_only"]  = df["start_date_local"].dt.date
    df["year_week"]  = df["start_date_local"].dt.strftime("%Y-W%V")
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


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fmt_pace(p) -> str:
    if p is None or (isinstance(p, float) and (np.isnan(p) or p <= 0)):
        return "N/A"
    m = int(p); s = int(round((p - m) * 60))
    if s == 60: m += 1; s = 0
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
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=14, color=GRAY_SECONDARY))
    fig.update_layout(paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                      xaxis_visible=False, yaxis_visible=False, height=280)
    return fig


def apply_base_layout(fig: go.Figure, height: int = 340, title: str = "",
                      title_color: str = GRAY_SECONDARY) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14, color=title_color), x=0),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(family="sans-serif", color=GRAY_SECONDARY),
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def _stub_pdf(title: str) -> bytes:
    """Gera um PDF mínimo de placeholder usando apenas stdlib."""
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
    """Retorna (d_start, d_end). Exibe filtro + botão PDF lado a lado."""
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


def donut_goal(current: float, goal: float, label: str,
               color_fill: str = SUNSET, height: int = 260) -> go.Figure:
    pct = min(current / goal, 1.0) if goal > 0 else 0
    remaining = max(goal - current, 0)
    fig = go.Figure(go.Pie(
        values=[current, remaining],
        labels=["Realizado", "Restante"],
        hole=0.65,
        marker=dict(colors=[color_fill, GRAY_ICE],
                    line=dict(color="#ffffff", width=2)),
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


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_home, tab_overview, tab_run, tab_swim, tab_walk = st.tabs([
    "🏠 Início",
    "📊 Visão Geral",
    "🏃‍♂️ Corrida",
    "🏊‍♂️ Natação",
    "🥾 Caminhada",
])

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — INÍCIO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_home:
    st.title("Strava Performance Analytics")

    athlete = load_athlete()
    col_profile, col_text = st.columns([1, 2.5], gap="large")

    with col_profile:
        profile_url = athlete.get("profile", "")
        img_tag = (
            f'<img src="{profile_url}" alt="Foto de perfil">'
            if profile_url
            else f'<div style="width:120px;height:120px;border-radius:50%;background:{ORANGE}40;'
                 f'margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:2.5rem;">👤</div>'
        )
        name = f"{athlete.get('firstname','Gabriel')} {athlete.get('lastname','Biroli')}"
        location = ", ".join(filter(None, [athlete.get("city",""), athlete.get("country","")]))
        st.markdown(
            f"""<div class="profile-card" style="min-height:420px;display:flex;flex-direction:column;
                    align-items:center;justify-content:center;">
                {img_tag}
                <div class="profile-name">{name}</div>
                {'<div style="opacity:.6;font-size:.85rem;color:' + GRAY_SECONDARY + ';">' + location + '</div>' if location else ''}
                <hr style="width:80%;border-color:{ORANGE}30;margin:14px 0;">
                <div class="profile-links">
                    <a href="https://www.linkedin.com/in/gabrielbiroli/" target="_blank">LinkedIn</a>
                    <a href="https://github.com/g-biroli" target="_blank">GitHub</a>
                    <a href="https://github.com/g-biroli/strava-performance-analytics" target="_blank">Repositório</a>
                </div>
                <div class="strava-cta">
                    <a href="https://www.strava.com/athletes/134740757" target="_blank">Siga-me no Strava 🏃‍♂️🏊‍♂️</a>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col_text:
        st.markdown("### Sobre o Projeto")
        st.markdown(
            f"""Este é um projeto de portfólio pessoal e profissional desenvolvido com dados reais
            coletados diretamente via API do Strava. O objetivo é transformar registros brutos de
            treino — tempo, distância, frequência cardíaca e ritmo — em análises práticas que
            orientem o aprimoramento físico contínuo, com foco em esportes de endurance como
            corrida e natação.

            A aplicação é totalmente escalável: novos dados são incorporados automaticamente a
            cada sincronização com a API, e novas modalidades ou métricas podem ser adicionadas
            ao modelo de dados sem reescrita do pipeline.
            """
        )
        st.markdown(
            f"""<div style="background:{CREAM};border-left:4px solid {ORANGE};border-radius:8px;
                    padding:14px 18px;margin:12px 0;">
                <b style="color:{ORANGE};">📧 Pipeline Automatizado de Relatórios</b><br>
                <span style="font-size:.93rem;color:{DARK_TITLE};">
                O projeto conta com uma <b>automatização de pipeline que envia relatórios de performance
                em PDF semanalmente para o e-mail pessoal</b>. O objetivo é monitorar métricas de forma
                contínua e aperfeiçoar a prática esportiva, impactando diretamente a
                <b>preparação para provas e desafios de endurance</b>.
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("### Stack Técnica")
        cols = st.columns(5)
        stack = [
            (
                "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg",
                "Python", "Linguagem principal",
            ),
            (
                "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg",
                "SQLite3", "Banco relacional local",
            ),
            (
                "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pandas/pandas-original.svg",
                "Pandas", "Transformação de dados",
            ),
            (
                "https://images.plot.ly/logo/new-branding/plotly-logomark.png",
                "Plotly", "Visualizações interativas",
            ),
            (
                "https://streamlit.io/images/brand/streamlit-mark-color.svg",
                "Streamlit", "Interface web",
            ),
        ]
        for col, (logo_url, tech_name, desc) in zip(cols, stack):
            with col:
                st.markdown(
                    f"""<div style="background:var(--secondary-background-color);border-radius:8px;
                        padding:14px 10px;text-align:center;border-top:3px solid {ORANGE};
                        box-shadow:0 1px 4px rgba(0,0,0,0.07);">
                        <img src="{logo_url}" style="height:36px;object-fit:contain;margin-bottom:6px;">
                        <div style="font-weight:700;font-size:.9rem;margin-top:2px;color:{DARK_TITLE};">{tech_name}</div>
                        <div style="font-size:.75rem;opacity:.55;">{desc}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — VISÃO GERAL
# ═══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # Banner
    st.markdown(
        f"""<div style="background:#fff;border-radius:12px;padding:20px 28px;
                margin-bottom:18px;border-bottom:4px solid {ORANGE};">
            <h2 style="color:{ORANGE};margin:0;">📊 Visão Geral de Performance</h2>
            <p style="color:{GRAY_SECONDARY};margin:4px 0 0;font-size:.9rem;">
            Panorama completo de todas as modalidades e períodos</p>
        </div>""",
        unsafe_allow_html=True,
    )

    d_start, d_end = date_filter_with_download("overview", 365, "Visão Geral")
    df_all = load_all_activities(d_start, d_end)

    if df_all.empty:
        st.warning("Nenhuma atividade encontrada no período selecionado.")
        st.stop()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    gps_types = ["Run", "TrailRun", "Swim", "OpenWaterSwim", "Ride", "Walk", "Rowing"]
    df_gps    = df_all[df_all["sport_type"].isin(gps_types)]
    total_km  = df_gps["dist_km"].sum()
    total_acts = len(df_all)
    total_h   = df_all["duration_h"].sum()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("Total de Atividades", str(total_acts), "no período selecionado")
    with k2:
        kpi("Quilômetros Acumulados", f"{total_km:,.1f} km", "todas as modalidades GPS")
    with k3:
        kpi("Horas de Movimento", f"{total_h:,.0f} h", "tempo movendo-se")
    with k4:
        avg_hr = df_all["average_heartrate"].dropna()
        kpi("FC Média Histórica",
            f"{avg_hr.mean():.0f} bpm" if not avg_hr.empty else "N/A",
            f"em {avg_hr.count()} atividades c/ HR")

    st.divider()

    # ── Top 3 modalidades ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Top 3 Modalidades</div>', unsafe_allow_html=True)
    top3 = (
        df_all.groupby("sport_type").agg(n=("id", "count"))
        .reset_index().sort_values("n", ascending=False).head(3)
    )
    if not top3.empty:
        top3 = top3.sort_values("n", ascending=True)  # horizontal: maior fica em cima
        fig_top3 = go.Figure(go.Bar(
            x=top3["n"], y=top3["sport_type"],
            orientation="h",
            marker_color=[SPORT_COLORS.get(s, GRAY_SECONDARY) for s in top3["sport_type"]],
            text=top3["n"].astype(str) + " treinos",
            textposition="inside",
            textfont=dict(color="#fff", size=13, family="sans-serif"),
            hovertemplate="%{y}: %{x} treinos<extra></extra>",
        ))
        apply_base_layout(fig_top3, height=200)
        st.plotly_chart(fig_top3, use_container_width=True)

    st.divider()

    # ── Metas semanais gerais ─────────────────────────────────────────────────
    st.markdown('<div class="section-title">Metas da Semana Atual</div>', unsafe_allow_html=True)
    today_ts = pd.Timestamp.today()
    week_str = today_ts.strftime("%Y-W%V")
    df_week  = df_all[df_all["year_week"] == week_str] if "year_week" in df_all.columns else pd.DataFrame()

    week_h    = df_week["duration_h"].sum() if not df_week.empty else 0.0
    week_acts = len(df_week) if not df_week.empty else 0

    m1, m2 = st.columns(2, gap="large")
    with m1:
        st.markdown(f"**Meta de Tempo — 5h semanais** ({week_h:.1f}h realizadas)")
        fig_t = donut_goal(week_h, 5.0, "horas / 5h", color_fill=ORANGE, height=220)
        st.plotly_chart(fig_t, use_container_width=True)
    with m2:
        st.markdown(f"**Meta de Frequência — 5 atividades** ({week_acts} realizadas)")
        fig_f = donut_goal(float(week_acts), 5.0, "atividades / 5", color_fill=SUNSET, height=220)
        st.plotly_chart(fig_f, use_container_width=True)

    st.divider()

    col_heatmap, col_donut = st.columns([3, 1.4], gap="large")

    # ── Calendário de atividades ───────────────────────────────────────────────
    with col_heatmap:
        st.markdown('<div class="section-title">Calendário de Atividades</div>', unsafe_allow_html=True)
        daily = (
            df_all.groupby("date_only")
            .agg(count=("id", "count"), km=("dist_km", "sum"))
            .reset_index()
        )
        daily["date"]     = pd.to_datetime(daily["date_only"])
        daily["date_only"] = daily["date_only"]
        idx  = pd.date_range(d_start, d_end, freq="D")
        grid = pd.DataFrame({"date": idx})
        grid["week_num"]  = grid["date"].dt.isocalendar().week.astype(int)
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
        grid_pivot = grid.pivot_table(index="dayofweek", columns="week_cat",
                                      values="count", aggfunc="sum").fillna(0)
        day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        fig_heat = go.Figure(go.Heatmap(
            z=grid_pivot.values,
            x=list(grid_pivot.columns),
            y=[day_names[i] for i in grid_pivot.index],
            colorscale=HEATMAP_COLORSCALE,
            showscale=False,
            hovertemplate="Semana: %{x}<br>Dia: %{y}<br>Treinos: %{z}<extra></extra>",
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

    # ── Donut mix ─────────────────────────────────────────────────────────────
    with col_donut:
        st.markdown('<div class="section-title">Mix de Modalidades</div>', unsafe_allow_html=True)
        mix = df_all.groupby("sport_type").agg(n=("id", "count")).reset_index().sort_values("n", ascending=False)
        colors_donut = [SPORT_COLORS.get(s, GRAY_SECONDARY) for s in mix["sport_type"]]
        fig_donut = go.Figure(go.Pie(
            labels=mix["sport_type"], values=mix["n"], hole=0.55,
            marker=dict(colors=colors_donut, line=dict(color="#ffffff", width=2)),
            textinfo="percent", textposition="inside",
            hovertemplate="%{label}: %{value} treinos (%{percent})<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{total_acts}</b><br><span style='font-size:10px'>treinos</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=ORANGE),
        )
        fig_donut.update_layout(
            height=260, showlegend=True,
            legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor=CHART_BG, margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # ── Volume mensal por modalidade ───────────────────────────────────────────
    st.markdown('<div class="section-title">Volume Mensal por Modalidade (horas)</div>', unsafe_allow_html=True)
    all_types = list(SPORT_COLORS.keys())
    vol_m = (
        df_all[df_all["sport_type"].isin(all_types)]
        .groupby(["month_str", "sport_type"])["duration_h"]
        .sum().reset_index().sort_values("month_str")
    )
    if not vol_m.empty:
        THRESHOLD = 0.3  # horas — abaixo disso oculta rótulo interno
        vol_m["text_label"] = vol_m["duration_h"].apply(
            lambda v: f"{v:.1f}h" if v >= THRESHOLD else ""
        )
        fig_bar_vol = px.bar(
            vol_m, x="month_str", y="duration_h", color="sport_type",
            color_discrete_map=SPORT_COLORS,
            text="text_label",
            labels={"month_str": "", "duration_h": "Horas", "sport_type": ""},
        )
        fig_bar_vol.update_traces(textposition="inside", textfont_size=9)
        fig_bar_vol.update_xaxes(categoryorder="category ascending", tickangle=-30)
        apply_base_layout(fig_bar_vol, height=340)
        st.plotly_chart(fig_bar_vol, use_container_width=True)
    else:
        st.plotly_chart(empty_fig(), use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CORRIDA
# ═══════════════════════════════════════════════════════════════════════════════
with tab_run:
    # Banner
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
    else:
        df_5k  = df_run[df_run["distance"].between(4900, 5500)].copy()
        df_10k = df_run[df_run["distance"].between(9800, 10500)].copy()

        # ── KPIs ──────────────────────────────────────────────────────────────
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
            kpi("Volume Total", f"{df_run['dist_km'].sum():,.1f} km",
                f"{len(df_run)} sessões de corrida")
        with k5:
            hr_run = df_run["average_heartrate"].dropna()
            kpi("FC Média Corrida",
                f"{hr_run.mean():.0f} bpm" if not hr_run.empty else "N/A",
                f"em {len(hr_run)} corridas c/ HR")

        st.divider()

        # ── Metas de corrida (donut) ───────────────────────────────────────────
        st.markdown('<div class="section-title">Meta Semanal de Corrida</div>', unsafe_allow_html=True)
        today_ts  = pd.Timestamp.today()
        week_str_r = today_ts.strftime("%Y-W%V")
        df_week_r  = df_run[df_run["year_week"] == week_str_r] if "year_week" in df_run.columns else pd.DataFrame()
        week_km_r  = df_week_r["dist_km"].sum() if not df_week_r.empty else 0.0

        mc1, mc2 = st.columns([1, 2], gap="large")
        with mc1:
            st.markdown(f"**Meta: 5 km acumulados na semana** ({week_km_r:.1f} km realizados)")
            fig_goal_r = donut_goal(week_km_r, 5.0, "km / 5km", color_fill=SUNSET, height=240)
            st.plotly_chart(fig_goal_r, use_container_width=True)

        # ── Turismo esportivo ──────────────────────────────────────────────────
        with mc2:
            st.markdown('<div class="section-title">Turismo Esportivo</div>', unsafe_allow_html=True)
            sp_keywords = ["são paulo", "sao paulo", "sp", "São Paulo"]

            def is_outside_sp(row):
                name_ = str(row.get("name", "") or "").lower()
                return not any(k in name_ for k in sp_keywords)

            outside_sp = df_run.apply(is_outside_sp, axis=1)
            n_outside  = int(outside_sp.sum())
            km_outside = df_run.loc[outside_sp, "dist_km"].sum()
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

        # ── Evolução de pace ───────────────────────────────────────────────────
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

        # ── Volume mensal de corrida ───────────────────────────────────────────
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
                textposition="inside",
                textfont=dict(color="#fff", size=10),
                hovertemplate="Mês: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
            ))
            fig_vol_r.update_xaxes(tickangle=-30, categoryorder="total descending")
            fig_vol_r.update_yaxes(title_text="km")
            apply_base_layout(fig_vol_r, height=300, title="km de Corrida por Mês")
            st.plotly_chart(fig_vol_r, use_container_width=True)
        else:
            st.plotly_chart(empty_fig(), use_container_width=True)

        # ── Zonas de FC ────────────────────────────────────────────────────────
        st.markdown('<div class="section-title">Distribuição de Frequência Cardíaca (Corrida)</div>',
                    unsafe_allow_html=True)
        df_run_hr = df_run.dropna(subset=["average_heartrate"]).copy()
        if not df_run_hr.empty:
            FC_MAX = 195
            bins     = [0, 0.60*FC_MAX, 0.70*FC_MAX, 0.80*FC_MAX, 0.90*FC_MAX, FC_MAX+50]
            labels_z = ["Z1 — Recuperação","Z2 — Base Aeróbica","Z3 — Tempo","Z4 — Limiar","Z5 — VO2max"]
            colors_z = ["#4CAF50","#8BC34A",ORANGE,"#FF5722","#B71C1C"]
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
            apply_base_layout(fig_zones, height=300,
                               title=f"Zonas de FC por Sessão (FCmax ref: {FC_MAX} bpm)")
            st.plotly_chart(fig_zones, use_container_width=True)
            st.caption("Zonas calculadas sobre a FC média da atividade. Ajuste `FC_MAX` para calibrar ao seu perfil.")
        else:
            st.info("Sem dados de frequência cardíaca nas corridas do período.")

        # ── Evolução mensal pace 5k ────────────────────────────────────────────
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

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — NATAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_swim:
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,{SWIM_DARK} 0%,#001F3F 100%);
                border-radius:12px;padding:22px 28px;margin-bottom:18px;
                border-left:5px solid {ORANGE};">
            <h2 style="color:#fff;margin:0;">🏊‍♂️ Performance em Natação</h2>
            <p style="color:#8EC8E8;margin:4px 0 0;font-size:.9rem;">
            Análise de ritmo e volume na piscina</p>
        </div>""",
        unsafe_allow_html=True,
    )

    d_start_s, d_end_s = date_filter_with_download("swim", 500, "Relatório de Natação")
    df_all_s = load_all_activities(d_start_s, d_end_s)

    swim_types = ["Swim", "OpenWaterSwim"]
    df_swim = df_all_s[df_all_s["sport_type"].isin(swim_types)].copy()

    if not df_swim.empty:
        df_swim["pace_100m"] = np.where(
            (df_swim["distance"] > 0) & (df_swim["moving_time"] > 0),
            (df_swim["moving_time"] / 60) / (df_swim["distance"] / 100), np.nan,
        )
        df_swim = df_swim[df_swim["pace_100m"].between(0.8, 10.0)]

    df_1k_swim = df_swim[df_swim["distance"].between(900, 1100)]  if not df_swim.empty else pd.DataFrame()
    df_2k_swim = df_swim[df_swim["distance"].between(1900, 2100)] if not df_swim.empty else pd.DataFrame()

    SWIM_MID = "#2A6496"  # tom intermediário para elementos secundários

    if df_swim.empty:
        st.warning("Sem dados de natação para o período selecionado.")
    else:
        # ── KPIs ──────────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            pr_1k = df_1k_swim["pace_100m"].min() if not df_1k_swim.empty else None
            kpi("PR Pace — 1 km", (fmt_pace(pr_1k)+"/100m") if pr_1k else "N/A",
                f"{len(df_1k_swim)} sessões ~1000m", swim=True)
        with k2:
            avg_1k = df_1k_swim["pace_100m"].mean() if not df_1k_swim.empty else None
            kpi("Pace Médio — 1 km", (fmt_pace(avg_1k)+"/100m") if avg_1k else "N/A", swim=True)
        with k3:
            pr_2k = df_2k_swim["pace_100m"].min() if not df_2k_swim.empty else None
            kpi("PR Pace — 2 km", (fmt_pace(pr_2k)+"/100m") if pr_2k else "N/A",
                f"{len(df_2k_swim)} sessões ~2000m", swim=True)
        with k4:
            kpi("Volume Total Nadado", f"{df_swim['dist_km'].sum():,.1f} km",
                f"{len(df_swim)} sessões", swim=True)

        st.divider()

        # ── Meta semanal natação ───────────────────────────────────────────────
        st.markdown('<div class="section-title swim">Meta Semanal de Natação</div>', unsafe_allow_html=True)
        today_ts_s  = pd.Timestamp.today()
        week_str_s  = today_ts_s.strftime("%Y-W%V")
        df_week_s   = df_swim[df_swim["year_week"] == week_str_s] if "year_week" in df_swim.columns else pd.DataFrame()
        week_km_s   = df_week_s["dist_km"].sum() if not df_week_s.empty else 0.0

        sc1, sc2 = st.columns([1, 2])
        with sc1:
            st.markdown(f"**Meta: 2 km nadados na semana** ({week_km_s:.2f} km realizados)")
            fig_goal_s = donut_goal(week_km_s, 2.0, "km / 2km", color_fill=SWIM_DARK, height=240)
            st.plotly_chart(fig_goal_s, use_container_width=True)

        st.divider()

        # ── Evolução volume e pace ─────────────────────────────────────────────
        st.markdown('<div class="section-title swim">Evolução de Volume e Ritmo</div>', unsafe_allow_html=True)
        swim_m = (
            df_swim.groupby("month_str")
            .agg(dist_km=("dist_km","sum"), pace_med=("pace_100m","mean"), n=("id","count"))
            .reset_index().sort_values("month_str")
        )
        fig_swim_ev = go.Figure()
        fig_swim_ev.add_trace(go.Bar(
            x=swim_m["month_str"], y=swim_m["dist_km"], name="Volume (km)",
            marker_color=SWIM_DARK, opacity=0.85,
            text=swim_m["dist_km"].apply(lambda v: f"{v:.1f}"),
            textposition="inside", textfont=dict(color="#fff", size=10),
            hovertemplate="Mês: %{x}<br>Volume: %{y:.2f} km<extra></extra>",
            yaxis="y",
        ))
        fig_swim_ev.add_trace(go.Scatter(
            x=swim_m["month_str"], y=swim_m["pace_med"], name="Pace Médio /100m",
            mode="lines+markers+text",
            line=dict(color=ORANGE, width=2.5), marker=dict(size=8, color=ORANGE),
            text=swim_m["pace_med"].apply(fmt_pace),
            textposition="top center", textfont=dict(size=9, color=ORANGE),
            hovertemplate="Mês: %{x}<br>Pace: %{text}/100m<extra></extra>",
            yaxis="y2",
        ))
        fig_swim_ev.update_layout(
            yaxis=dict(title="Volume (km)", gridcolor="rgba(26,46,64,0.12)", color=SWIM_DARK),
            yaxis2=dict(title="Pace (min/100m)", overlaying="y", side="right",
                        autorange="reversed", gridcolor="rgba(0,0,0,0)", color=ORANGE),
            xaxis=dict(tickangle=-30, categoryorder="category ascending"),
            height=360, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=dict(color=GRAY_SECONDARY, family="sans-serif"),
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
            title=dict(text="Volume Mensal vs. Pace Médio", font=dict(size=13, color=SWIM_DARK), x=0),
        )
        st.plotly_chart(fig_swim_ev, use_container_width=True)

        # ── Frequência e Pace por distância ───────────────────────────────────
        col_freq, col_pace_dist = st.columns([1, 1.4], gap="large")

        with col_freq:
            st.markdown('<div class="section-title swim">Frequência de Treinos na Piscina</div>',
                        unsafe_allow_html=True)
            freq_m = swim_m[["month_str","n"]].copy()
            fig_freq = go.Figure(go.Bar(
                x=freq_m["month_str"], y=freq_m["n"],
                marker_color=SWIM_DARK,
                text=freq_m["n"], textposition="inside",
                textfont=dict(color="#fff", size=11),
                hovertemplate="Mês: %{x}<br>Treinos: %{y}<extra></extra>",
            ))
            avg_n = freq_m["n"].mean()
            fig_freq.add_hline(y=avg_n, line_dash="dot", line_color=ORANGE,
                                annotation_text=f"Média: {avg_n:.1f}/mês",
                                annotation_position="top right",
                                annotation_font=dict(size=10, color=ORANGE))
            fig_freq.update_xaxes(tickangle=-30, categoryorder="category ascending")
            fig_freq.update_yaxes(title_text="Sessões")
            fig_freq.update_layout(
                height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                font=dict(color=GRAY_SECONDARY), margin=dict(l=10,r=10,t=10,b=30),
            )
            st.plotly_chart(fig_freq, use_container_width=True)

        with col_pace_dist:
            st.markdown('<div class="section-title swim">Pace por Distância Nadada</div>',
                        unsafe_allow_html=True)
            fig_scatter_s = go.Figure()
            fig_scatter_s.add_trace(go.Scatter(
                x=df_swim["dist_km"]*1000, y=df_swim["pace_100m"],
                mode="markers+text",
                marker=dict(size=10, color=SWIM_MID, opacity=0.75,
                            line=dict(color=SWIM_DARK, width=1)),
                text=df_swim["pace_100m"].apply(fmt_pace),
                textposition="top center", textfont=dict(size=7, color=SWIM_DARK),
                hovertemplate="Data: %{customdata}<br>Dist: %{x:.0f} m<br>Pace: %{text}/100m<extra></extra>",
                customdata=df_swim["start_date_local"].dt.strftime("%d/%m/%Y"),
            ))
            fig_scatter_s.add_hline(y=2.0, line_dash="dash", line_color=ORANGE,
                                     annotation_text="Ref.: 2:00/100m",
                                     annotation_position="bottom right",
                                     annotation_font=dict(size=9, color=ORANGE))
            fig_scatter_s.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
            fig_scatter_s.update_xaxes(title_text="Distância (m)")
            fig_scatter_s.update_layout(
                height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                font=dict(color=GRAY_SECONDARY), margin=dict(l=10,r=10,t=10,b=30),
            )
            st.plotly_chart(fig_scatter_s, use_container_width=True)

        # ── Evolução pace 1km ──────────────────────────────────────────────────
        if not df_1k_swim.empty:
            st.markdown('<div class="section-title swim">Evolução do Pace — Sessões ~1000m</div>',
                        unsafe_allow_html=True)
            ds_1k = df_1k_swim.sort_values("start_date_local")
            fig_pace_1k = go.Figure()
            if len(ds_1k) >= 3:
                x_num = np.arange(len(ds_1k))
                z = np.polyfit(x_num, ds_1k["pace_100m"].values, 1)
                fig_pace_1k.add_trace(go.Scatter(
                    x=ds_1k["start_date_local"], y=np.poly1d(z)(x_num),
                    mode="lines", name="Tendência",
                    line=dict(color=ORANGE, width=1.5, dash="dot"),
                ))
            fig_pace_1k.add_trace(go.Scatter(
                x=ds_1k["start_date_local"], y=ds_1k["pace_100m"],
                mode="markers+lines", name="Pace Real",
                line=dict(color=SWIM_DARK, width=1.5),
                marker=dict(size=8, color=SWIM_DARK, line=dict(color=ORANGE, width=1.5)),
                text=ds_1k["pace_100m"].apply(fmt_pace),
                textposition="top center", textfont=dict(size=8, color=SWIM_DARK),
                hovertemplate="Data: %{x|%d/%m/%Y}<br>Pace: %{text}/100m<extra></extra>",
            ))
            fig_pace_1k.update_yaxes(autorange="reversed", title_text="Pace (min/100m)", tickformat=".2f")
            fig_pace_1k.update_layout(
                height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                font=dict(color=GRAY_SECONDARY),
                margin=dict(l=10,r=10,t=10,b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
            )
            fig_pace_1k.update_xaxes(gridcolor="rgba(26,46,64,0.12)")
            fig_pace_1k.update_yaxes(gridcolor="rgba(26,46,64,0.12)")
            st.plotly_chart(fig_pace_1k, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — CAMINHADA (NOVA)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_walk:
    # Banner
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,{GREEN_OUTDOOR} 0%,#1E3D2A 100%);
                border-radius:12px;padding:22px 28px;margin-bottom:18px;
                border-left:5px solid {ORANGE};">
            <h2 style="color:#fff;margin:0;">🥾 Performance em Caminhada</h2>
            <p style="color:#A8D5B5;margin:4px 0 0;font-size:.9rem;">
            Trilhas, caminhadas urbanas e turismo ativo</p>
        </div>""",
        unsafe_allow_html=True,
    )

    d_start_w, d_end_w = date_filter_with_download("walk", 500, "Relatório de Caminhada")
    df_all_w = load_all_activities(d_start_w, d_end_w)

    walk_types = ["Walk", "Hike"]
    df_walk = df_all_w[df_all_w["sport_type"].isin(walk_types)].copy()

    if df_walk.empty:
        st.warning("Sem dados de caminhada para o período selecionado.")
    else:
        # ── KPIs ──────────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi("Total de Saídas", str(len(df_walk)), "sessões de caminhada", walk=True)
        with k2:
            kpi("Distância Total", f"{df_walk['dist_km'].sum():,.1f} km",
                "acumulado no período", walk=True)
        with k3:
            kpi("Horas Caminhando", f"{df_walk['duration_h'].sum():,.0f} h",
                "tempo em movimento", walk=True)
        with k4:
            elev = df_walk["total_elevation_gain"].dropna().sum()
            kpi("Ganho de Elevação", f"{elev:,.0f} m",
                "total acumulado", walk=True)

        st.divider()

        # ── Meta semanal caminhada ─────────────────────────────────────────────
        st.markdown('<div class="section-title walk">Meta Semanal de Caminhada</div>', unsafe_allow_html=True)
        today_ts_w = pd.Timestamp.today()
        week_str_w = today_ts_w.strftime("%Y-W%V")
        df_week_w  = df_walk[df_walk["year_week"] == week_str_w] if "year_week" in df_walk.columns else pd.DataFrame()
        week_km_w  = df_week_w["dist_km"].sum() if not df_week_w.empty else 0.0

        wc1, wc2 = st.columns([1, 2])
        with wc1:
            WALK_GOAL_KM = 15.0
            st.markdown(f"**Meta: {WALK_GOAL_KM:.0f} km na semana** ({week_km_w:.1f} km realizados)")
            fig_goal_w = donut_goal(week_km_w, WALK_GOAL_KM, f"km / {WALK_GOAL_KM:.0f}km",
                                     color_fill=GREEN_OUTDOOR, height=240)
            st.plotly_chart(fig_goal_w, use_container_width=True)

        with wc2:
            # Turismo esportivo caminhada
            st.markdown('<div class="section-title walk">Turismo de Caminhada</div>', unsafe_allow_html=True)
            sp_keywords_w = ["são paulo", "sao paulo", "sp", "São Paulo"]

            def is_outside_sp_w(row):
                name_ = str(row.get("name", "") or "").lower()
                return not any(k in name_ for k in sp_keywords_w)

            outside_sp_w  = df_walk.apply(is_outside_sp_w, axis=1)
            n_outside_w   = int(outside_sp_w.sum())
            km_outside_w  = df_walk.loc[outside_sp_w, "dist_km"].sum()
            st.markdown(
                f"""<div style="background:#F0F7F3;border-left:4px solid {GREEN_OUTDOOR};
                        border-radius:8px;padding:16px 20px;margin-top:10px;">
                    <div style="font-size:.8rem;text-transform:uppercase;
                         color:{GRAY_SECONDARY};letter-spacing:.05em;">Caminhadas fora de São Paulo</div>
                    <div style="font-size:2rem;font-weight:700;color:{GREEN_OUTDOOR};">{n_outside_w}</div>
                    <div style="font-size:.9rem;color:{GRAY_SECONDARY};">
                    {km_outside_w:.1f} km explorados em trilhas e outras localidades</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Volumetria mensal (decrescente) ────────────────────────────────────
        st.markdown('<div class="section-title walk">Volumetria Mensal (km)</div>', unsafe_allow_html=True)
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
                hovertemplate="Mês: %{x}<br>Volume: %{y:.1f} km<extra></extra>",
            ))
            fig_vol_w.update_xaxes(tickangle=-30, categoryorder="total descending")
            fig_vol_w.update_yaxes(title_text="km")
            apply_base_layout(fig_vol_w, height=320,
                               title="km de Caminhada por Mês (ordem decrescente)",
                               title_color=GREEN_OUTDOOR)
            st.plotly_chart(fig_vol_w, use_container_width=True)
        else:
            st.plotly_chart(empty_fig("Sem volume de caminhada para o período."), use_container_width=True)
