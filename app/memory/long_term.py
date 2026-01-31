"""
Memória de Longo Prazo (Long-Term Memory).
Implementa Vector Store com FAISS para persistência semântica.
Baseada em identidade (matrícula), indexável e auditável.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from app.memory.models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)

MEMORY_DIR = Path.home() / ".chat_memory"
MEMORY_FILE = MEMORY_DIR / "long_term_memory.json"


class LongTermMemory:
    """
    Gerenciador de memória de longo prazo.
    Usa FAISS para busca semântica e JSON para persistência de metadados.
    """

    def __init__(self, user_id: str | None = None):
        """
        Inicializa a memória de longo prazo.

        Args:
            user_id: Matrícula do usuário (chave de identidade)
        """
        self.user_id = user_id
        self._entries: list[MemoryEntry] = []
        self._embeddings: list[list[float]] = []
        self._faiss_index = None
        self._embedding_model = None

        self._ensure_storage_dir()
        self._load_from_disk()

    def _ensure_storage_dir(self):
        """Garante que o diretório de armazenamento existe."""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self) -> Path:
        """Retorna o arquivo de memória do usuário."""
        if self.user_id:
            return MEMORY_DIR / f"memory_{self.user_id}.json"
        return MEMORY_FILE

    def _load_from_disk(self):
        """Carrega memórias do disco."""
        file_path = self._get_user_file()
        if file_path.exists():
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    self._entries = [
                        MemoryEntry.from_dict(entry)
                        for entry in data.get("entries", [])
                    ]
                    logger.info(
                        f"Loaded {len(self._entries)} memories for user {self.user_id}"
                    )
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error loading memory: {e}")
                self._entries = []

    def _save_to_disk(self):
        """Salva memórias no disco."""
        file_path = self._get_user_file()
        try:
            data = {
                "user_id": self.user_id,
                "last_updated": datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in self._entries],
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self._entries)} memories for user {self.user_id}")
        except OSError as e:
            logger.error(f"Error saving memory: {e}")

    def _get_embedding(self, text: str) -> list[float]:
        """
        Gera embedding para o texto.
        Usa modelo de embeddings do OpenAI ou fallback simples.
        """
        try:
            from langchain_openai import OpenAIEmbeddings

            if self._embedding_model is None:
                self._embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

            return self._embedding_model.embed_query(text)
        except Exception as e:
            logger.warning(f"Could not generate embedding: {e}")
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> list[float]:
        """Fallback: embedding simples baseado em hash."""
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes[:128]]

    def _build_faiss_index(self):
        """Constrói o índice FAISS para busca semântica."""
        if not self._entries:
            return

        try:
            import faiss
            import numpy as np

            if not self._embeddings:
                self._embeddings = [
                    self._get_embedding(entry.conteudo) for entry in self._entries
                ]

            if self._embeddings:
                dimension = len(self._embeddings[0])
                self._faiss_index = faiss.IndexFlatL2(dimension)
                embeddings_array = np.array(self._embeddings).astype("float32")
                self._faiss_index.add(embeddings_array)
                logger.info(f"Built FAISS index with {len(self._entries)} entries")
        except ImportError:
            logger.warning("FAISS not available, using simple search")
            self._faiss_index = None

    def add(self, entry: MemoryEntry) -> str:
        """
        Adiciona uma entrada à memória de longo prazo.

        Args:
            entry: Entrada de memória

        Returns:
            ID do embedding
        """
        entry.user_id = self.user_id or entry.user_id
        entry.embedding_id = f"mem_{len(self._entries)}_{datetime.now().timestamp()}"

        self._entries.append(entry)

        embedding = self._get_embedding(entry.conteudo)
        self._embeddings.append(embedding)

        self._save_to_disk()
        self._build_faiss_index()

        logger.info(
            f"Added memory: type={entry.tipo.value}, domain={entry.dominio}"
        )

        return entry.embedding_id

    def search(
        self,
        query: str,
        limit: int = 5,
        tipo: MemoryType | None = None,
        dominio: str | None = None,
    ) -> list[MemoryEntry]:
        """
        Busca memórias semanticamente similares.

        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            tipo: Filtrar por tipo de memória
            dominio: Filtrar por domínio

        Returns:
            Lista de entradas de memória relevantes
        """
        if not self._entries:
            return []

        filtered_entries = self._entries
        if tipo:
            filtered_entries = [e for e in filtered_entries if e.tipo == tipo]
        if dominio:
            filtered_entries = [e for e in filtered_entries if e.dominio == dominio]

        if not filtered_entries:
            return []

        try:
            if self._faiss_index is not None:
                return self._faiss_search(query, filtered_entries, limit)
        except Exception as e:
            logger.warning(f"FAISS search failed: {e}")

        return self._simple_search(query, filtered_entries, limit)

    def _faiss_search(
        self, query: str, entries: list[MemoryEntry], limit: int
    ) -> list[MemoryEntry]:
        """Busca usando FAISS."""
        import numpy as np

        query_embedding = np.array([self._get_embedding(query)]).astype("float32")

        entry_indices = [self._entries.index(e) for e in entries]
        entry_embeddings = np.array(
            [self._embeddings[i] for i in entry_indices]
        ).astype("float32")

        import faiss

        temp_index = faiss.IndexFlatL2(entry_embeddings.shape[1])
        temp_index.add(entry_embeddings)

        k = min(limit, len(entries))
        _, indices = temp_index.search(query_embedding, k)

        return [entries[i] for i in indices[0] if i < len(entries)]

    def _simple_search(
        self, query: str, entries: list[MemoryEntry], limit: int
    ) -> list[MemoryEntry]:
        """Busca simples baseada em palavras-chave."""
        query_words = set(query.lower().split())

        scored_entries = []
        for entry in entries:
            content_words = set(entry.conteudo.lower().split())
            score = len(query_words & content_words)
            if score > 0:
                scored_entries.append((score, entry))

        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def get_by_type(self, tipo: MemoryType) -> list[MemoryEntry]:
        """Retorna todas as memórias de um tipo específico."""
        return [e for e in self._entries if e.tipo == tipo]

    def get_ambiguity_resolutions(self, dominio: str | None = None) -> list[MemoryEntry]:
        """Retorna resoluções de ambiguidade."""
        entries = self.get_by_type(MemoryType.RESOLUCAO_AMBIGUIDADE)
        if dominio:
            entries = [e for e in entries if e.dominio == dominio]
        return entries

    def get_user_preferences(self) -> list[MemoryEntry]:
        """Retorna preferências do usuário."""
        return self.get_by_type(MemoryType.PREFERENCIA_USUARIO)

    def get_decisions(self, dominio: str | None = None) -> list[MemoryEntry]:
        """Retorna decisões tomadas."""
        entries = self.get_by_type(MemoryType.DECISAO_TOMADA)
        if dominio:
            entries = [e for e in entries if e.dominio == dominio]
        return entries

    def count(self) -> int:
        """Retorna o número total de memórias."""
        return len(self._entries)

    def clear(self):
        """Limpa todas as memórias (use com cuidado)."""
        self._entries = []
        self._embeddings = []
        self._faiss_index = None
        self._save_to_disk()
        logger.warning(f"Cleared all memories for user {self.user_id}")


_long_term_memories: dict[str, LongTermMemory] = {}


def get_long_term_memory(user_id: str) -> LongTermMemory:
    """
    Factory function para obter a instância de memória de longo prazo.

    Args:
        user_id: Matrícula do usuário

    Returns:
        Instância de LongTermMemory para o usuário
    """
    if user_id not in _long_term_memories:
        _long_term_memories[user_id] = LongTermMemory(user_id)
    return _long_term_memories[user_id]
