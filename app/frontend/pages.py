"""
Páginas do frontend Streamlit.
Implementa fluxo de duas telas: seleção de domínios e chat com desambiguação.
Suporta múltiplos provedores de LLM (OpenAI e Google Gemini).
"""

import streamlit as st

from app.config.agents import get_available_themes, get_theme_descriptions
from app.config.llm import (
    DEFAULT_MODEL,
    get_model_config,
    get_model_display_info,
)
from app.governance.logging import get_governance_manager
from app.orchestration.graph import create_deep_orchestrator_instance


def init_session_state():
    """Inicializa o estado da sessão."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "active_domains" not in st.session_state:
        st.session_state.active_domains = []

    if "domains_selected" not in st.session_state:
        st.session_state.domains_selected = False

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None

    if "session_context" not in st.session_state:
        st.session_state.session_context = None

    if "show_details" not in st.session_state:
        st.session_state.show_details = True

    if "pending_visualization" not in st.session_state:
        st.session_state.pending_visualization = None

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = DEFAULT_MODEL


def render_chart(chart_data: dict):
    """
    Renderiza um gráfico baseado nos dados fornecidos.

    Args:
        chart_data: Dicionário com dados do gráfico
    """
    import pandas as pd

    chart_type = chart_data.get("chart_type", "bar")
    title = chart_data.get("title", "Gráfico")
    labels = chart_data.get("labels", [])
    datasets = chart_data.get("datasets", [])

    if not labels or not datasets:
        values = chart_data.get("values", [])
        if values and labels:
            datasets = [{"name": "Valores", "values": values}]

    if not datasets:
        st.warning("Dados insuficientes para gerar o gráfico.")
        return

    st.subheader(title)

    data = {"Categoria": labels}
    for dataset in datasets:
        name = dataset.get("name", "Série")
        values = dataset.get("values", [])
        if len(values) == len(labels):
            data[name] = values

    df = pd.DataFrame(data)

    if chart_type == "bar":
        st.bar_chart(df.set_index("Categoria"))
    elif chart_type == "line":
        st.line_chart(df.set_index("Categoria"))
    elif chart_type == "area":
        st.area_chart(df.set_index("Categoria"))
    elif chart_type == "pie":
        import altair as alt

        if datasets:
            values = datasets[0].get("values", [])
            pie_df = pd.DataFrame({"Categoria": labels, "Valor": values})
            chart = (
                alt.Chart(pie_df)
                .mark_arc()
                .encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Categoria", type="nominal"),
                    tooltip=["Categoria", "Valor"],
                )
                .properties(title=title)
            )
            st.altair_chart(chart, use_container_width=True)
    elif chart_type == "scatter":
        if len(datasets) >= 2:
            scatter_df = pd.DataFrame({
                "X": datasets[0].get("values", []),
                "Y": datasets[1].get("values", []),
            })
            st.scatter_chart(scatter_df)
        else:
            st.warning("Gráfico de dispersão requer pelo menos 2 séries de dados.")
    else:
        st.bar_chart(df.set_index("Categoria"))


def render_disambiguation_card(ambiguity_result: dict):
    """
    Renderiza o card de desambiguação de forma elegante e não intrusiva.

    Args:
        ambiguity_result: Resultado da desambiguação do AmbiguityResolverAgent
    """
    if not ambiguity_result:
        return

    original = ambiguity_result.get("original_question", "")
    normalized = ambiguity_result.get("normalized_question", "")
    ambiguities = ambiguity_result.get("ambiguities_detected", [])
    inferred_period = ambiguity_result.get("inferred_period")
    inferred_domains = ambiguity_result.get("inferred_domains", [])

    if original == normalized and not ambiguities:
        return

    with st.expander("Interpretação da Pergunta", expanded=False):
        st.markdown("---")

        if ambiguities:
            for amb in ambiguities:
                term = amb.get("term", "")
                resolution = amb.get("resolution", "")
                amb_type = amb.get("type", "")
                if term and resolution:
                    st.markdown(f"• **{term}** → {resolution}")
                    if amb_type:
                        st.caption(f"   Tipo: {amb_type}")

        if inferred_period:
            st.markdown(f"• **período inferido** → {inferred_period}")

        if inferred_domains:
            domains_str = ", ".join(inferred_domains)
            st.markdown(f"• **domínios** → {domains_str}")

        st.markdown("---")
        st.caption(f"Pergunta interpretada: *{normalized}*")


def render_domain_selection_page():
    """
    Tela 1 - Seleção de Informações/Domínios.
    O usuário DEVE selecionar pelo menos um domínio antes de acessar o chat.
    """
    st.title("Plataforma Multiagente de IA")
    st.markdown("---")

    st.markdown("""
    ### Seleção de Domínios de Dados

    Antes de iniciar o chat, selecione os domínios de dados que deseja consultar.
    Isso permite que os agentes especializados sejam acionados de forma otimizada.

    **Recursos da plataforma:**
    - Desambiguação automática de perguntas
    - Agentes especializados por domínio
    - Orquestração inteligente com LangGraph
    - Sugestões de visualização de dados
    - Rastreabilidade completa
    - Suporte a múltiplos modelos de IA (OpenAI e Google Gemini)
    """)

    st.markdown("---")
    st.markdown("### Selecione os domínios disponíveis:")

    themes = get_available_themes()
    descriptions = get_theme_descriptions()

    selected_domains = []

    cols = st.columns(len(themes))

    for i, theme in enumerate(themes):
        with cols[i]:
            st.markdown(f"#### {theme.capitalize()}")
            st.markdown(descriptions.get(theme, ""))

            is_selected = st.checkbox(
                f"Incluir {theme.capitalize()}",
                key=f"domain_{theme}",
                value=theme in st.session_state.active_domains,
            )

            if is_selected:
                selected_domains.append(theme)

    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        if selected_domains:
            domains_text = ", ".join([d.capitalize() for d in selected_domains])
            st.success(f"Domínios selecionados: **{domains_text}**")
        else:
            st.warning("Selecione pelo menos um domínio para continuar.")

    with col2:
        continue_disabled = len(selected_domains) == 0

        if st.button(
            "Continuar para o Chat",
            use_container_width=True,
            disabled=continue_disabled,
            type="primary",
        ):
            st.session_state.active_domains = selected_domains
            st.session_state.domains_selected = True

            governance = get_governance_manager()
            st.session_state.session_context = governance.create_session()
            st.session_state.orchestrator = create_deep_orchestrator_instance(
                st.session_state.session_context,
                model_id=st.session_state.selected_model,
            )
            st.session_state.messages = []
            st.rerun()

    st.markdown("---")

    st.markdown("### Selecione o modelo de IA:")

    model_info = get_model_display_info()

    openai_models = [m for m in model_info if m["provider"] == "openai"]
    gemini_models = [m for m in model_info if m["provider"] == "gemini"]

    col_openai, col_gemini = st.columns(2)

    with col_openai:
        st.markdown("#### OpenAI (ChatGPT)")
        st.radio(
            "Modelo OpenAI",
            options=[m["id"] for m in openai_models],
            format_func=lambda x: next(
                (m["display_name"] + (" (sem API key)" if not m["available"] else "")
                 for m in openai_models if m["id"] == x),
                x
            ),
            key="openai_model_radio",
            index=0,
            label_visibility="collapsed",
        )

    with col_gemini:
        st.markdown("#### Google (Gemini)")
        st.radio(
            "Modelo Gemini",
            options=[m["id"] for m in gemini_models],
            format_func=lambda x: next(
                (m["display_name"] + (" (sem API key)" if not m["available"] else "")
                 for m in gemini_models if m["id"] == x),
                x
            ),
            key="gemini_model_radio",
            index=0,
            label_visibility="collapsed",
        )

    provider_choice = st.radio(
        "Escolha o provedor:",
        options=["OpenAI", "Google Gemini"],
        horizontal=True,
        key="provider_choice",
    )

    if provider_choice == "OpenAI":
        selected_model = st.session_state.get("openai_model_radio", "gpt-4o-mini")
    else:
        selected_model = st.session_state.get("gemini_model_radio", "gemini-1.5-flash")

    model_config = get_model_config(selected_model)
    if model_config:
        st.caption(f"Modelo selecionado: **{model_config.display_name}**")

    st.session_state.selected_model = selected_model

    st.markdown("---")

    with st.expander("Sobre os domínios", expanded=False):
        st.markdown("""
        **Cadastro**: Informações cadastrais de clientes, incluindo dados pessoais,
        endereços, contatos e histórico de cadastro.

        **Financeiro**: Dados financeiros como transações, saldos, pagamentos
        e histórico financeiro.

        **Rentabilidade**: Métricas de rentabilidade, análises de lucro, margens,
        ROI e indicadores de desempenho.
        """)


def render_chat_page():
    """
    Tela 2 - Interface de Chat com IA.
    Exibe respostas, plano, subagentes e processo de desambiguação.
    """
    active_domains = st.session_state.active_domains

    with st.sidebar:
        st.title("Configurações")

        domains_text = ", ".join([d.capitalize() for d in active_domains])
        st.info(f"**Domínios ativos:** {domains_text}")

        st.markdown("---")

        st.session_state.show_details = st.checkbox(
            "Mostrar detalhes da execução",
            value=st.session_state.show_details,
        )

        st.markdown("---")

        if st.button("Alterar Domínios", use_container_width=True):
            st.session_state.domains_selected = False
            st.session_state.messages = []
            st.session_state.orchestrator = None
            st.session_state.pending_visualization = None
            st.rerun()

        st.markdown("---")

        if st.session_state.session_context:
            st.markdown("**Session ID:**")
            st.code(st.session_state.session_context.session_id[:8] + "...")

        st.markdown("---")

        model_config = get_model_config(st.session_state.selected_model)
        if model_config:
            st.markdown("**Modelo de IA:**")
            st.markdown(f"- {model_config.display_name}")

        st.markdown("---")
        st.markdown("**Powered by:**")
        st.markdown("- LangGraph")
        st.markdown("- DeepAgents")
        st.markdown("- Databricks")

    st.title("Chat - Análise de Dados")
    st.caption(f"Consultando: {domains_text}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and st.session_state.show_details:
                if "ambiguity_result" in message and message["ambiguity_result"]:
                    render_disambiguation_card(message["ambiguity_result"])

                if "plan" in message and message["plan"]:
                    with st.expander("Plano de Execução"):
                        for step in message["plan"]:
                            if step.get("agent") != "VisualizationAgent":
                                status_icon = "○"
                                st.markdown(f"{status_icon} **{step.get('agent', 'Agent')}**: {step.get('task', '')}")

                if "sources" in message and message["sources"]:
                    with st.expander("Fontes Consultadas"):
                        for source in message["sources"]:
                            st.markdown(f"- {source}")

                if "subagent_responses" in message and message["subagent_responses"]:
                    with st.expander("Respostas dos Subagentes"):
                        for resp in message["subagent_responses"]:
                            st.markdown(f"**{resp.get('agent', 'Unknown')}:**")
                            st.markdown(resp.get("response", "Sem resposta"))
                            st.markdown("---")

                if "visualization_data" in message and message["visualization_data"]:
                    with st.expander("Visualização", expanded=True):
                        render_chart(message["visualization_data"])

    if st.session_state.pending_visualization:
        viz_data = st.session_state.pending_visualization
        st.info(viz_data.get("suggestion", "Deseja ver um gráfico dos dados?"))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, mostrar gráfico", use_container_width=True):
                if viz_data.get("chart_data"):
                    render_chart(viz_data["chart_data"])
                st.session_state.pending_visualization = None
                st.rerun()
        with col2:
            if st.button("Não, obrigado", use_container_width=True):
                st.session_state.pending_visualization = None
                st.rerun()

    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                try:
                    orchestrator = st.session_state.orchestrator

                    result = orchestrator.process_query(prompt, active_domains)

                    ambiguity_result = result.get("ambiguity_result", {})
                    if ambiguity_result and st.session_state.show_details:
                        render_disambiguation_card(ambiguity_result)

                    response_text = result.get("response", "Não foi possível processar a pergunta.")
                    st.markdown(response_text)

                    message_data = {
                        "role": "assistant",
                        "content": response_text,
                        "ambiguity_result": ambiguity_result,
                    }

                    if "plan" in result and result["plan"]:
                        message_data["plan"] = result["plan"]
                        if st.session_state.show_details:
                            with st.expander("Plano de Execução"):
                                for step in result["plan"]:
                                    if step.get("agent") != "VisualizationAgent":
                                        status_icon = "○"
                                        st.markdown(f"{status_icon} **{step.get('agent', 'Agent')}**: {step.get('task', '')}")

                    if "sources" in result and result["sources"]:
                        message_data["sources"] = result["sources"]
                        if st.session_state.show_details:
                            with st.expander("Fontes Consultadas"):
                                for source in result["sources"]:
                                    st.markdown(f"- {source}")

                    if "subagent_responses" in result and result["subagent_responses"]:
                        message_data["subagent_responses"] = result["subagent_responses"]
                        if st.session_state.show_details:
                            with st.expander("Respostas dos Subagentes"):
                                for resp in result["subagent_responses"]:
                                    st.markdown(f"**{resp.get('agent', 'Unknown')}:**")
                                    st.markdown(resp.get("response", "Sem resposta"))
                                    st.markdown("---")

                    viz_suggestion = result.get("visualization_suggestion")
                    viz_data = result.get("visualization_data")

                    if viz_suggestion:
                        st.info(f"**Sugestão de Visualização:** {viz_suggestion}")

                        if viz_data:
                            message_data["visualization_data"] = viz_data
                            st.session_state.pending_visualization = {
                                "suggestion": viz_suggestion,
                                "chart_data": viz_data,
                            }

                    st.session_state.messages.append(message_data)

                except Exception as e:
                    error_msg = f"Erro ao processar pergunta: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })


def render_page():
    """
    Renderiza a página apropriada baseada no estado.
    Tela 1 (seleção) é OBRIGATÓRIA antes da Tela 2 (chat).
    """
    init_session_state()

    if not st.session_state.domains_selected:
        render_domain_selection_page()
    else:
        render_chat_page()
