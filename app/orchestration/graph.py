"""
Orquestração com LangGraph e DeepAgents.
Implementa o fluxo de agentes usando StateGraph com desambiguação.
Suporta múltiplos provedores de LLM (OpenAI e Google Gemini).

Fluxo obrigatório:
User Input → AmbiguityResolverAgent → PlannerAgent → Subagentes → CriticAgent → ResponseAgent
"""

import json
from typing import Annotated, Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.config.agents import (
    AMBIGUITY_RESOLVER_AGENT_CONFIG,
    CADASTRO_AGENT_CONFIG,
    CRITIC_AGENT_CONFIG,
    FINANCEIRO_AGENT_CONFIG,
    PLANNER_AGENT_CONFIG,
    RENTABILIDADE_AGENT_CONFIG,
    RESPONSE_AGENT_CONFIG,
    VISUALIZATION_AGENT_CONFIG,
)
from app.config.llm import DEFAULT_MODEL, create_llm
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
    original_query: str
    normalized_query: str
    active_domains: list[str]
    ambiguity_result: dict[str, Any]
    plan: list[dict[str, Any]]
    subagent_responses: list[dict[str, Any]]
    validation: dict[str, Any]
    final_response: str
    sources: list[str]
    session_id: str
    visualization_suggestion: str | None
    visualization_data: dict[str, Any] | None


DATABRICKS_TOOLS = [describe_table, sample_data, run_sql, get_metadata]


def parse_json_response(content: str) -> dict[str, Any] | None:
    """Extrai JSON de uma resposta do LLM."""
    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(content[json_start:json_end])
    except json.JSONDecodeError:
        pass
    return None


