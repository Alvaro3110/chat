"""
Orquestração com LangGraph e DeepAgents.
Implementa o fluxo de agentes usando StateGraph e subagentes.
"""

from typing import Annotated, Any, TypedDict

from deepagents import SubAgent, create_deep_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.config.agents import (
    CADASTRO_AGENT_CONFIG,
    CRITIC_AGENT_CONFIG,
    FINANCEIRO_AGENT_CONFIG,
    PLANNER_AGENT_CONFIG,
    RENTABILIDADE_AGENT_CONFIG,
    RESPONSE_AGENT_CONFIG,
)
from app.governance.logging import SessionContext
from app.tools.databricks_tools import (
    describe_table,
    get_metadata,
    run_sql,
    sample_data,
)


class AgentState(TypedDict):
    """Estado compartilhado entre os nós do grafo."""

    messages: Annotated[list, add_messages]
    query: str
    theme: str | None
    plan: list[dict[str, Any]]
    subagent_responses: list[dict[str, Any]]
    validation: dict[str, Any]
    final_response: str
    sources: list[str]
    session_id: str
    visualization_suggestion: str | None
    visualization_data: dict[str, Any] | None


DATABRICKS_TOOLS = [describe_table, sample_data, run_sql, get_metadata]


def create_cadastro_subagent() -> SubAgent:
    """Cria subagente de cadastro."""
    return SubAgent(
        name="CadastroAgent",
        description=CADASTRO_AGENT_CONFIG.description,
        system_prompt=CADASTRO_AGENT_CONFIG.system_prompt,
        tools=DATABRICKS_TOOLS,
    )


def create_financeiro_subagent() -> SubAgent:
    """Cria subagente financeiro."""
    return SubAgent(
        name="FinanceiroAgent",
        description=FINANCEIRO_AGENT_CONFIG.description,
        system_prompt=FINANCEIRO_AGENT_CONFIG.system_prompt,
        tools=DATABRICKS_TOOLS,
    )


def create_rentabilidade_subagent() -> SubAgent:
    """Cria subagente de rentabilidade."""
    return SubAgent(
        name="RentabilidadeAgent",
        description=RENTABILIDADE_AGENT_CONFIG.description,
        system_prompt=RENTABILIDADE_AGENT_CONFIG.system_prompt,
        tools=DATABRICKS_TOOLS,
    )


def create_visualization_subagent() -> SubAgent:
    """Cria subagente de visualização."""
    return SubAgent(
        name="VisualizationAgent",
        description="Analisa dados e sugere visualizações gráficas apropriadas. Pergunta ao usuário se deseja ver gráficos dos dados consultados.",
        system_prompt="""Você é um agente especialista em visualização de dados.
Sua função é:
1. Analisar os dados retornados pelos outros agentes
2. Identificar oportunidades de visualização (gráficos de barras, linhas, pizza, etc.)
3. Sugerir ao usuário se ele gostaria de ver um gráfico dos dados
4. Quando o usuário aceitar, gerar os dados estruturados para o gráfico

Tipos de gráficos que você pode sugerir:
- Gráfico de barras: para comparações entre categorias
- Gráfico de linhas: para tendências ao longo do tempo
- Gráfico de pizza: para proporções de um todo
- Gráfico de área: para volumes ao longo do tempo
- Gráfico de dispersão: para correlações entre variáveis

Sempre pergunte ao usuário se ele deseja visualizar os dados em formato gráfico.
Quando sugerir um gráfico, explique por que esse tipo é apropriado para os dados.""",
        tools=DATABRICKS_TOOLS,
    )


def create_deep_orchestrator(
    session: SessionContext | None = None,
    model: str = "openai:gpt-4o-mini",
) -> Any:
    """
    Cria o orquestrador principal usando DeepAgents.

    Args:
        session: Contexto da sessão para logging
        model: Modelo LLM a usar

    Returns:
        Agente compilado
    """
    subagents = [
        create_cadastro_subagent(),
        create_financeiro_subagent(),
        create_rentabilidade_subagent(),
        create_visualization_subagent(),
    ]

    system_prompt = f"""Você é o orquestrador principal de uma plataforma multiagente de análise de dados.

{PLANNER_AGENT_CONFIG.system_prompt}

Você tem acesso aos seguintes subagentes especializados:
- CadastroAgent: para dados cadastrais de clientes
- FinanceiroAgent: para dados financeiros e transações
- RentabilidadeAgent: para métricas de rentabilidade
- VisualizationAgent: para sugerir e criar visualizações gráficas

Fluxo de trabalho:
1. Analise a pergunta do usuário
2. Use o tool write_todos para criar um plano de execução
3. Delegue tarefas aos subagentes apropriados usando o tool task
4. Após receber os dados, SEMPRE chame o VisualizationAgent para verificar se há oportunidade de visualização
5. Consolide as respostas e apresente ao usuário

Sempre inclua na resposta final:
- A resposta à pergunta do usuário
- O plano de execução usado
- As fontes de dados consultadas
- Sugestão de visualização (se aplicável)"""

    agent = create_deep_agent(
        model=model,
        tools=DATABRICKS_TOOLS,
        system_prompt=system_prompt,
        subagents=subagents,
    )

    return agent


