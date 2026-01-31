"""
Orquestrador principal da plataforma multiagente.
Coordena a execução dos subagentes e agentes de orquestração.
"""

from typing import Any

from app.agents.cadastro.agent import create_cadastro_agent
from app.agents.financeiro.agent import create_financeiro_agent
from app.agents.rentabilidade.agent import create_rentabilidade_agent
from app.governance.logging import SessionContext, get_governance_manager
from app.orchestration.critic import create_critic_agent
from app.orchestration.planner import create_planner_agent
from app.orchestration.response import create_response_agent


class Orchestrator:
    """Orquestrador principal que coordena todos os agentes."""

    def __init__(self, session: SessionContext | None = None):
        self.session = session or get_governance_manager().create_session()
        self.planner = create_planner_agent(self.session)
        self.critic = create_critic_agent(self.session)
        self.response_agent = create_response_agent(self.session)

        self.subagents = {
            "cadastro": create_cadastro_agent(self.session),
            "financeiro": create_financeiro_agent(self.session),
            "rentabilidade": create_rentabilidade_agent(self.session),
        }

    def _get_agent_for_domain(self, domain: str):
        """Retorna o agente apropriado para um domínio."""
        return self.subagents.get(domain.lower())

    def execute_plan(
        self,
        query: str,
        plan: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Executa o plano de ações.

        Args:
            query: Pergunta original
            plan: Plano de execução

        Returns:
            Lista de respostas dos subagentes
        """
        responses = []

        for step in plan:
            domain = step.get("domain", "")
            agent = self._get_agent_for_domain(domain)

            if agent:
                step["status"] = "in_progress"
                result = agent.invoke(query)
                step["status"] = "completed"
                responses.append(result)

        return responses

    def process_query(
        self,
        query: str,
        chat_history: list | None = None,
    ) -> dict[str, Any]:
        """
        Processa uma pergunta do usuário através do pipeline completo.

        Args:
            query: Pergunta do usuário
            chat_history: Histórico de mensagens

        Returns:
            Dicionário com resposta completa e metadados
        """
        self.session.log_user_query(query)

        planning_result = self.planner.invoke(query)
        analysis = planning_result["analysis"]
        plan = planning_result["plan"]

        responses = self.execute_plan(query, plan)

        validation = self.critic.invoke(query, responses)

        final_response = self.response_agent.invoke(
            query,
            responses,
            plan,
            validation,
        )

        result = {
            "response": final_response["response"],
            "plan": plan,
            "analysis": analysis,
            "subagent_responses": responses,
            "validation": validation,
            "sources": final_response["sources"],
            "session_id": self.session.session_id,
        }

        return result

    def process_single_theme(
        self,
        query: str,
        theme: str,
        chat_history: list | None = None,
    ) -> dict[str, Any]:
        """
        Processa uma pergunta usando apenas um tema específico.

        Args:
            query: Pergunta do usuário
            theme: Tema selecionado
            chat_history: Histórico de mensagens

        Returns:
            Dicionário com resposta e metadados
        """
        self.session.log_user_query(query, theme)

        agent = self._get_agent_for_domain(theme)
        if not agent:
            return {
                "response": f"Tema '{theme}' não encontrado.",
                "success": False,
                "session_id": self.session.session_id,
            }

        result = agent.invoke(query, chat_history)

        self.session.log_response(result.get("response", ""), [theme])

        return {
            "response": result.get("response", ""),
            "agent": result.get("agent", ""),
            "success": result.get("success", True),
            "session_id": self.session.session_id,
        }

    def get_session_trace(self) -> list[dict[str, Any]]:
        """Retorna o trace de execução da sessão."""
        return self.session.get_execution_trace()

    def get_session_summary(self) -> dict[str, Any]:
        """Retorna resumo da sessão."""
        return self.session.get_events_summary()


def create_orchestrator(session: SessionContext | None = None) -> Orchestrator:
    """Factory function para criar Orchestrator."""
    return Orchestrator(session=session)