def create_langgraph_workflow(
    session: SessionContext | None = None,
    model_id: str | None = None,
    llm: BaseChatModel | None = None,
) -> StateGraph:
    """
    Cria o workflow usando LangGraph com fluxo de desambiguação.

    Fluxo: AmbiguityResolver → Planner → Executor → Visualization → Critic → Response

    Args:
        session: Contexto da sessão
        model_id: ID do modelo LLM a usar (ex: "gpt-4o-mini", "gemini-1.5-flash")
        llm: Instância do LLM já configurada (opcional, sobrescreve model_id)

    Returns:
        Grafo compilado
    """
    if llm is None:
        llm = create_llm(model_id or DEFAULT_MODEL)

    def ambiguity_resolver_node(state: AgentState) -> dict[str, Any]:
        """
        Nó de desambiguação - PRIMEIRO nó do fluxo.
        Analisa a pergunta original e produz versão normalizada.
        """
        original_query = state["original_query"]
        active_domains = state.get("active_domains", [])

        domains_text = ", ".join(active_domains) if active_domains else "todos os domínios"

        prompt = f"""{AMBIGUITY_RESOLVER_AGENT_CONFIG.system_prompt}

Domínios ativos selecionados pelo usuário: {domains_text}

Pergunta do usuário: {original_query}

Analise a pergunta e retorne o JSON com a desambiguação."""

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        ambiguity_result = parse_json_response(content)

        if ambiguity_result:
            normalized_query = ambiguity_result.get("normalized_question", original_query)
        else:
            ambiguity_result = {
                "original_question": original_query,
                "normalized_question": original_query,
                "ambiguities_detected": [],
                "inferred_domains": active_domains,
                "inferred_period": None,
                "requires_clarification": False,
            }
            normalized_query = original_query

        return {
            "normalized_query": normalized_query,
            "ambiguity_result": ambiguity_result,
            "messages": [AIMessage(content=f"Pergunta normalizada: {normalized_query}")],
        }

    def planner_node(state: AgentState) -> dict[str, Any]:
        """
        Nó do planejador - recebe pergunta JÁ DESAMBIGUADA.
        """
        normalized_query = state.get("normalized_query", state["original_query"])
        active_domains = state.get("active_domains", [])
        ambiguity_result = state.get("ambiguity_result", {})

        inferred_domains = ambiguity_result.get("inferred_domains", active_domains)
        domains_to_use = list(set(active_domains) & set(inferred_domains)) if active_domains else inferred_domains

        if not domains_to_use:
            domains_to_use = active_domains if active_domains else ["cadastro", "financeiro", "rentabilidade"]

        domains_text = ", ".join(domains_to_use)

        prompt = f"""{PLANNER_AGENT_CONFIG.system_prompt}

Domínios ativos: {domains_text}
Pergunta desambiguada: {normalized_query}

Crie um plano de execução considerando apenas os domínios ativos."""

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        plan_data = parse_json_response(content)

        if plan_data:
            plan = plan_data.get("steps", [])
        else:
            plan = []
            for domain in domains_to_use:
                plan.append({
                    "step": len(plan) + 1,
                    "agent": f"{domain.capitalize()}Agent",
                    "task": normalized_query,
                })

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
        """Nó executor que processa os subagentes temáticos."""
        normalized_query = state.get("normalized_query", state["original_query"])
        plan = state.get("plan", [])
        active_domains = state.get("active_domains", [])
        responses = []

        llm_with_tools = llm.bind_tools(DATABRICKS_TOOLS)

        for step in plan:
            agent_name = step.get("agent", "")
            task = step.get("task", normalized_query)

            if agent_name == "VisualizationAgent":
                continue

            config = None
            domain = None

            if "cadastro" in agent_name.lower():
                config = CADASTRO_AGENT_CONFIG
                domain = "cadastro"
            elif "financeiro" in agent_name.lower():
                config = FINANCEIRO_AGENT_CONFIG
                domain = "financeiro"
            elif "rentabilidade" in agent_name.lower():
                config = RENTABILIDADE_AGENT_CONFIG
                domain = "rentabilidade"

            if config and (not active_domains or domain in active_domains):
                messages = [
                    HumanMessage(content=f"{config.system_prompt}\n\nTarefa: {task}"),
                ]
                response = llm_with_tools.invoke(messages)
                responses.append({
                    "agent": agent_name,
                    "domain": domain,
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
        normalized_query = state.get("normalized_query", state["original_query"])

        if not responses:
            return {
                "visualization_suggestion": None,
                "visualization_data": None,
            }

        responses_text = "\n".join([
            f"{r['agent']}: {r['response'][:500]}" for r in responses
        ])

        prompt = f"""{VISUALIZATION_AGENT_CONFIG.system_prompt}

Pergunta: {normalized_query}

Dados dos subagentes:
{responses_text}

Analise e retorne em formato JSON:
{{
    "has_visualization_opportunity": true/false,
    "chart_type": "bar/line/pie/area/scatter ou null",
    "suggestion": "mensagem para o usuário perguntando se deseja ver o gráfico",
    "chart_data": {{
        "chart_type": "tipo do gráfico",
        "title": "título do gráfico",
        "labels": ["lista de labels"],
        "datasets": [{{"name": "nome", "values": [valores]}}]
    }}
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        viz_data = parse_json_response(content)

        if viz_data and viz_data.get("has_visualization_opportunity"):
            suggestion = viz_data.get("suggestion", "")
            chart_data = viz_data.get("chart_data")
        else:
            suggestion = None
            chart_data = None

        return {
            "visualization_suggestion": suggestion,
            "visualization_data": chart_data,
        }

    def critic_node(state: AgentState) -> dict[str, Any]:
        """Nó crítico que valida as respostas."""
        responses = state.get("subagent_responses", [])
        normalized_query = state.get("normalized_query", state["original_query"])
        plan = state.get("plan", [])

        if not responses:
            return {
                "validation": {
                    "is_valid": False,
                    "completeness_score": 0,
                    "issues": ["Nenhuma resposta dos subagentes"],
                    "summary": "Não foi possível obter respostas dos subagentes.",
                }
            }

        responses_text = "\n".join([
            f"{r['agent']}: {r['response'][:300]}" for r in responses
        ])

        plan_text = "\n".join([
            f"{s['step']}. {s['agent']}: {s['task']}" for s in plan if s['agent'] != 'VisualizationAgent'
        ])

        prompt = f"""{CRITIC_AGENT_CONFIG.system_prompt}

Pergunta: {normalized_query}

Plano executado:
{plan_text}

Respostas dos subagentes:
{responses_text}

Avalie e retorne em JSON:
{{
    "is_valid": true/false,
    "completeness_score": 0-100,
    "adherence_to_plan": true/false,
    "issues": [],
    "summary": "resumo da validação"
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        validation = parse_json_response(content)

        if not validation:
            validation = {
                "is_valid": True,
                "completeness_score": 70,
                "adherence_to_plan": True,
                "issues": [],
                "summary": response.content,
            }

        return {"validation": validation}

    def response_node(state: AgentState) -> dict[str, Any]:
        """Nó de resposta que formata a saída final."""
        original_query = state["original_query"]
        normalized_query = state.get("normalized_query", original_query)
        responses = state.get("subagent_responses", [])
        plan = state.get("plan", [])
        validation = state.get("validation", {})
        viz_suggestion = state.get("visualization_suggestion")
        ambiguity_result = state.get("ambiguity_result", {})

        responses_text = "\n".join([
            f"{r['agent']}: {r['response']}" for r in responses
        ])

        plan_text = "\n".join([
            f"{s['step']}. {s['agent']}: {s['task']}" for s in plan if s['agent'] != 'VisualizationAgent'
        ])

        ambiguities = ambiguity_result.get("ambiguities_detected", [])
        ambiguity_text = ""
        if ambiguities:
            ambiguity_text = "\n".join([
                f"- {a.get('term', '')} → {a.get('resolution', '')}" for a in ambiguities
            ])

        prompt = f"""{RESPONSE_AGENT_CONFIG.system_prompt}

Pergunta original: {original_query}
Pergunta interpretada: {normalized_query}

{"Ajustes de interpretação:" + chr(10) + ambiguity_text if ambiguity_text else ""}

Plano executado:
{plan_text}

Respostas dos subagentes:
{responses_text}

Validação: {validation.get('summary', 'OK')}

{"Sugestão de visualização disponível: " + viz_suggestion if viz_suggestion else ""}

Crie uma resposta final clara, completa e em linguagem executiva."""

        response = llm.invoke([HumanMessage(content=prompt)])

        final_response = response.content

        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)],
        }

    workflow = StateGraph(AgentState)

    workflow.add_node("ambiguity_resolver", ambiguity_resolver_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("visualization", visualization_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("response", response_node)

    workflow.set_entry_point("ambiguity_resolver")
    workflow.add_edge("ambiguity_resolver", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "visualization")
    workflow.add_edge("visualization", "critic")
    workflow.add_edge("critic", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


class DeepAgentOrchestrator:
    """Orquestrador usando LangGraph com fluxo de desambiguação."""

    def __init__(
        self,
        session: SessionContext | None = None,
        model_id: str | None = None,
    ):
        self.session = session
        self.model_id = model_id or DEFAULT_MODEL
        self.agent = create_langgraph_workflow(session, model_id=self.model_id)

    def process_query(
        self,
        query: str,
        active_domains: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Processa uma pergunta usando o orquestrador com desambiguação.

        Args:
            query: Pergunta do usuário
            active_domains: Lista de domínios ativos selecionados pelo usuário

        Returns:
            Dicionário com resposta e metadados incluindo desambiguação
        """
        if self.session:
            self.session.log_user_query(query, str(active_domains))

        if active_domains is None:
            active_domains = []

        initial_state: AgentState = {
            "messages": [],
            "original_query": query,
            "normalized_query": "",
            "active_domains": active_domains,
            "ambiguity_result": {},
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
            "original_query": result.get("original_query", query),
            "normalized_query": result.get("normalized_query", query),
            "ambiguity_result": result.get("ambiguity_result", {}),
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
    model_id: str | None = None,
) -> DeepAgentOrchestrator:
    """Factory function para criar o orquestrador."""
    return DeepAgentOrchestrator(session=session, model_id=model_id)
