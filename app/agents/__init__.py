"""Modulo de agentes tematicos."""

from app.agents.base import BaseAgent
from app.agents.cadastro.agent import CadastroAgent, create_cadastro_agent
from app.agents.financeiro.agent import FinanceiroAgent, create_financeiro_agent
from app.agents.rentabilidade.agent import (
    RentabilidadeAgent,
    create_rentabilidade_agent,
)
from app.agents.sql.agent import SQLAgent, create_sql_agent

__all__ = [
    "BaseAgent",
    "CadastroAgent",
    "FinanceiroAgent",
    "RentabilidadeAgent",
    "SQLAgent",
    "create_cadastro_agent",
    "create_financeiro_agent",
    "create_rentabilidade_agent",
    "create_sql_agent",
]
