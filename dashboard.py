import streamlit as st

from sections.home import render_home
from sections.overview import render_overview
from sections.running import render_running
from sections.swimming import render_swimming
from sections.walking import render_walking
from utils.styles import inject_css

st.set_page_config(
    page_title="Strava Performance Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

tab_home, tab_overview, tab_run, tab_swim, tab_walk = st.tabs([
    "🏠 Início",
    "📊 Visão Geral",
    "🏃‍♂️ Corrida",
    "🏊‍♂️ Natação",
    "🥾 Caminhada",
])

with tab_home:
    render_home()

with tab_overview:
    render_overview()

with tab_run:
    render_running()

with tab_swim:
    render_swimming()

with tab_walk:
    render_walking()
