"""
Páginas do frontend Streamlit.
Implementa fluxo de três telas: Login → Seleção de Grupos → Chat.
Frontend apenas coleta contexto e exibe estado - sem lógica de negócio.
"""

import streamlit as st

from app.frontend.styles import apply_custom_styles

SAMPLE_GROUPS = [
    {
        "codigo_grupo": "GRP001",
        "nome_grupo": "Grupo Alpha Investimentos",
        "cnpj": "12.345.678/0001-90",
        "razao_social": "Alpha Investimentos S.A.",
        "rating": 8.5,
        "quantidade_socios": 12,
        "principalidade": "Holding",
        "quantidade_produtos": 45,
        "risco": "Baixo",
        "relevancia": "Alta",
        "complexidade": "Média",
    },
    {
        "codigo_grupo": "GRP002",
        "nome_grupo": "Grupo Beta Participações",
        "cnpj": "98.765.432/0001-10",
        "razao_social": "Beta Participações Ltda.",
        "rating": 7.2,
        "quantidade_socios": 8,
        "principalidade": "Comercial",
        "quantidade_produtos": 23,
        "risco": "Médio",
        "relevancia": "Média",
        "complexidade": "Baixa",
    },
    {
        "codigo_grupo": "GRP003",
        "nome_grupo": "Grupo Gamma Serviços",
        "cnpj": "11.222.333/0001-44",
        "razao_social": "Gamma Serviços e Consultoria S.A.",
        "rating": 9.1,
        "quantidade_socios": 5,
        "principalidade": "Serviços",
        "quantidade_produtos": 67,
        "risco": "Baixo",
        "relevancia": "Alta",
        "complexidade": "Alta",
    },
    {
        "codigo_grupo": "GRP004",
        "nome_grupo": "Grupo Delta Industrial",
        "cnpj": "55.666.777/0001-88",
        "razao_social": "Delta Indústria e Comércio Ltda.",
        "rating": 6.8,
        "quantidade_socios": 15,
        "principalidade": "Industrial",
        "quantidade_produtos": 89,
        "risco": "Alto",
        "relevancia": "Média",
        "complexidade": "Média",
    },
]


def init_session_state():
    """Inicializa o estado da sessão com todas as variáveis necessárias."""
    if "user" not in st.session_state:
        st.session_state.user = None

    if "selected_group" not in st.session_state:
        st.session_state.selected_group = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None

    if "session_context" not in st.session_state:
        st.session_state.session_context = None

    if "show_details" not in st.session_state:
        st.session_state.show_details = True

    if "pending_visualization" not in st.session_state:
        st.session_state.pending_visualization = None

    if "available_groups" not in st.session_state:
        st.session_state.available_groups = SAMPLE_GROUPS

    if "memory_status" not in st.session_state:
        st.session_state.memory_status = {
            "contexto_carregado": False,
            "memoria_consultada": False,
            "raio_x_validado": False,
            "ambiguidade_resolvida": False,
            "resposta_entregue": False,
        }

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-4o-mini"

    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = "openai"


