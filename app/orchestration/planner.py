"""
Agente Planejador (PlannerAgent).
Analisa a intenção da pergunta e gera um plano de ações.
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

    @property
    def llm(self) -> ChatOpenAI:
        """Retorna instância do LLM lazy-loaded."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
            )
        return self._llm

    def analyze_query(self, query: str) -> dict[str, Any]:
        """
        Analisa a pergunta e identifica os domínios necessários.

        Args:
            query: Pergunta do usuário

        Returns:
            Dicionário com análise da pergunta
        """
        available_themes = get_available_themes()

        analysis_prompt = f"""Analise a seguinte pergunta e identifique:
1. Quais domínios de dados são necessários para responder
2. Se a pergunta é simples (um domínio) ou complexa (múltiplos domínios)
3. A ordem de execução recomendada

Domínios disponíveis: {', '.join(available_themes)}

Pergunta: {query}

Responda em formato JSON com a seguinte estrutura:
{{
    "domains": ["lista de domínios necessários"],
    "is_complex": true/false,
    "execution_order": ["ordem de execução dos domínios"],
    "reasoning": "explicação da análise"
}}"""

        messages = [
            SystemMessage(content=self.config.system_prompt),
            HumanMessage(content=analysis_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content

        try:
            import json

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                analysis = json.loads(content[json_start:json_end])
            else:
                analysis = {
                    "domains": available_themes[:1],
                    "is_complex": False,
                    "execution_order": available_themes[:1],
                    "reasoning": content,
                }
        except json.JSONDecodeError:
            analysis = {
                "domains": available_themes[:1],
                "is_complex": False,
                "execution_order": available_themes[:1],
                "reasoning": content,
            }

        return analysis

    def create_plan(self, query: str, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Cria um plano de execução baseado na análise.

        Args:
            query: Pergunta original
            analysis: Resultado da análise

        Returns:
            Lista de etapas do plano
        """
        plan = []
        domains = analysis.get("execution_order", analysis.get("domains", []))

        for i, domain in enumerate(domains, 1):
            step = {
                "step": i,
                "agent": f"{domain.capitalize()}Agent",
                "domain": domain,
                "task": f"Consultar dados de {domain} para responder: {query}",
                "status": "pending",
            }
            plan.append(step)

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

    def invoke(self, query: str) -> dict[str, Any]:
        """
        Executa o planejamento completo.

        Args:
            query: Pergunta do usuário

        Returns:
            Dicionário com análise e plano
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
