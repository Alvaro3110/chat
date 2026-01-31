"""
Estilos CSS personalizados para o frontend Streamlit.
"""

CUSTOM_CSS = """
<style>
    /* Layout corporativo limpo */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a365d;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Login Container */
    .login-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 400px;
        margin: 0 auto;
    }

    /* User Info Bar */
    .user-info-bar {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        color: #4a5568;
    }

    /* Info Cards para seleção de grupo */
    .info-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .info-label {
        font-size: 0.75rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .info-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
    }

    /* Group Header - Cabeçalho contextual fixo */
    .group-header {
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .group-header-title {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }

    .group-code {
        background-color: rgba(255, 255, 255, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .group-name {
        font-size: 1.25rem;
        font-weight: 600;
    }

    .group-header-info {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
    }

    .header-info-item {
        display: flex;
        flex-direction: column;
    }

    .header-label {
        font-size: 0.7rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .header-value {
        font-size: 0.95rem;
        font-weight: 500;
    }

    /* Chat Title */
    .chat-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a365d;
        margin-bottom: 0.25rem;
    }

    .chat-subtitle {
        font-size: 0.9rem;
        color: #718096;
        margin-bottom: 1rem;
    }

    /* Theme Cards */
    .theme-card {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }

    .theme-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        border-color: #cbd5e0;
    }

    /* Chat Messages */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }

    .user-message {
        background-color: #ebf8ff;
        margin-left: 2rem;
    }

    .assistant-message {
        background-color: #f7fafc;
        margin-right: 2rem;
    }

    /* Execution Details */
    .execution-details {
        background-color: #fffaf0;
        border-left: 4px solid #ed8936;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 10px 10px 0;
    }

    /* Source Badges */
    .source-badge {
        display: inline-block;
        background-color: #e6fffa;
        color: #234e52;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }

    /* Plan Steps */
    .plan-step {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-left: 3px solid #3182ce;
        background-color: #f7fafc;
    }

    .plan-step.completed {
        border-left-color: #38a169;
        background-color: #f0fff4;
    }

    .plan-step.in-progress {
        border-left-color: #ed8936;
        background-color: #fffaf0;
    }

    /* Session Info */
    .session-info {
        font-size: 0.8rem;
        color: #718096;
        padding: 0.5rem;
        background-color: #f7fafc;
        border-radius: 5px;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        background-color: #f7fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
    }

    /* Sidebar Buttons */
    .sidebar .stButton > button {
        background-color: #f7fafc;
        color: #2d3748;
        border: 1px solid #e2e8f0;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
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

    /* Form Inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    .stTextInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 1px #3182ce;
    }

    /* Select Box */
    .stSelectbox > div > div {
        border-radius: 8px;
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
