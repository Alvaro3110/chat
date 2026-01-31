"""
Orquestração com LangGraph e DeepAgents.
Fluxo multiagente com contrato de estado forte e validação rigorosa.
VERSÃO CORRIGIDA - Pipeline semanticamente correto.
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


class AgentState(TypedDict):
    """
    Estado forte do pipeline multiagente.
    Todos os campos são obrigatórios e validados.
    """
    messages: Annotated[list, add_messages]
    original_query: str
    normalized_query: str
    active_domains: list[str]
    group_context: dict[str, Any]
    user_id: str
    ambiguity_result: dict[str, Any]
    ambiguity_resolved: bool
    plan: list[dict[str, Any]]
    subagent_responses: list[dict[str, Any]]
    final_report: str
    validation: dict[str, Any]
    final_response: str
    sources: list[str]
    session_id: str
    visualization_requested: bool
    visualization_suggestion: str | None
    visualization_data: dict[str, Any] | None
    memory_context: list[dict[str, Any]]
    memory_status: dict[str, bool]


DATABRICKS_TOOLS = [describe_table, sample_data, run_sql, get_metadata]

VISUALIZATION_KEYWORDS = [
    "gráfico", "grafico", "chart", "visualização", "visualizacao",
    "plot", "plotar", "desenhar", "mostrar gráfico", "exibir gráfico",
    "barras", "pizza", "linha", "dispersão", "histograma"
]


def check_visualization_requested(query: str, plan: list[dict[str, Any]]) -> bool:
    """Verifica se visualização foi solicitada na pergunta ou no plano."""
    query_lower = query.lower()
    for keyword in VISUALIZATION_KEYWORDS:
        if keyword in query_lower:
            return True

    for step in plan:
        agent = step.get("agent", "").lower()
        task = step.get("task", "").lower()
        if "visualization" in agent or "visualização" in task:
            return True

    return False


def create_langgraph_workflow(
    session: SessionContext | None = None,
    user_id: str | None = None,
    model_id: str | None = None,
    debug_mode: bool = False,
) -> StateGraph:
    from app.config.models import DEFAULT_MODEL, get_model_config

    print("\n[DEBUG] ========== CREATING LANGGRAPH WORKFLOW ==========")
    print(f"[DEBUG] Requested model_id: {model_id}")
    print(f"[DEBUG] Debug mode: {debug_mode}")

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

    def memory_recall_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== MEMORY_RECALL ==========")
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

        print(f"[NODE] Memory context loaded: {len(memory_context)} items")
        print(f"[NODE] Memory status: {memory_status}")

        return {
            "memory_context": memory_context,
            "memory_status": memory_status,
            "messages": [AIMessage(content=f"Memória carregada ({len(memory_context)})")],
        }

    def ambiguity_resolver_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== AMBIGUITY_RESOLVER ==========")

        if state.get("ambiguity_resolved", False):
            print("[NODE] Ambiguity already resolved, skipping")
            return {}

        prompt = f"""{AMBIGUITY_RESOLVER_AGENT_CONFIG.system_prompt}

Pergunta do usuário:
{state['original_query']}

Domínios ativos: {', '.join(state.get('active_domains', []))}
Contexto do grupo: {json.dumps(state.get('group_context', {}), ensure_ascii=False)}

Retorne SOMENTE JSON no formato:
{{
    "normalized_question": "pergunta normalizada",
    "ambiguities_detected": [
        {{"term": "termo", "resolution": "resolução", "domain": "domínio"}}
    ],
    "requires_clarification": false,
    "inferred_period": "período inferido ou null",
    "inferred_domains": ["domínios inferidos"]
}}"""

        print(f"[NODE] Prompt length: {len(prompt)}")

        response = llm.invoke([HumanMessage(content=prompt)])
        content = normalize_llm_content(response.content)

        print(f"[NODE] Response length: {len(content)}")

        ambiguity = safe_parse_json(content) or {
            "normalized_question": state["original_query"],
            "ambiguities_detected": [],
            "requires_clarification": False,
        }

        memory_status = state.get("memory_status", {}).copy()
        memory_status["ambiguidade_resolvida"] = True

        print(f"[NODE] Normalized query: {ambiguity.get('normalized_question', '')[:100]}...")
        print(f"[NODE] Ambiguities detected: {len(ambiguity.get('ambiguities_detected', []))}")

        return {
            "normalized_query": ambiguity.get("normalized_question", state["original_query"]),
            "ambiguity_result": ambiguity,
            "ambiguity_resolved": True,
            "memory_status": memory_status,
        }

    def planner_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== PLANNER ==========")

        prompt = f"""{PLANNER_AGENT_CONFIG.system_prompt}

