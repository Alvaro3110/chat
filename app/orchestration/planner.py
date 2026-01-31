"""
Agente Planejador (PlannerAgent).
Analisa a intenção da pergunta e gera um plano de ações.

VERSÃO ENTERPRISE-SAFE:
- Normaliza response.content
- Parsing JSON defensivo
- Compatível com OpenAI / Databricks
- Nunca quebra o pipeline
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config.agents import PLANNER_AGENT_CONFIG, get_available_themes
from app.governance.logging import SessionContext


class PlannerAgent:
    """Agente responsável por planejar a execução de tarefas."""

    def __init__(
        self,
        session: SessionContext | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        self.config = PLANNER_AGENT_CONFIG
        self.session = session
        self.model_name = model_name
        self._llm = None

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
            )
        return self._llm

    # ------------------------------------------------------------------
    # Helpers internos (CRÍTICOS)
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_llm_content(content: Any) -> str:
        """
        Normaliza QUALQUER retorno do LLM para string.
        Pode receber: str | list | dict | None
        """
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(
                        str(item.get("text") or item.get("content") or item)
                    )
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        if isinstance(content, dict):
            return str(content)

        return str(content)

    @staticmethod
    def _safe_parse_json(text: str) -> dict[str, Any] | None:
        """
        Extrai JSON de texto livre de forma defensiva.
        Nunca lança exceção.
        """
        import json

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

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------
    def analyze_query(self, query: str) -> dict[str, Any]:
        """
        Analisa a pergunta e identifica os domínios necessários.
        """
        available_themes = get_available_themes()

        analysis_prompt = f"""
Analise a seguinte pergunta e identifique:
1. Quais domínios de dados são necessários para responder
2. Se a pergunta é simples (um domínio) ou complexa (múltiplos domínios)
3. A ordem de execução recomendada

Domínios disponíveis: {', '.join(available_themes)}

Pergunta: {query}

Responda SOMENTE com um JSON válido:
{{
  "domains": ["lista de domínios necessários"],
  "is_complex": true/false,
  "execution_order": ["ordem de execução dos domínios"],
  "reasoning": "explicação da análise"
}}
""".strip()

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=analysis_prompt),
        ]

        response = self.llm.invoke(messages)
        content = self._normalize_llm_content(
            getattr(response, "content", response)
        )

        parsed = self._safe_parse_json(content)

        if parsed:
            analysis = parsed
        else:
            # Fallback seguro
            default_domain = available_themes[:1] if available_themes else []
            analysis = {
                "domains": default_domain,
                "is_complex": False,
                "execution_order": default_domain,
                "reasoning": content or "Fallback: análise não estruturada.",
            }

        return analysis

    # ------------------------------------------------------------------
    def create_plan(self, query: str, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Cria um plano de execução baseado na análise.
        """
        plan: list[dict[str, Any]] = []

        domains = analysis.get(
            "execution_order",
            analysis.get("domains", []),
        )

        for i, domain in enumerate(domains, 1):
            plan.append({
                "step": i,
                "agent": f"{domain.capitalize()}Agent",
                "domain": domain,
                "task": f"Consultar dados de {domain} para responder: {query}",
                "status": "pending",
            })

        plan.append({
            "step": len(plan) + 1,
            "agent": "CriticAgent",
            "domain": "validation",
            "task": "Validar consistência e completude das respostas",
            "status": "pending",
        })

        plan.append({
            "step": len(plan) + 1,
            "agent": "ResponseAgent",
            "domain": "response",
            "task": "Formatar resposta final para o usuário",
            "status": "pending",
        })

        if self.session:
            self.session.log_plan([step["task"] for step in plan])

        return plan

    # ------------------------------------------------------------------
    def invoke(self, query: str) -> dict[str, Any]:
        """
        Executa o planejamento completo.
        """
        if self.session:
            self.session.log_agent_call(self.config.name, query)

        analysis = self.analyze_query(query)
        plan = self.create_plan(query, analysis)

        return {
            "query": query,
            "analysis": analysis,
            "plan": plan,
        }


def create_planner_agent(session: SessionContext | None = None) -> PlannerAgent:
    """Factory function para criar PlannerAgent."""
    return PlannerAgent(session=session)