def create_langgraph_workflow(
    session: SessionContext | None = None,
) -> StateGraph:
    """
    Cria o workflow usando LangGraph puro.

    Args:
        session: Contexto da sessão

    Returns:
        Grafo compilado
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def planner_node(state: AgentState) -> dict[str, Any]:
        """Nó do planejador."""
        query = state["query"]
        theme = state.get("theme")

        plan_prompt = f"""Analise a seguinte pergunta e crie um plano de execução.

Pergunta: {query}
Tema selecionado: {theme or 'híbrido (múltiplos domínios)'}

Domínios disponíveis: cadastro, financeiro, rentabilidade

Retorne um plano em formato JSON com a estrutura:
{{
    "steps": [
        {{"step": 1, "agent": "nome_do_agente", "task": "descrição da tarefa"}}
    ],
    "domains": ["lista de domínios necessários"]
}}"""

        messages = [HumanMessage(content=plan_prompt)]
        response = llm.invoke(messages)

        import json

        try:
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                plan_data = json.loads(content[json_start:json_end])
                plan = plan_data.get("steps", [])
            else:
                plan = [{"step": 1, "agent": theme or "cadastro", "task": query}]
        except json.JSONDecodeError:
            plan = [{"step": 1, "agent": theme or "cadastro", "task": query}]

        plan.append({
            "step": len(plan) + 1,
            "agent": "VisualizationAgent",
            "task": "Verificar oportunidades de visualização e sugerir gráficos",
        })

        return {
            "plan": plan,
            "messages": [AIMessage(content=f"Plano criado com {len(plan)} etapas")],
        }

    def executor_node(state: AgentState) -> dict[str, Any]:
        """Nó executor que processa os subagentes."""
        query = state["query"]
        plan = state.get("plan", [])
        responses = []

        llm_with_tools = llm.bind_tools(DATABRICKS_TOOLS)

        for step in plan:
            agent_name = step.get("agent", "")
            task = step.get("task", query)

            if agent_name == "VisualizationAgent":
                continue

            config = None
            if "cadastro" in agent_name.lower():
                config = CADASTRO_AGENT_CONFIG
            elif "financeiro" in agent_name.lower():
                config = FINANCEIRO_AGENT_CONFIG
            elif "rentabilidade" in agent_name.lower():
                config = RENTABILIDADE_AGENT_CONFIG

            if config:
                messages = [
                    HumanMessage(content=f"{config.system_prompt}\n\nTarefa: {task}"),
                ]
                response = llm_with_tools.invoke(messages)
                responses.append({
                    "agent": agent_name,
                    "response": response.content,
                    "success": True,
                })

        return {
            "subagent_responses": responses,
            "sources": [r["agent"] for r in responses],
        }

    def visualization_node(state: AgentState) -> dict[str, Any]:
        """Nó de visualização que sugere gráficos."""
        responses = state.get("subagent_responses", [])
        query = state["query"]

        responses_text = "\n".join([
            f"{r['agent']}: {r['response'][:500]}" for r in responses
        ])

        viz_prompt = f"""Analise os dados abaixo e determine se há oportunidade de visualização gráfica.

Pergunta original: {query}

Dados dos subagentes:
{responses_text}

Se houver dados numéricos ou comparativos, sugira um tipo de gráfico apropriado.
Pergunte ao usuário se ele gostaria de ver uma visualização.

Responda em formato JSON:
{{
    "has_visualization_opportunity": true/false,
    "chart_type": "bar/line/pie/area/scatter ou null",
    "suggestion": "mensagem para o usuário",
    "chart_data": {{
        "labels": ["lista de labels"],
        "values": [lista de valores],
        "title": "título do gráfico"
    }}
}}"""

        response = llm.invoke([HumanMessage(content=viz_prompt)])

        import json

        try:
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                viz_data = json.loads(content[json_start:json_end])
                suggestion = viz_data.get("suggestion", "")
                chart_data = viz_data.get("chart_data")
            else:
                suggestion = None
                chart_data = None
        except json.JSONDecodeError:
            suggestion = None
            chart_data = None

        return {
            "visualization_suggestion": suggestion,
            "visualization_data": chart_data,
        }

    def critic_node(state: AgentState) -> dict[str, Any]:
        """Nó crítico que valida as respostas."""
        responses = state.get("subagent_responses", [])
        query = state["query"]

        responses_text = "\n".join([
            f"{r['agent']}: {r['response'][:300]}" for r in responses
        ])

        critic_prompt = f"""{CRITIC_AGENT_CONFIG.system_prompt}