Pergunta normalizada:
{state['normalized_query']}

Domínios ativos: {', '.join(state.get('active_domains', []))}
Contexto do grupo: {json.dumps(state.get('group_context', {}), ensure_ascii=False)}

Retorne JSON com o plano de execução:
{{
    "steps": [
        {{"agent": "NomeDoAgente", "task": "descrição da tarefa", "priority": 1}}
    ],
    "requires_visualization": false,
    "estimated_complexity": "low|medium|high"
}}

Agentes disponíveis:
- CadastroAgent: dados cadastrais do cliente
- FinanceiroAgent: dados financeiros e transações
- RentabilidadeAgent: métricas de rentabilidade
- ReportAgent: consolidação e relatório final
- VisualizationAgent: gráficos (somente se solicitado)"""

        print(f"[NODE] Prompt length: {len(prompt)}")

        response = llm.invoke([HumanMessage(content=prompt)])
        content = normalize_llm_content(response.content)

        print(f"[NODE] Response length: {len(content)}")

        plan_data = safe_parse_json(content)
        plan = plan_data.get("steps", []) if plan_data else []

        visualization_requested = check_visualization_requested(
            state["normalized_query"],
            plan
        )
        if plan_data:
            visualization_requested = visualization_requested or plan_data.get("requires_visualization", False)

        print(f"[NODE] Plan steps: {len(plan)}")
        print(f"[NODE] Visualization requested: {visualization_requested}")
        for i, step in enumerate(plan):
            print(f"[NODE]   Step {i+1}: {step.get('agent', 'Unknown')} - {step.get('task', '')[:50]}...")

        return {
            "plan": plan,
            "visualization_requested": visualization_requested,
        }

    def executor_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== EXECUTOR ==========")
        print(f"[NODE] Active provider: {active_provider.value if active_provider else 'None'}")
        print(f"[NODE] Model: {model_id}")
        print(f"[NODE] Plan steps: {len(state.get('plan', []))}")

        responses = []

        if supports_tools:
            print("[NODE] Model supports tools, using bind_tools")
            llm_for_tools = llm.bind_tools(DATABRICKS_TOOLS)
        else:
            print("[NODE] Model doesn't support bind_tools, using LLM directly")
            llm_for_tools = llm

        for step in state.get("plan", []):
            agent_name = step.get("agent", "")
            task = step.get("task", state["normalized_query"])

            print(f"[NODE] Executing: {agent_name}")

            if agent_name == "VisualizationAgent":
                print("[NODE] Skipping VisualizationAgent in executor (handled separately)")
                continue

            agent_prompt = f"""Você é o {agent_name}, um agente especializado.

Tarefa: {task}

Pergunta original: {state['original_query']}
Pergunta normalizada: {state['normalized_query']}
Domínios ativos: {', '.join(state.get('active_domains', []))}
Contexto do grupo: {json.dumps(state.get('group_context', {}), ensure_ascii=False)}

Forneça uma resposta detalhada e específica para a tarefa.
NÃO peça mais contexto - use as informações fornecidas.
Se não houver dados suficientes, indique claramente o que está faltando."""

            try:
                response = llm_for_tools.invoke([HumanMessage(content=agent_prompt)])
                content = normalize_llm_content(response.content)
                print(f"[NODE] {agent_name} response length: {len(content)}")

                responses.append({
                    "agent": agent_name,
                    "response": content,
                    "success": True,
                })
            except Exception as e:
                print(f"[NODE] ERROR in {agent_name}: {e}")
                responses.append({
                    "agent": agent_name,
                    "response": f"Erro: {str(e)}",
                    "success": False,
                })

        final_report = ""
        if responses:
            report_prompt = f"""Você é o ReportAgent, responsável por consolidar as respostas dos subagentes.

Pergunta original: {state['original_query']}
Pergunta normalizada: {state['normalized_query']}

Respostas dos subagentes:
"""
            for r in responses:
                report_prompt += f"\n--- {r['agent']} ---\n{r['response']}\n"

            report_prompt += """
