import streamlit as st

from utils.db import load_athlete
from utils.palette import CREAM, DARK_TITLE, GRAY_SECONDARY, ORANGE


def render_home() -> None:
    st.title("Strava Performance Analytics")

    athlete = load_athlete()
    col_profile, col_text = st.columns([1, 2.5], gap="large")

    with col_profile:
        profile_url = athlete.get("profile", "")
        img_tag = (
            f'<img src="{profile_url}" alt="Foto de perfil">'
            if profile_url
            else (
                f'<div style="width:120px;height:120px;border-radius:50%;background:{ORANGE}40;'
                f'margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:2.5rem;">👤</div>'
            )
        )
        name = f"{athlete.get('firstname', 'Gabriel')} {athlete.get('lastname', 'Biroli')}"
        location = ", ".join(filter(None, [athlete.get("city", ""), athlete.get("country", "")]))
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
            """Este é um projeto de portfólio pessoal e profissional desenvolvido com dados reais
            coletados diretamente via API do Strava. O objetivo é transformar registros brutos de
            treino — tempo, distância, frequência cardíaca e ritmo — em análises práticas que
            orientem o aprimoramento físico contínuo, com foco em esportes de endurance como
            corrida e natação.

            A aplicação é totalmente escalável: novos dados são incorporados automaticamente a
            cada sincronização com a API, e novas modalidades ou métricas podem ser adicionadas
            ao modelo de dados sem reescrita do pipeline."""
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
