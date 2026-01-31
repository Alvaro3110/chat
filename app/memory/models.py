"""
Modelos de dados para o sistema de memória.
Define estruturas para entradas de memória e tipos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    """Tipos de memória suportados."""

    PREFERENCIA_USUARIO = "preferencia_usuario"
    DECISAO_TOMADA = "decisao_tomada"
    RESOLUCAO_AMBIGUIDADE = "resolucao_ambiguidade"
    RESUMO_INTERACAO = "resumo_interacao"


@dataclass
class MemoryEntry:
    """
    Entrada de memória de longo prazo.

    Attributes:
        user_id: Matrícula do usuário
        tipo: Tipo da memória (MemoryType)
        conteudo: Conteúdo semântico da memória
        dominio: Domínio relacionado (cadastro, financeiro, rentabilidade)
        timestamp: Data/hora da criação
        metadata: Metadados adicionais
        version: Versão da entrada (para versionamento)
        embedding_id: ID do embedding no Vector Store
    """

    user_id: str
    tipo: MemoryType
    conteudo: str
    dominio: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    embedding_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "user_id": self.user_id,
            "tipo": self.tipo.value,
            "conteudo": self.conteudo,
            "dominio": self.dominio,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "version": self.version,
            "embedding_id": self.embedding_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """Cria instância a partir de dicionário."""
        return cls(
            user_id=data["user_id"],
            tipo=MemoryType(data["tipo"]),
            conteudo=data["conteudo"],
            dominio=data.get("dominio"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            embedding_id=data.get("embedding_id"),
        )


@dataclass
class ShortTermState:
    """
    Estado de memória de curto prazo (sessão).

    Attributes:
        user_id: Matrícula do usuário
        current_group: Grupo atualmente selecionado
        last_query: Última pergunta do usuário
        last_response: Última resposta do sistema
        conversation_context: Contexto da conversa atual
        raio_x_status: Status do Raio X do Cliente
        ambiguity_status: Status da retirada de ambiguidade
        memory_status: Status da memória (carregada, consultada, etc.)
        active_domains: Domínios ativos na sessão
    """

    user_id: str | None = None
    current_group: dict[str, Any] | None = None
    last_query: str | None = None
    last_response: str | None = None
    conversation_context: list[dict[str, Any]] = field(default_factory=list)
    raio_x_status: str = "pendente"
    ambiguity_status: str = "pendente"
    memory_status: dict[str, bool] = field(default_factory=lambda: {
        "contexto_carregado": False,
        "memoria_consultada": False,
        "raio_x_validado": False,
        "ambiguidade_resolvida": False,
        "resposta_entregue": False,
    })
    active_domains: list[str] = field(default_factory=list)

    def reset(self):
        """Reseta o estado para logout."""
        self.user_id = None
        self.current_group = None
        self.last_query = None
        self.last_response = None
        self.conversation_context = []
        self.raio_x_status = "pendente"
        self.ambiguity_status = "pendente"
        self.memory_status = {
            "contexto_carregado": False,
            "memoria_consultada": False,
            "raio_x_validado": False,
            "ambiguidade_resolvida": False,
            "resposta_entregue": False,
        }
        self.active_domains = []

    def update_status(self, key: str, value: bool):
        """Atualiza um status específico."""
        if key in self.memory_status:
            self.memory_status[key] = value
