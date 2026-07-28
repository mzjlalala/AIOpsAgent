"""Memory 工厂。"""

from __future__ import annotations

from app.memory.backend.base import MemoryBackend
from app.memory.backend.memory import (
    InMemoryKvStore,
    InMemoryListStore,
    InMemoryVectorMemoryStore,
)
from app.memory.conversation import ConversationMemory
from app.memory.experience import ExperienceMemory
from app.memory.long_term import LongMemory
from app.memory.manager import MemoryManager
from app.memory.session import SessionMemory
from app.providers.embedding.base import EmbeddingProvider
from app.providers.embedding.mock import MockEmbeddingProvider


def build_memory_backend() -> MemoryBackend:
    """默认三个 InMemory 能力组合。"""
    return MemoryBackend(
        lists=InMemoryListStore(),
        kv=InMemoryKvStore(),
        vectors=InMemoryVectorMemoryStore(),
    )


def build_memory_manager(
    *,
    backend: MemoryBackend | None = None,
    embedding: EmbeddingProvider | None = None,
) -> MemoryManager:
    """默认 InMemory 能力组合 + MockEmbeddingProvider。

    不自动注入 FastAPI；后续可挂入 RuntimeDependencies。
    """
    be = backend or build_memory_backend()
    emb = embedding or MockEmbeddingProvider()
    return MemoryManager(
        conversation=ConversationMemory(be.lists),
        session=SessionMemory(be.kv),
        long_term=LongMemory(be.vectors, emb),
        experience=ExperienceMemory(be.vectors, emb),
    )