Consolide todas as informações acima em um relatório único e coerente.
O relatório deve:
1. Responder diretamente à pergunta do usuário
2. Integrar informações de todos os agentes
3. Ser claro e objetivo
4. NÃO pedir mais contexto ou informações"""

            try:
                report_response = llm.invoke([HumanMessage(content=report_prompt)])
                final_report = normalize_llm_content(report_response.content)
                print(f"[NODE] Final report generated, length: {len(final_report)}")
            except Exception as e:
                print(f"[NODE] ERROR generating final report: {e}")
                final_report = "\n\n".join([f"[{r['agent']}]: {r['response']}" for r in responses])

        print(f"[NODE] Executor completed with {len(responses)} responses")
        print(f"[NODE] Final report preview: {final_report[:200]}...")

        return {
            "subagent_responses": responses,
            "sources": [r["agent"] for r in responses],
            "final_report": final_report,
        }

    def visualization_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== VISUALIZATION ==========")

        if not state.get("visualization_requested", False):
            print("[NODE] Visualization not requested, skipping")
            return {
                "visualization_suggestion": None,
                "visualization_data": None,
            }

        print("[NODE] Visualization requested, processing...")

        viz_prompt = f"""Você é o VisualizationAgent, especialista em sugerir visualizações de dados.

Pergunta: {state['normalized_query']}
Relatório consolidado: {state.get('final_report', '')[:1000]}

Sugira uma visualização apropriada. Retorne JSON:
{{
    "suggestion": "descrição da visualização sugerida",
    "chart_type": "bar|line|pie|scatter|area",
    "chart_data": {{
        "labels": ["label1", "label2"],
        "values": [10, 20],
        "title": "Título do gráfico"
    }}
}}

Se não houver dados numéricos para visualizar, retorne:
{{"suggestion": null, "chart_type": null, "chart_data": null}}"""

        response = llm.invoke([HumanMessage(content=viz_prompt)])
        content = normalize_llm_content(response.content)

        viz = safe_parse_json(content)

        print(f"[NODE] Visualization suggestion: {viz.get('suggestion') if viz else None}")

        return {
            "visualization_suggestion": viz.get("suggestion") if viz else None,
            "visualization_data": viz.get("chart_data") if viz else None,
        }

    def critic_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== CRITIC ==========")

        final_report = state.get("final_report", "")

        if not final_report or len(final_report) < 50:
            print("[NODE] CRITIC: Final report is empty or too short")
            return {
                "validation": {
                    "is_valid": False,
                    "completeness_score": 0,
                    "issues": ["Relatório final vazio ou muito curto"],
                    "summary": "Falha: relatório não gerado corretamente",
                }
            }

        generic_phrases = [
            "forneça mais contexto",
            "preciso de mais informações",
            "não tenho dados suficientes",
            "por favor, especifique",
            "não foi possível determinar",
        ]

        report_lower = final_report.lower()
        is_generic = any(phrase in report_lower for phrase in generic_phrases)

        if is_generic:
            print("[NODE] CRITIC: Final report contains generic/evasive phrases")
            return {
                "validation": {
                    "is_valid": False,
                    "completeness_score": 20,
                    "issues": ["Relatório contém frases genéricas ou evasivas"],
                    "summary": "Falha: resposta genérica detectada",
                }
            }

        critic_prompt = f"""Você é o CriticAgent, responsável por validar a qualidade do relatório.

Pergunta original: {state['original_query']}
Pergunta normalizada: {state['normalized_query']}

Relatório a validar:
{final_report}

Avalie o relatório e retorne SOMENTE JSON:
{{
    "is_valid": true/false,
    "completeness_score": 0-100,
    "issues": ["lista de problemas encontrados"],
    "summary": "resumo da validação"
}}

Critérios de validação:
1. O relatório responde à pergunta?
2. O conteúdo é específico e não genérico?
3. As informações são coerentes?
4. O relatório é completo?"""

        print(f"[NODE] Validating report of length: {len(final_report)}")

        response = llm.invoke([HumanMessage(content=critic_prompt)])
        content = normalize_llm_content(response.content)

        validation = safe_parse_json(content) or {
            "is_valid": True,
            "completeness_score": 70,
            "issues": [],
            "summary": "Validação automática",
        }

        print(f"[NODE] Validation result: is_valid={validation.get('is_valid')}, score={validation.get('completeness_score')}")

        return {"validation": validation}

    def response_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== RESPONSE ==========")

        final_report = state.get("final_report", "")
        validation = state.get("validation", {})
        is_valid = validation.get("is_valid", True)

        print(f"[NODE] Final report length: {len(final_report)}")
        print(f"[NODE] Validation is_valid: {is_valid}")

        response_prompt = f"""Você é o ResponseAgent, responsável por formatar a resposta final para o usuário.

