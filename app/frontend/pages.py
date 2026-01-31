"""
Páginas do frontend Streamlit.
Implementa a tela inicial e interface de chat com suporte a visualizações.
"""

import streamlit as st

from app.config.agents import get_available_themes, get_theme_descriptions
from app.governance.logging import get_governance_manager
from app.orchestration.graph import create_deep_orchestrator_instance


def init_session_state():
    """Inicializa o estado da sessão."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "selected_theme" not in st.session_state:
        st.session_state.selected_theme = None

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None

    if "session_context" not in st.session_state:
        st.session_state.session_context = None

    if "show_details" not in st.session_state:
        st.session_state.show_details = True

    if "pending_visualization" not in st.session_state:
        st.session_state.pending_visualization = None


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


def render_home_page():
    """Renderiza a página inicial de seleção de tema."""
    st.title("Plataforma Multiagente de IA")
    st.markdown("---")

    st.markdown("""
    ### Bem-vindo à Plataforma de Análise de Dados

    Esta plataforma utiliza múltiplos agentes de IA especializados para responder
    suas perguntas sobre diferentes domínios de dados.

    **Recursos:**
    - Agentes especializados por domínio (Cadastro, Financeiro, Rentabilidade)
    - Orquestração inteligente com LangGraph e DeepAgents
    - Sugestões automáticas de visualização de dados
    - Rastreabilidade completa das consultas

    **Selecione um tema abaixo para começar:**
    """)

    themes = get_available_themes()
    descriptions = get_theme_descriptions()

    cols = st.columns(len(themes))

    for i, theme in enumerate(themes):
        with cols[i]:
            st.markdown(f"#### {theme.capitalize()}")
            st.markdown(descriptions.get(theme, ""))

            if st.button(
                f"Acessar {theme.capitalize()}",
                key=f"btn_{theme}",
                use_container_width=True,
            ):
                st.session_state.selected_theme = theme
                governance = get_governance_manager()
                st.session_state.session_context = governance.create_session()
                st.session_state.orchestrator = create_deep_orchestrator_instance(
                    st.session_state.session_context
                )
                st.session_state.messages = []
                st.rerun()

    st.markdown("---")

    st.markdown("""
    ### Modo Híbrido

    Para perguntas que envolvem múltiplos domínios de dados, use o modo híbrido
    que aciona automaticamente os agentes necessários.
    """)

    if st.button("Acessar Modo Híbrido", use_container_width=True):
        st.session_state.selected_theme = "hybrid"
        governance = get_governance_manager()
        st.session_state.session_context = governance.create_session()
        st.session_state.orchestrator = create_deep_orchestrator_instance(
            st.session_state.session_context
        )
        st.session_state.messages = []
        st.rerun()


def render_chat_page():
    """Renderiza a página de chat."""
    theme = st.session_state.selected_theme

    with st.sidebar:
        st.title("Configurações")

        if theme == "hybrid":
            st.info("Modo Híbrido: Múltiplos agentes serão acionados conforme necessário.")
        else:
            st.info(f"Tema atual: **{theme.capitalize()}**")

        st.markdown("---")

        st.session_state.show_details = st.checkbox(
            "Mostrar detalhes da execução",
            value=st.session_state.show_details,
        )

        st.markdown("---")

        if st.button("Voltar ao Início", use_container_width=True):
            st.session_state.selected_theme = None
            st.session_state.messages = []
            st.session_state.orchestrator = None
            st.session_state.pending_visualization = None
            st.rerun()

        st.markdown("---")

        if st.session_state.session_context:
            st.markdown("**Session ID:**")
            st.code(st.session_state.session_context.session_id[:8] + "...")

        st.markdown("---")
        st.markdown("**Powered by:**")
        st.markdown("- LangGraph")
        st.markdown("- DeepAgents")
        st.markdown("- Databricks")

    if theme == "hybrid":
        st.title("Chat - Modo Híbrido")
    else:
        st.title(f"Chat - {theme.capitalize()}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and st.session_state.show_details:
                if "plan" in message:
                    with st.expander("Plano de Execução"):
                        for step in message["plan"]:
                            status_icon = "✓" if step.get("status") == "completed" else "○"
                            st.markdown(f"{status_icon} **{step['agent']}**: {step['task']}")

                if "sources" in message:
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

                    result = orchestrator.process_query(prompt, theme)

                    response_text = result.get("response", "Não foi possível processar a pergunta.")
                    st.markdown(response_text)

                    message_data = {
                        "role": "assistant",
                        "content": response_text,
                    }

                    if "plan" in result:
                        message_data["plan"] = result["plan"]
                        if st.session_state.show_details:
                            with st.expander("Plano de Execução"):
                                for step in result["plan"]:
                                    status_icon = "✓" if step.get("status") == "completed" else "○"
                                    st.markdown(f"{status_icon} **{step['agent']}**: {step['task']}")

                    if "sources" in result:
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
    """Renderiza a página apropriada baseada no estado."""
    init_session_state()

    if st.session_state.selected_theme is None:
        render_home_page()
    else:
        render_chat_page()
