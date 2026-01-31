"""
Módulo de memória corporativa.
Implementa memória de curto prazo (sessão) e longo prazo (Vector Store).
"""

from app.memory.long_term import LongTermMemory, get_long_term_memory
from app.memory.memory_agent import MemoryAgent, create_memory_agent
from app.memory.models import MemoryEntry, MemoryType
from app.memory.short_term import ShortTermMemory, get_short_term_memory

__all__ = [
    "ShortTermMemory",
    "get_short_term_memory",
    "LongTermMemory",
    "get_long_term_memory",
    "MemoryAgent",
    "create_memory_agent",
    "MemoryEntry",
    "MemoryType",
]
