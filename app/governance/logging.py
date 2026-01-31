"""
Módulo de governança e observabilidade.
Implementa logging estruturado, geração de session_id e integração com LangSmith.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any

LANGSMITH_ENABLED = os.getenv("LANGSMITH_API_KEY") is not None


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configura logging estruturado para a aplicação.

    Args:
        level: Nível de logging (padrão: INFO)

    Returns:
        Logger configurado
    """
    logger = logging.getLogger("multiagent_platform")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(session_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class SessionContext:
    """Contexto de sessão para rastreamento."""

    def __init__(self, user_id: str | None = None):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.now()
        self.events: list[dict[str, Any]] = []
        self.logger = setup_logging()

    def log_event(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Registra um evento na sessão.

        Args:
            event_type: Tipo do evento (ex: 'user_query', 'agent_response')
            message: Mensagem do evento
            metadata: Metadados adicionais
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }
        self.events.append(event)
        self.logger.info(
            message,
            extra={"session_id": self.session_id},
        )

    def log_user_query(self, query: str, theme: str | None = None) -> None:
        """Registra uma pergunta do usuário."""
        self.log_event(
            "user_query",
            f"Pergunta do usuário: {query[:100]}...",
            {"query": query, "theme": theme},
        )

    def log_plan(self, plan: list[str]) -> None:
        """Registra o plano de execução."""
        self.log_event(
            "execution_plan",
            f"Plano criado com {len(plan)} etapas",
            {"plan": plan},
        )

    def log_agent_call(
        self,
        agent_name: str,
        task: str,
        result: str | None = None,
    ) -> None:
        """Registra chamada a um subagente."""
        self.log_event(
            "agent_call",
            f"Agente {agent_name} executando tarefa",
            {"agent": agent_name, "task": task, "result": result},
        )

    def log_tool_execution(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: str | None = None,
    ) -> None:
        """Registra execução de uma ferramenta."""
        self.log_event(
            "tool_execution",
            f"Ferramenta {tool_name} executada",
            {"tool": tool_name, "args": args, "result": result},
        )

    def log_response(self, response: str, sources: list[str] | None = None) -> None:
        """Registra a resposta final."""
        self.log_event(
            "final_response",
            f"Resposta gerada ({len(response)} caracteres)",
            {"response": response[:500], "sources": sources or []},
        )

    def log_error(self, error: str, context: dict[str, Any] | None = None) -> None:
        """Registra um erro."""
        self.log_event(
            "error",
            f"Erro: {error}",
            {"error": error, "context": context or {}},
        )

    def get_trace_metadata(self) -> dict[str, Any]:
        """
        Retorna metadados para integração com LangSmith.

        Returns:
            Dicionário com metadados da sessão
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }

    def get_events_summary(self) -> dict[str, Any]:
        """
        Retorna resumo dos eventos da sessão.

        Returns:
            Dicionário com resumo
        """
        event_counts = {}
        for event in self.events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "event_counts": event_counts,
            "duration_seconds": (datetime.now() - self.created_at).total_seconds(),
        }

    def get_execution_trace(self) -> list[dict[str, Any]]:
        """
        Retorna trace completo de execução para auditoria.

        Returns:
            Lista de eventos ordenados
        """
        return sorted(self.events, key=lambda x: x["timestamp"])


class GovernanceManager:
    """Gerenciador de governança e observabilidade."""

    def __init__(self):
        self.sessions: dict[str, SessionContext] = {}
        self.logger = setup_logging()

    def create_session(self, user_id: str | None = None) -> SessionContext:
        """
        Cria uma nova sessão.

        Args:
            user_id: ID do usuário (opcional)

        Returns:
            Contexto da sessão criada
        """
        session = SessionContext(user_id)
        self.sessions[session.session_id] = session
        self.logger.info(
            f"Sessão criada: {session.session_id}",
            extra={"session_id": session.session_id},
        )
        return session

    def get_session(self, session_id: str) -> SessionContext | None:
        """
        Recupera uma sessão existente.

        Args:
            session_id: ID da sessão

        Returns:
            Contexto da sessão ou None
        """
        return self.sessions.get(session_id)

    def end_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Finaliza uma sessão e retorna resumo.

        Args:
            session_id: ID da sessão

        Returns:
            Resumo da sessão ou None
        """
        session = self.sessions.pop(session_id, None)
        if session:
            summary = session.get_events_summary()
            self.logger.info(
                f"Sessão finalizada: {session_id}",
                extra={"session_id": session_id},
            )
            return summary
        return None


_governance_manager: GovernanceManager | None = None


def get_governance_manager() -> GovernanceManager:
    """Retorna instância singleton do gerenciador de governança."""
    global _governance_manager
    if _governance_manager is None:
        _governance_manager = GovernanceManager()
    return _governance_manager
