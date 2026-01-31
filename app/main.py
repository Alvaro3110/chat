"""
Script principal que inicia a aplicação Streamlit.
Configura os agentes e renderiza a interface.
"""

import streamlit as st
from dotenv import load_dotenv

from app.frontend.pages import render_page
from app.frontend.styles import apply_custom_styles

load_dotenv()

st.set_page_config(
    page_title="Plataforma Multiagente de IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()

render_page()
