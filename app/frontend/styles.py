"""
Estilos CSS personalizados para o frontend Streamlit.
"""

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }

    .theme-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .theme-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }

    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }

    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }

    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }

    .execution-details {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 10px 10px 0;
    }

    .source-badge {
        display: inline-block;
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }

    .plan-step {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-left: 3px solid #1f77b4;
        background-color: #f8f9fa;
    }

    .plan-step.completed {
        border-left-color: #4caf50;
        background-color: #e8f5e9;
    }

    .plan-step.in-progress {
        border-left-color: #ff9800;
        background-color: #fff3e0;
    }

    .session-info {
        font-size: 0.8rem;
        color: #666;
        padding: 0.5rem;
        background-color: #f0f0f0;
        border-radius: 5px;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    div[data-testid="stExpander"] {
        background-color: #fafafa;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }

    .stChatMessage {
        border-radius: 15px;
    }

    .sidebar .stButton > button {
        background-color: #f0f2f6;
        color: #333;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
"""


def apply_custom_styles():
    """Aplica estilos CSS personalizados."""
    import streamlit as st

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_theme_card(theme: str, description: str) -> str:
    """
    Renderiza um card de tema.

    Args:
        theme: Nome do tema
        description: Descrição do tema

    Returns:
        HTML do card
    """
    return f"""
    <div class="theme-card">
        <h3>{theme.capitalize()}</h3>
        <p>{description}</p>
    </div>
    """


def render_plan_step(step: dict, index: int) -> str:
    """
    Renderiza uma etapa do plano.

    Args:
        step: Dados da etapa
        index: Índice da etapa

    Returns:
        HTML da etapa
    """
    status_class = step.get("status", "pending")
    status_icon = {
        "completed": "✓",
        "in_progress": "⟳",
        "pending": "○",
    }.get(status_class, "○")

    return f"""
    <div class="plan-step {status_class}">
        <strong>{status_icon} Etapa {index + 1}:</strong> {step.get('agent', 'Unknown')}
        <br>
        <small>{step.get('task', '')}</small>
    </div>
    """


def render_source_badges(sources: list[str]) -> str:
    """
    Renderiza badges de fontes.

    Args:
        sources: Lista de fontes

    Returns:
        HTML dos badges
    """
    badges = "".join([
        f'<span class="source-badge">{source}</span>'
        for source in sources
    ])
    return f'<div class="sources-container">{badges}</div>'
