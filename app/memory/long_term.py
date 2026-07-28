"""长期记忆服务。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from app.memory.backend.base import VectorMemoryStore
from app.memory.models import LongMemoryItem, ScoredLongHit
from app.providers.embedding.base import EmbeddingProvider
from app.schemas.filters import MetadataFilter

_NS = "long"


class LongMemory:
    """长期记忆：save 时 embed，recall 时相似度检索。"""

    def __init__(
        self,
        vectors: VectorMemoryStore,
        embedding: EmbeddingProvider,
    ) -> None:
        self._vectors = vectors
        self._embedding = embedding

    async def asave(self, item: LongMemoryItem) -> LongMemoryItem:
        content = item.content
        vector = await self._embedding.embed_query(content)
        stored = item.model_copy(
            update={
                "embedding": vector,
                "created_at": item.created_at or datetime.now(UTC),
            }
        )
        await self._vectors.aupsert(_NS, [stored])
        return stored

    async def arecall(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[ScoredLongHit]:
        vector = await self._embedding.embed_query(query)
        hits = await self._vectors.asearch(
            _NS, vector=vector, top_k=top_k, filters=filters
        )
        results: list[ScoredLongHit] = []
        for record, score in hits:
            item = (
                record
                if isinstance(record, LongMemoryItem)
                else LongMemoryItem.model_validate(record.model_dump())
            )
            results.append(ScoredLongHit(item=item, score=score))
        return results
