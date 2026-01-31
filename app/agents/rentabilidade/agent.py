"""
Agente especializado em dados de rentabilidade.
"""

from app.agents.base import BaseAgent
from app.config.agents import RENTABILIDADE_AGENT_CONFIG
from app.governance.logging import SessionContext


class RentabilidadeAgent(BaseAgent):
    """Agente especializado em análise de rentabilidade."""

    def __init__(self, session: SessionContext | None = None):
        super().__init__(
            config=RENTABILIDADE_AGENT_CONFIG,
            session=session,
        )

    def get_available_tables(self) -> list[str]:
        """Retorna lista de tabelas disponíveis para este agente."""
        return self.config.tables or []


def create_rentabilidade_agent(
    session: SessionContext | None = None,
) -> RentabilidadeAgent:
    """Factory function para criar RentabilidadeAgent."""
    return RentabilidadeAgent(session=session)