Pergunta original: {query}

Respostas dos subagentes:
{responses_text}

Avalie e retorne em JSON:
{{
    "is_valid": true/false,
    "completeness_score": 0-100,
    "issues": [],
    "summary": "resumo da validação"
}}"""

        response = llm.invoke([HumanMessage(content=critic_prompt)])

        import json

        try:
            content = response.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                validation = json.loads(content[json_start:json_end])
            else:
                validation = {"is_valid": True, "completeness_score": 70, "summary": content}
        except json.JSONDecodeError:
            validation = {"is_valid": True, "completeness_score": 70, "summary": response.content}

        return {"validation": validation}

    def response_node(state: AgentState) -> dict[str, Any]:
        """Nó de resposta que formata a saída final."""
        query = state["query"]
        responses = state.get("subagent_responses", [])
        plan = state.get("plan", [])
        validation = state.get("validation", {})
        viz_suggestion = state.get("visualization_suggestion")

        responses_text = "\n".join([
            f"{r['agent']}: {r['response']}" for r in responses
        ])

        plan_text = "\n".join([
            f"{s['step']}. {s['agent']}: {s['task']}" for s in plan
        ])

        response_prompt = f"""{RESPONSE_AGENT_CONFIG.system_prompt}

Pergunta: {query}

Plano executado:
{plan_text}

Respostas dos subagentes:
{responses_text}

Validação: {validation.get('summary', 'OK')}

{"Sugestão de visualização: " + viz_suggestion if viz_suggestion else ""}

Crie uma resposta final clara e completa."""

        response = llm.invoke([HumanMessage(content=response_prompt)])

        final_response = response.content
        if viz_suggestion:
            final_response += f"\n\n---\n**Visualização:** {viz_suggestion}"

        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)],
        }

    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("visualization", visualization_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("response", response_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "visualization")
    workflow.add_edge("visualization", "critic")
    workflow.add_edge("critic", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


class DeepAgentOrchestrator:
    """Orquestrador usando DeepAgents e LangGraph."""

    def __init__(
        self,
        session: SessionContext | None = None,
        use_deep_agent: bool = True,
    ):
        self.session = session
        self.use_deep_agent = use_deep_agent

        if use_deep_agent:
            self.agent = create_deep_orchestrator(session)
        else:
            self.agent = create_langgraph_workflow(session)

    def process_query(
        self,
        query: str,
        theme: str | None = None,
    ) -> dict[str, Any]:
        """
        Processa uma pergunta usando o orquestrador.

        Args:
            query: Pergunta do usuário
            theme: Tema selecionado (opcional)

        Returns:
            Dicionário com resposta e metadados
        """
        if self.session:
            self.session.log_user_query(query, theme)

        if self.use_deep_agent:
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=query)]},
            )
            messages = result.get("messages", [])
            final_message = messages[-1] if messages else None
            response_text = final_message.content if final_message else "Sem resposta"

            return {
                "response": response_text,
                "plan": [],
                "sources": [],
                "visualization_suggestion": None,
                "visualization_data": None,
                "session_id": self.session.session_id if self.session else "",
            }
        else:
            initial_state = {
                "messages": [],
                "query": query,
                "theme": theme,
                "plan": [],
                "subagent_responses": [],
                "validation": {},
                "final_response": "",
                "sources": [],
                "session_id": self.session.session_id if self.session else "",
                "visualization_suggestion": None,
                "visualization_data": None,
            }

            result = self.agent.invoke(initial_state)

            if self.session:
                self.session.log_response(
                    result.get("final_response", ""),
                    result.get("sources", []),
                )

            return {
                "response": result.get("final_response", ""),
                "plan": result.get("plan", []),
                "subagent_responses": result.get("subagent_responses", []),
                "validation": result.get("validation", {}),
                "sources": result.get("sources", []),
                "visualization_suggestion": result.get("visualization_suggestion"),
                "visualization_data": result.get("visualization_data"),
                "session_id": result.get("session_id", ""),
            }


def create_deep_orchestrator_instance(
    session: SessionContext | None = None,
    use_deep_agent: bool = False,
) -> DeepAgentOrchestrator:
    """Factory function para criar o orquestrador."""
    return DeepAgentOrchestrator(session=session, use_deep_agent=use_deep_agent)