def render_login_page():
    """
    Tela 1 - Login.
    Captura matrícula e senha do usuário.
    Não executa validação complexa, apenas armazena contexto.
    """
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; min-height: 80vh; flex-direction: column;">
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
            <div class="login-container">
                <h1 style="text-align: center; color: #1a365d; margin-bottom: 0.5rem;">
                    Copiloto de IA
                </h1>
                <p style="text-align: center; color: #4a5568; margin-bottom: 2rem;">
                    Plataforma Multiagente Corporativa
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Acesso ao Sistema")

            matricula = st.text_input(
                "Matrícula",
                value="t781385",
                placeholder="Digite sua matrícula",
                key="login_matricula",
            )

            senha = st.text_input(
                "Senha",
                type="password",
                value="alvaro10",
                placeholder="Digite sua senha",
                key="login_senha",
            )

            submitted = st.form_submit_button(
                "Entrar",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                if matricula and senha:
                    st.session_state.user = {
                        "matricula": matricula,
                    }
                    st.rerun()
                else:
                    st.error("Por favor, preencha todos os campos.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_group_selection_page():
    """
    Tela 2 - Seleção de Grupos.
    Exibe grupos disponíveis para seleção e configuração do modelo de IA.
    Apenas exibe dados, sem classificação ou inferência.
    """
    st.title("Seleção de Grupo Econômico")

    st.markdown(
        f"""
        <div class="user-info-bar">
            Usuário: <strong>{st.session_state.user.get('matricula', 'N/A')}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("### Configuração do Modelo de IA")

    from app.config.models import (
        MODELS_REGISTRY,
        ModelProvider,
        get_available_providers,
        get_models_by_provider,
    )

    available_providers = get_available_providers()

    if not available_providers:
        st.warning(
            "Nenhuma API key configurada. Configure OPENAI_API_KEY "
            "ou DATABRICKS_TOKEN/DATABRICKS_HOST no arquivo .env"
        )
        available_providers = [("OpenAI (não configurado)", ModelProvider.OPENAI)]

    provider_names = [p[0] for p in available_providers]

    databricks_idx = next(
        (i for i, (name, _) in enumerate(available_providers) if name == "Databricks"),
        0
    )

    selected_provider_idx = st.selectbox(
        "Provedor de IA",
        options=range(len(provider_names)),
        format_func=lambda i: provider_names[i],
        index=databricks_idx,
        key="provider_selector",
    )

    selected_provider = available_providers[selected_provider_idx][1]
    st.session_state.selected_provider = selected_provider.value

    provider_models = get_models_by_provider(selected_provider)

    if provider_models:
        model_options = []
        for model_id in provider_models:
            config = MODELS_REGISTRY[model_id]
            model_options.append((model_id, config.display_name, config.task.value))

        selected_model_idx = st.selectbox(
            "Modelo",
            options=range(len(model_options)),
            format_func=lambda i: f"[ {available_providers[selected_provider_idx][0]} ] {model_options[i][1]} ({model_options[i][2]})",
            key="model_selector",
        )

        st.session_state.selected_model = model_options[selected_model_idx][0]
        st.session_state.active_model = model_options[selected_model_idx][0]

        model_config = MODELS_REGISTRY[st.session_state.selected_model]
        st.caption(f"_{model_config.description}_")

        if model_config.endpoint_name:
            st.caption(f"Endpoint: `{model_config.endpoint_name}`")
        elif model_config.model_name:
            st.caption(f"Model: `{model_config.model_name}`")

    st.markdown("---")

    st.markdown("""
    ### Selecione o grupo que deseja avaliar

    Escolha um dos grupos econômicos disponíveis para iniciar a análise via chat.
    """)

    groups = st.session_state.available_groups

    # Grid de Cards Executivos
    cols_per_row = 2
    rows = [groups[i:i + cols_per_row] for i in range(0, len(groups), cols_per_row)]

    selected_group_code = st.session_state.get("temp_selected_group_code")

    for row_groups in rows:
        cols = st.columns(cols_per_row)
        for i, group in enumerate(row_groups):
            with cols[i]:
                is_selected = selected_group_code == group["codigo_grupo"]
                card_class = "executive-card executive-card-selected" if is_selected else "executive-card"
                
                rating_val = group["rating"]
                rating_pct = (rating_val / 10) * 100
                
                risk_color = "#e53e3e" if group["risco"] == "Alto" else "#dd6b20" if group["risco"] == "Médio" else "#38a169"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="executive-card-risk-indicator" style="background-color: {risk_color};">{group["risco"]}</div>
                    <div class="executive-card-header">
                        <h3 class="executive-card-title">{group["nome_grupo"]}</h3>
                        <span class="executive-card-badge">{group["codigo_grupo"]}</span>
                    </div>
                    <div class="executive-card-cnpj">{group["cnpj"]}</div>
                    <div class="executive-card-metrics">
                        <div class="executive-card-metric-item">
                            <span class="executive-card-metric-label">Principalidade</span>
                            <span class="executive-card-metric-value">{group["principalidade"]}</span>
                        </div>
                        <div class="executive-card-metric-item">
                            <span class="executive-card-metric-label">Sócios</span>
                            <span class="executive-card-metric-value">{group["quantidade_socios"]}</span>
                        </div>
                        <div class="executive-card-metric-item">
                            <span class="executive-card-metric-label">Produtos</span>
                            <span class="executive-card-metric-value">{group["quantidade_produtos"]}</span>
                        </div>
                        <div class="executive-card-metric-item">
                            <span class="executive-card-metric-label">Complexidade</span>
                            <span class="executive-card-metric-value">{group["complexidade"]}</span>
                        </div>
                    </div>
                    <div class="executive-card-rating-container">
                        <span class="executive-card-rating-label">Rating: {rating_val}/10</span>
                        <div class="executive-card-rating-bar-bg">
                            <div class="executive-card-rating-bar-fill" style="width: {rating_pct}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn, col_exp = st.columns([1, 1])
                with col_btn:
                    if st.button(f"Selecionar", key=f"sel_{group["codigo_grupo"]}", use_container_width=True, type="primary" if is_selected else "secondary"):
                        st.session_state.temp_selected_group_code = group["codigo_grupo"]
                        st.rerun()
                with col_exp:
                    with st.expander("Ver Detalhes"):
                        st.markdown(f"**Razão Social:** {group["razao_social"]}")
                        st.markdown(f"**Código:** {group["codigo_grupo"]}")
                        st.markdown(f"**CNPJ:** {group["cnpj"]}")
                        st.markdown(f"**Relevância:** {group["relevancia"]}")

    st.markdown("---")

    col_btn1, col_btn2 = st.columns([3, 1])

    with col_btn2:
        if st.button(
            "Confirmar Seleção",
            use_container_width=True,
            type="primary",
            disabled=not selected_group_code
        ):
            group = next(g for g in groups if g["codigo_grupo"] == selected_group_code)
            st.session_state.selected_group = {
                "codigo_grupo": group["codigo_grupo"],
                "nome_grupo": group["nome_grupo"],
                "cnpj": group["cnpj"],
                "razao_social": group["razao_social"],
                "rating": group["rating"],
                "quantidade_socios": group["quantidade_socios"],
                "principalidade": group["principalidade"],
                "quantidade_produtos": group["quantidade_produtos"],
                "risco": group["risco"],
                "relevancia": group["relevancia"],
                "complexidade": group["complexidade"],
            }

            from app.governance.logging import get_governance_manager
            from app.orchestration.graph import create_deep_orchestrator_instance

            governance = get_governance_manager()
            st.session_state.session_context = governance.create_session()

            user_id = st.session_state.user.get("matricula", "") if st.session_state.user else ""
            model_id = st.session_state.get("selected_model", "gpt-4o-mini")
            st.session_state.orchestrator = create_deep_orchestrator_instance(
                    st.session_state.session_context,
                    user_id=user_id,
                    model_id=model_id,
                )
            st.session_state.chat_history = []
            st.session_state.memory_status = {
                    "contexto_carregado": False,
                    "memoria_consultada": False,
                    "raio_x_validado": False,
                    "ambiguidade_resolvida": False,
                    "resposta_entregue": False,
                }
            st.rerun()

    with st.sidebar:
        st.markdown("### Navegação")
        if st.button("Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.selected_group = None
            st.session_state.chat_history = []
            st.rerun()


def render_group_header():
    """
    Renderiza o cabeçalho contextual fixo do grupo selecionado.
    Exibe informações básicas sem classificação ou análise.
    """
    group = st.session_state.selected_group

    if not group:
        return

    st.markdown(
        f"""
        <div class="group-header">
            <div class="group-header-title">
                <span class="group-code">{group['codigo_grupo']}</span>
                <span class="group-name">{group['nome_grupo']}</span>
            </div>
            <div class="group-header-info">
                <div class="header-info-item">
                    <span class="header-label">CNPJ</span>
                    <span class="header-value">{group['cnpj']}</span>
                </div>
                <div class="header-info-item">
                    <span class="header-label">Razão Social</span>
                    <span class="header-value">{group['razao_social']}</span>
                </div>
                <div class="header-info-item">
                    <span class="header-label">Rating</span>
                    <span class="header-value">{group['rating']}</span>
                </div>
                <div class="header-info-item">
                    <span class="header-label">Sócios</span>
                    <span class="header-value">{group['quantidade_socios']}</span>
                </div>
                <div class="header-info-item">
                    <span class="header-label">Principalidade</span>
                    <span class="header-value">{group['principalidade']}</span>
                </div>
                <div class="header-info-item">
                    <span class="header-label">Produtos</span>
                    <span class="header-value">{group['quantidade_produtos']}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
                    st.markdown(f"* **{term}** -> {resolution}")
                    if amb_type:
                        st.caption(f"   Tipo: {amb_type}")

        if inferred_period:
            st.markdown(f"* **período inferido** -> {inferred_period}")

        if inferred_domains:
            domains_str = ", ".join(inferred_domains)
            st.markdown(f"* **domínios** -> {domains_str}")

        st.markdown("---")
        st.caption(f"Pergunta interpretada: *{normalized}*")


def render_ai_reasoning(message_data):
    """Renderiza o painel de explicabilidade do raciocínio da IA."""
    with st.expander("🧠 Raciocínio da IA", expanded=False):
        analysis = message_data.get("analysis", {})
        category = analysis.get("category", "Geral")
        complexity = analysis.get("complexity", "Simples")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Categoria:** {category}")
        with col2:
            comp_lower = complexity.lower()
            comp_class = f"complexity-{comp_lower}"
            st.markdown(f"**Complexidade:** <span class='complexity-badge {comp_class}'>{complexity}</span>", unsafe_allow_html=True)
            
        st.markdown('<div class="reasoning-panel">', unsafe_allow_html=True)
        
        # Agentes envolvidos
        agents = []
        if "plan" in message_data and message_data["plan"]:
            agents = list(set([step.get("agent", "Agent") for step in message_data["plan"] if step.get("agent")]))
        
        steps = [
            ("🧭 Interpretação", "Análise da pergunta e resolução de termos técnicos para garantir precisão."),
            ("🧠 Estratégia", "Definição do plano de consulta aos dados e orquestração de subagentes."),
            ("⚙️ Execução", f"Acionamento dos agentes especializados: {', '.join(agents) if agents else 'Busca de dados'}."),
            ("✅ Validação", "Revisão da consistência dos dados retornados e formatação da resposta final.")
        ]
        
        for title, desc in steps:
            st.markdown(f"""
            <div class="reasoning-step">
                <div class="step-content">
                    <span class="step-title">{title}</span>
                    <span class="step-desc">{desc}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tempo (mockado ou real se disponível)
        exec_time = message_data.get("execution_time", "1.2")
        st.markdown(f"⏱️ **Tempo total de execução:** {exec_time}s")


def render_chat_page():
    """
    Tela 3 - Chat com IA.
    Interface de chat contextualizada pelo grupo selecionado.
    """
    if not st.session_state.selected_group:
        st.warning("Selecione um grupo para continuar.")
        if st.button("Voltar para Seleção"):
            st.rerun()
        return

    render_group_header()

    with st.sidebar:
        st.markdown("### Configurações")

        st.session_state.show_details = st.checkbox(
            "Mostrar detalhes da execução",
            value=st.session_state.show_details,
        )

        st.markdown("---")

        st.markdown("### Modelo Ativo")
        active_model = st.session_state.get("active_model", st.session_state.get("selected_model", "N/A"))
        selected_provider = st.session_state.get("selected_provider", "N/A")

        from app.config.models import get_model_config
        model_config = get_model_config(active_model) if active_model != "N/A" else None

        if model_config:
            provider_display = model_config.provider.value.upper()
            st.markdown(f"**Provider:** {provider_display}")
            st.markdown(f"**Modelo:** {model_config.display_name}")
            st.markdown(f"**Endpoint:** `{model_config.endpoint_name or model_config.model_name}`")
            st.markdown(f"**Task:** {model_config.task.value}")

            if model_config.provider.value == "databricks":
                st.success("Databricks ativo")
            else:
                st.warning("OpenAI selecionado explicitamente")
        else:
            st.markdown(f"**Provider:** {selected_provider}")
            st.markdown(f"**Modelo:** {active_model}")

        st.markdown("---")

        if st.button("Alterar Grupo", use_container_width=True):
            st.session_state.selected_group = None
            st.session_state.chat_history = []
            st.session_state.orchestrator = None
            st.session_state.pending_visualization = None
            st.rerun()

        st.markdown("---")

        if st.button("Sair", use_container_width=True):
            st.session_state.user = None
            st.session_state.selected_group = None
            st.session_state.chat_history = []
            st.session_state.orchestrator = None
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

        st.markdown("---")
        st.markdown("**Status do Pipeline:**")
        memory_status = st.session_state.get("memory_status", {})
        status_items = [
            ("contexto_carregado", "Contexto carregado"),
            ("memoria_consultada", "Memória consultada"),
            ("ambiguidade_resolvida", "Ambiguidade resolvida"),
            ("subagentes_executados", "Subagentes executados"),
            ("resposta_validada", "Resposta validada"),
            ("resposta_entregue", "Resposta entregue"),
        ]
        for key, label in status_items:
            status = memory_status.get(key, False)
            icon = "+" if status else "-"
            st.markdown(f"{icon} {label}")

    st.markdown("---")

    st.markdown(
        f"""
        <div class="chat-title">
            Chat - Avaliação do Grupo
        </div>
        <div class="chat-subtitle">
            Consultando: {st.session_state.selected_group['nome_grupo']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and st.session_state.show_details:
                render_ai_reasoning(message)

                if "plan" in message and message["plan"]:
                    with st.expander("Plano de Execução"):
                        for step in message["plan"]:
                            if step.get("agent") != "VisualizationAgent":
                                st.markdown(
                                    f"* **{step.get('agent', 'Agent')}**: {step.get('task', '')}"
                                )

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

    if prompt := st.chat_input("Digite sua pergunta sobre o grupo..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                try:
                    orchestrator = st.session_state.orchestrator

                    group_context = st.session_state.selected_group

                    result = orchestrator.process_query(
                        prompt,
                        ["cadastro", "financeiro", "rentabilidade"],
                        group_context=group_context,
                    )

                    ambiguity_result = result.get("ambiguity_result", {})
                    if ambiguity_result and st.session_state.show_details:
                        render_disambiguation_card(ambiguity_result)

                    response_text = result.get(
                        "response", "Não foi possível processar a pergunta."
                    )
                    st.markdown(response_text)

                    # Extrair metadados para explicabilidade
                    analysis = result.get("analysis", {})
                    if not analysis:
                        # Fallback se não vier do orquestrador
                        analysis = {
                            "category": "Financeiro",
                            "complexity": "Simples"
                        }

                    message_data = {
                        "role": "assistant",
                        "content": response_text,
                        "ambiguity_result": ambiguity_result,
                        "analysis": analysis,
                        "execution_time": "1.4" # Mockado para o exemplo
                    }

                    if "plan" in result and result["plan"]:
                        message_data["plan"] = result["plan"]
                        if st.session_state.show_details:
                            render_ai_reasoning(message_data)
                            
                            with st.expander("Plano de Execução"):
                                for step in result["plan"]:
                                    if step.get("agent") != "VisualizationAgent":
                                        st.markdown(
                                            f"* **{step.get('agent', 'Agent')}**: "
                                            f"{step.get('task', '')}"
                                        )

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

                    memory_status = result.get("memory_status", {})
                    if memory_status:
                        st.session_state.memory_status = memory_status
                        message_data["memory_status"] = memory_status

                    st.session_state.chat_history.append(message_data)

                except Exception as e:
                    error_msg = f"Erro ao processar pergunta: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg,
                    })


def render_page():
    """
    Renderiza a página apropriada baseada no estado.
    Fluxo: Login → Seleção de Grupos → Chat
    """
    apply_custom_styles()
    init_session_state()

    if st.session_state.user is None:
        render_login_page()
    elif st.session_state.selected_group is None:
        render_group_selection_page()
    else:
        render_chat_page()
