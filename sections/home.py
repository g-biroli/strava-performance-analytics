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
            f'<img src="{profile_url}" alt="Profile picture">'
            if profile_url
            else (
                f'<div style="width:120px;height:120px;border-radius:50%;background:{ORANGE}40;'
                f'margin:0 auto;display:flex;align-items:center;justify-content:center;font-size:2.5rem;">👤</div>'
            )
        )
        name = f"{athlete.get('firstname', 'Gabriel')} {athlete.get('lastname', 'Biroli')}"
        location = ", ".join(filter(None, [athlete.get("city", ""), athlete.get("country", "")]))
        location_html = (
            f'<div style="opacity:.6;font-size:.85rem;color:{GRAY_SECONDARY};">{location}</div>'
            if location else ""
        )
        st.markdown(
            f'<div class="profile-card" style="min-height:420px;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;">'
            f'{img_tag}'
            f'<div class="profile-name">{name}</div>'
            f'{location_html}'
            f'<hr style="width:80%;border-color:{ORANGE}30;margin:14px 0;">'
            f'<div class="profile-links">'
            f'<a href="https://www.linkedin.com/in/gabrielbiroli/" target="_blank">LinkedIn</a>'
            f'<a href="https://github.com/g-biroli" target="_blank">GitHub</a>'
            f'<a href="https://github.com/g-biroli/strava-performance-analytics" target="_blank">Repository</a>'
            f'</div>'
            f'<div class="strava-cta">'
            f'<a href="https://www.strava.com/athletes/134740757" target="_blank">Follow me on Strava 🏃‍♂️🏊‍♂️</a>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_text:
        st.markdown("### About This Project")
        st.markdown(
            """This is a personal and professional portfolio project built with real training data
            collected directly via the Strava API. The goal is to transform raw workout records —
            time, distance, heart rate, and pace — into actionable insights that continuously
            support athletic improvement, with a focus on endurance sports such as running and
            swimming.

            The application is fully scalable: new data is incorporated automatically with each
            API sync, and new sport types or metrics can be added to the data model without
            rewriting the pipeline."""
        )
        st.markdown(
            f'<div style="background:{CREAM};border-left:4px solid {ORANGE};border-radius:8px;'
            f'padding:14px 18px;margin:12px 0;">'
            f'<b style="color:{ORANGE};">📧 Automated PDF Report Pipeline</b><br>'
            f'<span style="font-size:.93rem;color:{DARK_TITLE};">'
            f'This project includes an <b>automated pipeline that delivers weekly performance '
            f'reports as PDF files directly to a personal email</b>. The goal is to continuously '
            f'monitor training metrics and refine athletic performance, directly supporting '
            f'<b>preparation for races and endurance challenges</b>.'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Tech Stack")
        cols = st.columns(5)
        stack = [
            ("https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg",
             "Python", "Core language"),
            ("https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg",
             "SQLite3", "Local database"),
            ("https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pandas/pandas-original.svg",
             "Pandas", "Data transformation"),
            ("https://images.plot.ly/logo/new-branding/plotly-logomark.png",
             "Plotly", "Interactive charts"),
            ("https://streamlit.io/images/brand/streamlit-mark-color.svg",
             "Streamlit", "Web interface"),
        ]
        for col, (logo_url, tech_name, desc) in zip(cols, stack):
            with col:
                st.markdown(
                    f'<div style="background:var(--secondary-background-color);border-radius:8px;'
                    f'padding:14px 10px;text-align:center;border-top:3px solid {ORANGE};'
                    f'box-shadow:0 1px 4px rgba(0,0,0,0.07);">'
                    f'<img src="{logo_url}" style="height:36px;object-fit:contain;margin-bottom:6px;">'
                    f'<div style="font-weight:700;font-size:.9rem;margin-top:2px;color:{DARK_TITLE};">{tech_name}</div>'
                    f'<div style="font-size:.75rem;opacity:.55;">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
