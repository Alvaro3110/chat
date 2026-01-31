"""
Orquestração com LangGraph e DeepAgents.
Fluxo com desambiguação, memória e validação.
VERSÃO ENTERPRISE-SAFE com debugging detalhado.
"""

import json
import logging
import traceback
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.config.agents import (
    AMBIGUITY_RESOLVER_AGENT_CONFIG,
    PLANNER_AGENT_CONFIG,
)
from app.governance.logging import SessionContext
from app.memory.memory_agent import MemoryAgent, create_memory_agent
from app.tools.databricks_tools import (
    describe_table,
    get_metadata,
    run_sql,
    sample_data,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# ---------------------------------------------------------------------
# Helpers globais (CRÍTICOS)
# ---------------------------------------------------------------------
def normalize_llm_content(content: Any) -> str:
    """Normaliza QUALQUER retorno do LLM para string."""
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    if isinstance(content, dict):
        return str(content)

    return str(content)


def safe_parse_json(text: str) -> dict[str, Any] | None:
    """Extrai JSON de texto livre sem lançar exceção."""
    if not text:
        return None

    try:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end <= start:
            return None

        parsed = json.loads(text[start:end])
        return parsed if isinstance(parsed, dict) else None

    except Exception:
        return None


# ---------------------------------------------------------------------
# Estado do Grafo
# ---------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    original_query: str
    normalized_query: str
    active_domains: list[str]
    group_context: dict[str, Any]
    user_id: str
    ambiguity_result: dict[str, Any]
    plan: list[dict[str, Any]]
    subagent_responses: list[dict[str, Any]]
    validation: dict[str, Any]
    final_response: str
    sources: list[str]
    session_id: str
    visualization_suggestion: str | None
    visualization_data: dict[str, Any] | None
    memory_context: list[dict[str, Any]]
    memory_status: dict[str, bool]


DATABRICKS_TOOLS = [describe_table, sample_data, run_sql, get_metadata]


# ---------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------
def create_langgraph_workflow(
    session: SessionContext | None = None,
    user_id: str | None = None,
    model_id: str | None = None,
) -> StateGraph:
    from app.config.models import DEFAULT_MODEL, get_model_config

    print("\n[DEBUG] ========== CREATING LANGGRAPH WORKFLOW ==========")
    print(f"[DEBUG] Requested model_id: {model_id}")

    if not model_id:
        model_id = DEFAULT_MODEL
        print(f"[DEBUG] No model_id provided, using DEFAULT_MODEL: {model_id}")

    model_config = get_model_config(model_id)
    supports_tools = False
    llm = None
    active_provider = None

    if model_config:
        print(f"[DEBUG] Model config found: {model_config.display_name}")
        print(f"[DEBUG] Provider: {model_config.provider.value}")
        print(f"[DEBUG] Endpoint: {model_config.endpoint_name or model_config.model_name}")
        print(f"[DEBUG] Supports tools: {model_config.supports_tools}")
        supports_tools = model_config.supports_tools
        active_provider = model_config.provider

        try:
            from app.config.llm import create_llm
            llm = create_llm(model_id=model_id, temperature=0)
            print(f"[DEBUG] LLM created successfully: {type(llm).__name__}")
        except Exception as e:
            print(f"[DEBUG] ERROR creating LLM: {e}")
            print(f"[DEBUG] Stack trace:\n{traceback.format_exc()}")
            print("[DEBUG] CRITICAL: LLM creation failed. NOT using silent fallback.")
            print("[DEBUG] CRITICAL: Please check your Databricks credentials and endpoint configuration.")
            raise RuntimeError(f"Failed to create LLM for model {model_id}: {e}") from e
    else:
        print(f"[DEBUG] ERROR: Model config not found for: {model_id}")
        print("[DEBUG] CRITICAL: Invalid model_id. NOT using silent fallback.")
        raise ValueError(f"Model config not found for: {model_id}")

    print(f"[DEBUG] Active provider: {active_provider.value if active_provider else 'None'}")
    print("[DEBUG] ========== WORKFLOW SETUP COMPLETE ==========\n")

    memory_agent: MemoryAgent | None = create_memory_agent(user_id) if user_id else None

    # -----------------------------------------------------------------
    def memory_recall_node(state: AgentState) -> dict[str, Any]:
        memory_context = []
        memory_status = state.get("memory_status", {}).copy()

        if memory_agent:
            memories = memory_agent.recall_ambiguity_resolutions(
                state["original_query"]
            )[:5]

            for mem in memories:
                memory_context.append({
                    "tipo": "ambiguidade",
                    "conteudo": mem.conteudo,
                    "dominio": mem.dominio,
                })

            memory_status["memoria_consultada"] = True
        else:
            memory_status["memoria_consultada"] = False

        memory_status["contexto_carregado"] = True

        return {
            "memory_context": memory_context,
            "memory_status": memory_status,
            "messages": [AIMessage(content=f"Memória carregada ({len(memory_context)})")],
        }

    # -----------------------------------------------------------------
    def ambiguity_resolver_node(state: AgentState) -> dict[str, Any]:
        prompt = f"""{AMBIGUITY_RESOLVER_AGENT_CONFIG.system_prompt}

Pergunta do usuário:
{state['original_query']}

Retorne SOMENTE JSON."""
        response = llm.invoke([HumanMessage(content=prompt)])
        content = normalize_llm_content(response.content)

        ambiguity = safe_parse_json(content) or {
            "normalized_question": state["original_query"],
            "ambiguities_detected": [],
            "requires_clarification": False,
        }

        return {
            "normalized_query": ambiguity.get(
                "normalized_question", state["original_query"]
            ),
            "ambiguity_result": ambiguity,
        }

    # -----------------------------------------------------------------
    def planner_node(state: AgentState) -> dict[str, Any]:
        prompt = f"""{PLANNER_AGENT_CONFIG.system_prompt}

Pergunta:
{state['normalized_query']}

Retorne JSON com o plano."""
        response = llm.invoke([HumanMessage(content=prompt)])
        content = normalize_llm_content(response.content)

        plan_data = safe_parse_json(content)
        plan = plan_data.get("steps", []) if plan_data else []

        return {"plan": plan}

    # -----------------------------------------------------------------
    def executor_node(state: AgentState) -> dict[str, Any]:
        print("\n[DEBUG] ========== EXECUTOR NODE ==========")
        print(f"[DEBUG] Active provider: {active_provider.value if active_provider else 'None'}")
        print(f"[DEBUG] Model: {model_id}")
        responses = []

        if supports_tools:
            print("[DEBUG] Model supports tools, using bind_tools")
            llm_for_tools = llm.bind_tools(DATABRICKS_TOOLS)
        else:
            print("[DEBUG] Model doesn't support bind_tools, using LLM directly")
            print("[DEBUG] NOTE: Databricks models don't support LangChain bind_tools")
            llm_for_tools = llm

        for step in state.get("plan", []):
            agent_name = step.get("agent", "")
            task = step.get("task", state["normalized_query"])

            print(f"[DEBUG] Executing step: agent={agent_name}, task_preview={task[:100]}...")

            if agent_name == "VisualizationAgent":
                print("[DEBUG] Skipping VisualizationAgent")
                continue

            try:
                print("[DEBUG] Invoking LLM for task...")
                response = llm_for_tools.invoke([HumanMessage(content=task)])
                content = normalize_llm_content(response.content)
                print(f"[DEBUG] Response received, content_length={len(content)}")

                responses.append({
                    "agent": agent_name,
                    "response": content,
                    "success": True,
                })
            except Exception as e:
                print(f"[DEBUG] ERROR in executor: {e}")
                print(f"[DEBUG] Stack trace:\n{traceback.format_exc()}")
                responses.append({
                    "agent": agent_name,
                    "response": f"Erro: {str(e)}",
                    "success": False,
                })

        print(f"[DEBUG] Executor completed with {len(responses)} responses")
        print("[DEBUG] ========== EXECUTOR NODE END ==========\n")

        return {
            "subagent_responses": responses,
            "sources": [r["agent"] for r in responses],
        }

    # -----------------------------------------------------------------
    def visualization_node(state: AgentState) -> dict[str, Any]:
        response = llm.invoke([HumanMessage(content="Avalie visualização.")])
        content = normalize_llm_content(response.content)

        viz = safe_parse_json(content)
        return {
            "visualization_suggestion": viz.get("suggestion") if viz else None,
            "visualization_data": viz.get("chart_data") if viz else None,
        }

    # -----------------------------------------------------------------
    def critic_node(state: AgentState) -> dict[str, Any]:
        response = llm.invoke([HumanMessage(content="Valide respostas.")])
        content = normalize_llm_content(response.content)

        validation = safe_parse_json(content) or {
            "is_valid": True,
            "completeness_score": 70,
            "summary": content,
        }

        return {"validation": validation}

    # -----------------------------------------------------------------
    def response_node(state: AgentState) -> dict[str, Any]:
        response = llm.invoke([HumanMessage(content="Gere resposta final.")])
        final_text = normalize_llm_content(response.content)

        memory_status = state.get("memory_status", {}).copy()
        memory_status["resposta_entregue"] = True

        return {
            "final_response": final_text,
            "memory_status": memory_status,
            "messages": [AIMessage(content=final_text)],
        }

    # -----------------------------------------------------------------
    def memory_persist_node(state: AgentState) -> dict[str, Any]:
        if not memory_agent:
            return {}

        ambiguities = state.get("ambiguity_result", {}).get("ambiguities_detected", [])
        for amb in ambiguities:
            memory_agent.memorize_ambiguity_resolution(
                amb.get("term"), amb.get("resolution"), amb.get("domain")
            )
        return {}

    # -----------------------------------------------------------------
    workflow = StateGraph(AgentState)

    workflow.add_node("memory_recall", memory_recall_node)
    workflow.add_node("ambiguity_resolver", ambiguity_resolver_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("visualization", visualization_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("response", response_node)
    workflow.add_node("memory_persist", memory_persist_node)

    workflow.set_entry_point("memory_recall")
    workflow.add_edge("memory_recall", "ambiguity_resolver")
    workflow.add_edge("ambiguity_resolver", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "visualization")
    workflow.add_edge("visualization", "critic")
    workflow.add_edge("critic", "response")
    workflow.add_edge("response", "memory_persist")
    workflow.add_edge("memory_persist", END)

    return workflow.compile()


# ---------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------
class DeepAgentOrchestrator:
    def __init__(
        self,
        session: SessionContext | None = None,
        user_id: str | None = None,
        model_id: str | None = None,
    ):
        self.session = session
        self.agent = create_langgraph_workflow(session, user_id, model_id)

    def process_query(
        self,
        query: str,
        active_domains: list[str] | None = None,
        group_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        initial_state: AgentState = {
            "messages": [],
            "original_query": query,
            "normalized_query": "",
            "active_domains": active_domains or [],
            "group_context": group_context or {},
            "user_id": "",
            "ambiguity_result": {},
            "plan": [],
            "subagent_responses": [],
            "validation": {},
            "final_response": "",
            "sources": [],
            "session_id": self.session.session_id if self.session else "",
            "visualization_suggestion": None,
            "visualization_data": None,
            "memory_context": [],
            "memory_status": {
                "contexto_carregado": False,
                "memoria_consultada": False,
                "ambiguidade_resolvida": False,
                "resposta_entregue": False,
            },
        }

        result = self.agent.invoke(initial_state)

        return {
            "response": result.get("final_response", ""),
            "normalized_query": result.get("normalized_query", ""),
            "validation": result.get("validation", {}),
            "memory_status": result.get("memory_status", {}),
        }


def create_deep_orchestrator_instance(
    session: SessionContext | None = None,
    user_id: str | None = None,
    model_id: str | None = None,
) -> DeepAgentOrchestrator:
    return DeepAgentOrchestrator(session=session, user_id=user_id, model_id=model_id)
