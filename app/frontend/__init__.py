"""Frontend Streamlit da plataforma."""

from app.frontend.pages import render_page
from app.frontend.styles import apply_custom_styles

__all__ = [
    "render_page",
    "apply_custom_styles",
]
