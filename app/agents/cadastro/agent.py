"""
Agente especializado em dados cadastrais.
"""

from app.agents.base import BaseAgent
from app.config.agents import CADASTRO_AGENT_CONFIG
from app.governance.logging import SessionContext


class CadastroAgent(BaseAgent):
    """Agente especializado em dados cadastrais de clientes."""

    def __init__(self, session: SessionContext | None = None):
        super().__init__(
            config=CADASTRO_AGENT_CONFIG,
            session=session,
        )

    def get_available_tables(self) -> list[str]:
        """Retorna lista de tabelas disponíveis para este agente."""
        return self.config.tables or []


def create_cadastro_agent(session: SessionContext | None = None) -> CadastroAgent:
    """Factory function para criar CadastroAgent."""
    return CadastroAgent(session=session)
