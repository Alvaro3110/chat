"""
Agente especializado em dados financeiros.
"""

from app.agents.base import BaseAgent
from app.config.agents import FINANCEIRO_AGENT_CONFIG
from app.governance.logging import SessionContext


class FinanceiroAgent(BaseAgent):
    """Agente especializado em dados financeiros."""

    def __init__(self, session: SessionContext | None = None):
        super().__init__(
            config=FINANCEIRO_AGENT_CONFIG,
            session=session,
        )

    def get_available_tables(self) -> list[str]:
        """Retorna lista de tabelas disponíveis para este agente."""
        return self.config.tables or []


def create_financeiro_agent(session: SessionContext | None = None) -> FinanceiroAgent:
    """Factory function para criar FinanceiroAgent."""
    return FinanceiroAgent(session=session)
