"""
Memória de Curto Prazo (Short-Term Memory).
Gerencia o estado da sessão usando st.session_state.
Volátil, session-based, reset ao logout.
"""

from typing import Any

import streamlit as st

from app.memory.models import ShortTermState


class ShortTermMemory:
    """
    Gerenciador de memória de curto prazo.
    Wrapper estruturado para st.session_state.
    """

    STATE_KEY = "short_term_memory"

    def __init__(self):
        """Inicializa a memória de curto prazo."""
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Garante que o estado está inicializado."""
        if self.STATE_KEY not in st.session_state:
            st.session_state[self.STATE_KEY] = ShortTermState()

    @property
    def state(self) -> ShortTermState:
        """Retorna o estado atual."""
        self._ensure_initialized()
        return st.session_state[self.STATE_KEY]

    def set_user(self, user_id: str):
        """Define o usuário da sessão."""
        self.state.user_id = user_id
        self.state.memory_status["contexto_carregado"] = True

    def set_group(self, group: dict[str, Any]):
        """Define o grupo selecionado."""
        self.state.current_group = group

    def set_last_query(self, query: str):
        """Define a última pergunta."""
        self.state.last_query = query

    def set_last_response(self, response: str):
        """Define a última resposta."""
        self.state.last_response = response
        self.state.memory_status["resposta_entregue"] = True

    def add_to_context(self, role: str, content: str, metadata: dict | None = None):
        """Adiciona mensagem ao contexto da conversa."""
        entry = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        self.state.conversation_context.append(entry)

    def get_context(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retorna o contexto recente da conversa."""
        return self.state.conversation_context[-limit:]

    def set_raio_x_status(self, status: str):
        """Atualiza status do Raio X."""
        self.state.raio_x_status = status
        if status == "validado":
            self.state.memory_status["raio_x_validado"] = True

    def set_ambiguity_status(self, status: str):
        """Atualiza status da ambiguidade."""
        self.state.ambiguity_status = status
        if status == "resolvida":
            self.state.memory_status["ambiguidade_resolvida"] = True

    def set_memory_consulted(self, consulted: bool = True):
        """Marca que a memória de longo prazo foi consultada."""
        self.state.memory_status["memoria_consultada"] = consulted

    def set_active_domains(self, domains: list[str]):
        """Define os domínios ativos."""
        self.state.active_domains = domains

    def get_memory_status(self) -> dict[str, bool]:
        """Retorna o status atual da memória."""
        return self.state.memory_status.copy()

    def get_user_id(self) -> str | None:
        """Retorna o ID do usuário."""
        return self.state.user_id

    def get_current_group(self) -> dict[str, Any] | None:
        """Retorna o grupo atual."""
        return self.state.current_group

    def reset(self):
        """Reseta a memória (logout)."""
        self.state.reset()

    def to_dict(self) -> dict[str, Any]:
        """Exporta o estado para dicionário."""
        return {
            "user_id": self.state.user_id,
            "current_group": self.state.current_group,
            "last_query": self.state.last_query,
            "last_response": self.state.last_response,
            "conversation_context": self.state.conversation_context,
            "raio_x_status": self.state.raio_x_status,
            "ambiguity_status": self.state.ambiguity_status,
            "memory_status": self.state.memory_status,
            "active_domains": self.state.active_domains,
        }


_short_term_memory: ShortTermMemory | None = None


def get_short_term_memory() -> ShortTermMemory:
    """Factory function para obter a instância de memória de curto prazo."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
