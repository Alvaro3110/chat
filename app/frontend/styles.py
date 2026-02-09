"""
Estilos CSS personalizados para o frontend Streamlit.
"""

CUSTOM_CSS = """
<style>
    /* Global Streamlit adjustments */
    .stApp {
        background-color: #f0f2f6;
        color: #2d3748;
        font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    }

    /* Hide Streamlit default header and footer */
    header, footer {
        visibility: hidden;
        height: 0;
    }

    /* Main content area padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Login Page Centralization */
    .login-page-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh; /* Full viewport height */
        width: 100%;
        position: fixed;
        top: 0;
        left: 0;
        background-color: #f0f2f6; /* Light background for the page */
    }

    .login-container {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 3rem 2.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        max-width: 450px;
        width: 90%;
        text-align: center;
        animation: fadeIn 0.5s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .login-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.5rem;
    }

    .login-subtitle {
        font-size: 1rem;
        color: #718096;
        margin-bottom: 2rem;
    }

    /* Form Inputs - Refined */
    .stTextInput > label {
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        display: block;
        text-align: left;
    }

    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #cbd5e0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        color: #2d3748;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.2);
        outline: none;
    }

    .stButton > button {
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        background-color: #3182ce;
        color: white;
        border: none;
    }

    .stButton > button:hover {
        background-color: #2c5282;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    .stSelectbox > div > div {
        border-radius: 10px;
        border: 1px solid #cbd5e0;
        transition: all 0.2s ease;
    }

    .stSelectbox > div > div:hover {
        border-color: #a0aec0;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.2);
        outline: none;
    }


    .selection-toolbar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0 1rem 0;
        color: #475569;
        font-size: 0.92rem;
    }

    div[data-testid="stChatInput"] {
        border-top: 1px solid #e2e8f0;
        padding-top: 0.75rem;
        margin-top: 1rem;
        background: linear-gradient(180deg, rgba(240,242,246,0.2) 0%, rgba(240,242,246,0.9) 55%, rgba(240,242,246,1) 100%);
    }

    div[data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid #cbd5e0 !important;
        background-color: #ffffff !important;
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

    /* Group Header - Cabeçalho contextual fixo (Enterprise Grade) */
    .group-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #1a365d;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    .group-header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f1f5f9;
    }

    .group-code {
        background-color: #1a365d;
        color: #ffffff;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.025em;
    }

    .group-name {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a365d;
    }

    .group-header-info {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1.25rem;
    }

    .header-info-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .header-label {
        font-size: 0.65rem;
        color: #94a3b8;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    .header-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #334155;
    }

    /* Loading / Progress Indicator - Usando st.status nativo */
    .stStatusWidget {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    /* Chat Message Blocks */
    .chat-message-user {
        background-color: #e6f0fa;
        border-radius: 12px;
        padding: 1rem;
        margin-left: auto; /* Alinha à direita */
        max-width: 85%;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border-bottom-right-radius: 2px;
    }



    .thought-trace {
        background: #f8fafc;
        border: 1px solid #dbeafe;
        border-left: 4px solid #3b82f6;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0 0.75rem 0;
    }

    .thought-trace p {
        margin-bottom: 0.4rem;
        color: #1e3a8a;
    }

    .chat-message-ai {
        background-color: #f7fafc;
        border-radius: 12px;
        padding: 1rem;
        margin-right: auto; /* Alinha à esquerda */
        max-width: 85%;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-bottom-left-radius: 2px;
    }

    .chat-message-timestamp {
        font-size: 0.75rem;
        color: #a0aec0;
        margin-top: 0.5rem;
        display: block;
        text-align: right;
    }

    .chat-message-ai .chat-message-timestamp {
        text-align: left;
    }

    .ai-response-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #edf2f7;
    }

    .ai-response-category-badge {
        background-color: #e0f2fe; /* Light blue */
        color: #0c4a6e; /* Darker blue */
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .ai-response-time {
        font-size: 0.75rem;
        color: #718096;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }

    .ai-response-agents {
        font-size: 0.75rem;
        color: #718096;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }

    .ai-response-content {
        font-size: 1rem;
        line-height: 1.6;
        color: #2d3748;
        margin-bottom: 1rem;
    }

    .ai-reasoning-expander .stExpanderDetails {
        background-color: #fdfdfd;
        border-top: 1px solid #edf2f7;
        padding-top: 1rem;
    }

    .ai-complexity-simples { background-color: #c6f6d5; color: #22543d; }
    .ai-complexity-complexa { background-color: #feebc8; color: #744210; }
    .ai-complexity-ambígua { background-color: #fed7d7; color: #822727; }

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

    /* General Streamlit component styling */
    div[data-testid="stExpander"] {
        background-color: #f7fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    div[data-testid="stExpander"] > div[role="button"] {
        padding: 0.75rem 1rem;
    }

    div[data-testid="stExpander"] > div[role="button"] > div > p {
        font-weight: 600;
        color: #2d3748;
    }

    .stAlert {
        border-radius: 8px;
    }

    .stProgress > div > div > div > div {
        background-color: #3182ce;
    }

    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #1a365d;
    }

    .stMarkdown p {
        line-height: 1.6;
    }

    .stMarkdown ul, .stMarkdown ol {
        margin-left: 1.25rem;
    }

    .stMarkdown li {
        margin-bottom: 0.5rem;
    }

    .stMarkdown blockquote {
        border-left: 4px solid #cbd5e0;
        padding-left: 1rem;
        margin-left: 0;
        color: #718096;
    }

    .stMarkdown code {
        background-color: #edf2f7;
        border-radius: 4px;
        padding: 0.2em 0.4em;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    }

    .stMarkdown pre code {
        display: block;
        padding: 1rem;
        overflow-x: auto;
        background-color: #2d3748;
        color: #f7fafc;
        border-radius: 8px;
    }
</style>
"""

def apply_custom_styles():
    """Aplica os estilos CSS personalizados ao app Streamlit."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
