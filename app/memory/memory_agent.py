"""
MemoryAgent - Agente dedicado para gerenciamento de memória.
Responsável por decidir o que entra na memória longa,
quando consultar, resolver conflitos e versionar entradas.
"""

import logging
from datetime import datetime
from typing import Any

from app.memory.long_term import get_long_term_memory
from app.memory.models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Agente de memória corporativo.
    Controla escrita e leitura da memória de longo prazo.
    Apenas o orquestrador deve chamar este agente.
    """

    def __init__(self, user_id: str):
        """
        Inicializa o MemoryAgent.

        Args:
            user_id: Matrícula do usuário
        """
        self.user_id = user_id
        self.long_term = get_long_term_memory(user_id)
        self._write_log: list[dict[str, Any]] = []
        self._read_log: list[dict[str, Any]] = []

    def should_memorize(
        self,
        content: str,
        tipo: MemoryType,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Decide se o conteúdo deve ser memorizado.

        Regras:
        - NÃO memorizar conversa raw
        - NÃO memorizar SQL executado
        - NÃO memorizar dados sensíveis
        - NÃO memorizar respostas finais completas
        - NÃO memorizar chain-of-thought

        Args:
            content: Conteúdo a ser avaliado
            tipo: Tipo de memória proposto
            context: Contexto adicional

        Returns:
            True se deve memorizar, False caso contrário
        """
        if not content or len(content.strip()) < 10:
            return False

        content_lower = content.lower()

        sensitive_patterns = [
            "senha", "password", "token", "secret", "api_key",
            "cpf", "rg", "cartao", "credit_card",
        ]
        for pattern in sensitive_patterns:
            if pattern in content_lower:
                logger.info(f"Blocked sensitive content: {pattern}")
                return False

        sql_patterns = ["select ", "insert ", "update ", "delete ", "from "]
        sql_count = sum(1 for p in sql_patterns if p in content_lower)
        if sql_count >= 2:
            logger.info("Blocked SQL content")
            return False

        if len(content) > 2000:
            logger.info("Blocked overly long content")
            return False

        if tipo == MemoryType.RESOLUCAO_AMBIGUIDADE:
            return True
        if tipo == MemoryType.PREFERENCIA_USUARIO:
            return True
        if tipo == MemoryType.DECISAO_TOMADA:
            return True
        if tipo == MemoryType.RESUMO_INTERACAO:
            return len(content) < 500

        return False

    def memorize(
        self,
        content: str,
        tipo: MemoryType,
        dominio: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Memoriza conteúdo se passar nas regras.

        Args:
            content: Conteúdo a memorizar
            tipo: Tipo de memória
            dominio: Domínio relacionado
            metadata: Metadados adicionais

        Returns:
            ID do embedding se memorizado, None caso contrário
        """
        if not self.should_memorize(content, tipo):
            logger.info("Content not memorized: failed rules check")
            return None

        existing = self._check_duplicate(content, tipo, dominio)
        if existing:
            logger.info(f"Content already exists: {existing.embedding_id}")
            return existing.embedding_id

        entry = MemoryEntry(
            user_id=self.user_id,
            tipo=tipo,
            conteudo=content,
            dominio=dominio,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        embedding_id = self.long_term.add(entry)

        self._log_write(entry, "created")

        return embedding_id

    def _check_duplicate(
        self,
        content: str,
        tipo: MemoryType,
        dominio: str | None,
    ) -> MemoryEntry | None:
        """Verifica se já existe memória similar."""
        existing = self.long_term.search(content, limit=3, tipo=tipo, dominio=dominio)

        for entry in existing:
            similarity = self._calculate_similarity(content, entry.conteudo)
            if similarity > 0.9:
                return entry

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simples entre dois textos."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def recall(
        self,
        query: str,
        limit: int = 5,
        tipo: MemoryType | None = None,
        dominio: str | None = None,
    ) -> list[MemoryEntry]:
        """
        Recupera memórias relevantes.

        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            tipo: Filtrar por tipo
            dominio: Filtrar por domínio

        Returns:
            Lista de memórias relevantes
        """
        results = self.long_term.search(query, limit, tipo, dominio)

        self._log_read(query, len(results))

        return results

    def recall_ambiguity_resolutions(
        self,
        query: str,
        dominio: str | None = None,
    ) -> list[MemoryEntry]:
        """
        Recupera resoluções de ambiguidade relevantes.

        Args:
            query: Texto de busca
            dominio: Filtrar por domínio

        Returns:
            Lista de resoluções de ambiguidade
        """
        return self.recall(
            query,
            limit=10,
            tipo=MemoryType.RESOLUCAO_AMBIGUIDADE,
            dominio=dominio,
        )

    def recall_user_preferences(self) -> list[MemoryEntry]:
        """Recupera preferências do usuário."""
        return self.long_term.get_user_preferences()

    def recall_decisions(self, dominio: str | None = None) -> list[MemoryEntry]:
        """Recupera decisões tomadas."""
        return self.long_term.get_decisions(dominio)

    def memorize_ambiguity_resolution(
        self,
        term: str,
        resolution: str,
        dominio: str | None = None,
    ) -> str | None:
        """
        Memoriza uma resolução de ambiguidade.

        Args:
            term: Termo ambíguo
            resolution: Resolução do termo
            dominio: Domínio relacionado

        Returns:
            ID do embedding se memorizado
        """
        content = f"{term} refere-se a {resolution}"
        return self.memorize(
            content,
            MemoryType.RESOLUCAO_AMBIGUIDADE,
            dominio,
            metadata={"term": term, "resolution": resolution},
        )

    def memorize_user_preference(
        self,
        preference: str,
        category: str | None = None,
    ) -> str | None:
        """
        Memoriza uma preferência do usuário.

        Args:
            preference: Descrição da preferência
            category: Categoria da preferência

        Returns:
            ID do embedding se memorizado
        """
        return self.memorize(
            preference,
            MemoryType.PREFERENCIA_USUARIO,
            metadata={"category": category} if category else None,
        )

    def memorize_decision(
        self,
        decision: str,
        dominio: str | None = None,
        context: str | None = None,
    ) -> str | None:
        """
        Memoriza uma decisão tomada.

        Args:
            decision: Descrição da decisão
            dominio: Domínio relacionado
            context: Contexto da decisão

        Returns:
            ID do embedding se memorizado
        """
        return self.memorize(
            decision,
            MemoryType.DECISAO_TOMADA,
            dominio,
            metadata={"context": context} if context else None,
        )

    def _log_write(self, entry: MemoryEntry, action: str):
        """Loga uma operação de escrita."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "tipo": entry.tipo.value,
            "dominio": entry.dominio,
            "content_preview": entry.conteudo[:100],
            "embedding_id": entry.embedding_id,
        }
        self._write_log.append(log_entry)
        logger.info(f"Memory write: {action} - {entry.tipo.value}")

    def _log_read(self, query: str, results_count: int):
        """Loga uma operação de leitura."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_preview": query[:100],
            "results_count": results_count,
        }
        self._read_log.append(log_entry)
        logger.info(f"Memory read: {results_count} results for query")

    def get_write_log(self) -> list[dict[str, Any]]:
        """Retorna o log de escritas."""
        return self._write_log.copy()

    def get_read_log(self) -> list[dict[str, Any]]:
        """Retorna o log de leituras."""
        return self._read_log.copy()

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas da memória."""
        return {
            "user_id": self.user_id,
            "total_memories": self.long_term.count(),
            "write_operations": len(self._write_log),
            "read_operations": len(self._read_log),
            "ambiguity_resolutions": len(
                self.long_term.get_ambiguity_resolutions()
            ),
            "user_preferences": len(self.long_term.get_user_preferences()),
            "decisions": len(self.long_term.get_decisions()),
        }


_memory_agents: dict[str, MemoryAgent] = {}


def create_memory_agent(user_id: str) -> MemoryAgent:
    """
    Factory function para criar o MemoryAgent.

    Args:
        user_id: Matrícula do usuário

    Returns:
        Instância de MemoryAgent para o usuário
    """
    if user_id not in _memory_agents:
        _memory_agents[user_id] = MemoryAgent(user_id)
    return _memory_agents[user_id]