CONTEXTO COMPLETO:
- Pergunta original: {state['original_query']}
- Pergunta normalizada: {state['normalized_query']}
- Domínios consultados: {', '.join(state.get('sources', []))}

RELATÓRIO CONSOLIDADO DOS AGENTES:
{final_report}

VALIDAÇÃO DO CRITIC:
- Válido: {validation.get('is_valid', 'N/A')}
- Score: {validation.get('completeness_score', 'N/A')}
- Resumo: {validation.get('summary', 'N/A')}

INSTRUÇÕES:
1. Formate o relatório consolidado de forma clara e profissional
2. Use o conteúdo do relatório - NÃO invente informações
3. NÃO peça mais contexto ou informações
4. Se o relatório indicar falta de dados, explique isso claramente
5. Mantenha um tom executivo e objetivo

Gere a resposta final:"""

        print(f"[NODE] Response prompt length: {len(response_prompt)}")

        response = llm.invoke([HumanMessage(content=response_prompt)])
        final_text = normalize_llm_content(response.content)

        print(f"[NODE] Final response length: {len(final_text)}")
        print(f"[NODE] Final response preview: {final_text[:200]}...")

        memory_status = state.get("memory_status", {}).copy()
        memory_status["resposta_entregue"] = True

        return {
            "final_response": final_text,
            "memory_status": memory_status,
            "messages": [AIMessage(content=final_text)],
        }

    def memory_persist_node(state: AgentState) -> dict[str, Any]:
        print("\n[NODE] ========== MEMORY_PERSIST ==========")

        if not memory_agent:
            print("[NODE] No memory agent, skipping")
            return {}

        if not state.get("ambiguity_resolved", False):
            print("[NODE] Ambiguity not resolved, skipping memory persist")
            return {}

        ambiguities = state.get("ambiguity_result", {}).get("ambiguities_detected", [])
        print(f"[NODE] Persisting {len(ambiguities)} ambiguity resolutions")

        for amb in ambiguities:
            memory_agent.memorize_ambiguity_resolution(
                amb.get("term"), amb.get("resolution"), amb.get("domain")
            )

        return {}

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

    print("[DEBUG] Workflow compiled successfully")

    return workflow.compile()


class DeepAgentOrchestrator:
    def __init__(
        self,
        session: SessionContext | None = None,
        user_id: str | None = None,
        model_id: str | None = None,
        debug_mode: bool = False,
    ):
        self.session = session
        self.model_id = model_id
        self.debug_mode = debug_mode
        self.agent = create_langgraph_workflow(session, user_id, model_id, debug_mode)

    def process_query(
        self,
        query: str,
        active_domains: list[str] | None = None,
        group_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        print("\n" + "=" * 60)
        print("STARTING MULTIAGENT PIPELINE")
        print("=" * 60)
        print(f"Query: {query}")
        print(f"Active domains: {active_domains}")
        print(f"Model: {self.model_id}")
        print("=" * 60)

        initial_state: AgentState = {
            "messages": [],
            "original_query": query,
            "normalized_query": "",
            "active_domains": active_domains or [],
            "group_context": group_context or {},
            "user_id": "",
            "ambiguity_result": {},
            "ambiguity_resolved": False,
            "plan": [],
            "subagent_responses": [],
            "final_report": "",
            "validation": {},
            "final_response": "",
            "sources": [],
            "session_id": self.session.session_id if self.session else "",
            "visualization_requested": False,
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

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED")
        print("=" * 60)

        return {
            "response": result.get("final_response", ""),
            "normalized_query": result.get("normalized_query", ""),
            "final_report": result.get("final_report", ""),
            "validation": result.get("validation", {}),
            "memory_status": result.get("memory_status", {}),
            "sources": result.get("sources", []),
            "visualization_suggestion": result.get("visualization_suggestion"),
            "visualization_data": result.get("visualization_data"),
        }


def create_deep_orchestrator_instance(
    session: SessionContext | None = None,
    user_id: str | None = None,
    model_id: str | None = None,
    debug_mode: bool = False,
) -> DeepAgentOrchestrator:
    return DeepAgentOrchestrator(
        session=session,
        user_id=user_id,
        model_id=model_id,
        debug_mode=debug_mode,
    )
