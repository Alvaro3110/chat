
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

    /* Group Selection Cards */
    .group-card-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        border-left: 5px solid #cbd5e0;
    }

    .group-card-container:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        border-color: #cbd5e0;
    }

    .group-card-selected {
        border: 1px solid #3182ce;
        border-left: 5px solid #3182ce;
        background-color: #f0f7ff;
        box-shadow: 0 0 0 1px #3182ce;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2d3748;
        margin: 0;
    }

    .card-badge {
        background-color: #edf2f7;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #4a5568;
    }

    .card-cnpj {
        font-size: 0.85rem;
        color: #718096;
        margin-bottom: 0.75rem;
    }

    .card-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .card-metric-item {
        display: flex;
        flex-direction: column;
    }

    .card-metric-label {
        font-size: 0.7rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    .card-metric-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #4a5568;
    }

    .rating-container {
        margin-top: 0.5rem;
    }

    .rating-stars {
        color: #ecc94b;
        font-size: 1rem;
    }

    .rating-bar-bg {
        background-color: #edf2f7;
        height: 6px;
        border-radius: 3px;
        width: 100%;
        margin-top: 4px;
    }

    .rating-bar-fill {
        background-color: #38a169;
        height: 100%;
        border-radius: 3px;
    }

    /* Executive Group Cards */
    .executive-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .executive-card:hover {
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
        transform: translateY(-3px);
        border-color: #a0aec0;
    }

    .executive-card-selected {
        border: 2px solid #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.2), 0 6px 16px rgba(0, 0, 0, 0.1);
        background-color: #e6f0fa;
    }

    .executive-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .executive-card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1a365d;
        margin: 0;
    }

    .executive-card-badge {
        background-color: #edf2f7;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #4a5568;
        text-transform: uppercase;
    }

    .executive-card-cnpj {
        font-size: 0.85rem;
        color: #718096;
        margin-bottom: 1rem;
    }

    .executive-card-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }

    .executive-card-metric-item {
        display: flex;
        flex-direction: column;
        background-color: #f7fafc;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    .executive-card-metric-label {
        font-size: 0.7rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .executive-card-metric-value {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3748;
    }

    .executive-card-rating-container {
        margin-top: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .executive-card-rating-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #4a5568;
    }

    .executive-card-rating-bar-bg {
        background-color: #edf2f7;
        height: 8px;
        border-radius: 4px;
        flex-grow: 1;
    }

    .executive-card-rating-bar-fill {
        background-color: #38a169;
        height: 100%;
        border-radius: 4px;
    }

    .executive-card-risk-indicator {
        position: absolute;
        top: 0;
        right: 0;
        background-color: #e53e3e;
        color: white;
        padding: 0.3rem 0.8rem;
        border-bottom-left-radius: 12px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .user-message-container {
        background-color: #e6f0fa;
        border-radius: 12px;
        padding: 1rem;
        margin-left: auto;
        max-width: 80%;
        text-align: right;
        position: relative;
    }

    .assistant-message-container {
        background-color: #f7fafc;
        border-radius: 12px;
        padding: 1rem;
        margin-right: auto;
        max-width: 80%;
        text-align: left;
        position: relative;
    }

    .message-timestamp {
        font-size: 0.7rem;
        color: #a0aec0;
        margin-top: 0.5rem;
        display: block;
    }

    /* AI Reasoning Panel - Refined */
    .ai-reasoning-panel {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .ai-reasoning-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #edf2f7;
    }

    .ai-reasoning-header-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        color: #4a5568;
        font-weight: 500;
    }

    .ai-reasoning-step-list {
        margin-top: 1rem;
    }

    .ai-reasoning-step {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .ai-reasoning-step-icon {
        font-size: 1rem;
        color: #3182ce;
        flex-shrink: 0;
    }

    .ai-reasoning-step-content {
        display: flex;
        flex-direction: column;
    }

    .ai-reasoning-step-title {
        font-weight: 600;
        color: #2d3748;
        font-size: 0.9rem;
    }

    .ai-reasoning-step-desc {
        color: #718096;
        font-size: 0.8rem;
        line-height: 1.3;
    }

    .ai-complexity-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    .ai-complexity-simples { background-color: #c6f6d5; color: #22543d; }
    .ai-complexity-complexa { background-color: #feebc8; color: #744210; }
    .ai-complexity-ambígua { background-color: #fed7d7; color: #822727; }

    .ai-time-metric {
        font-size: 0.85rem;
        color: #4a5568;
        font-weight: 500;
        margin-top: 1rem;
        text-align: right;
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