"""经验记忆服务。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from app.memory.backend.base import VectorMemoryStore
from app.memory.models import ExperienceRecord, ScoredExperienceHit
from app.providers.embedding.base import EmbeddingProvider
from app.schemas.filters import MetadataFilter

_NS = "experience"


class ExperienceMemory:
    """经验记忆：结构化案例 + 向量召回。"""

    def __init__(
        self,
        vectors: VectorMemoryStore,
        embedding: EmbeddingProvider,
    ) -> None:
        self._vectors = vectors
        self._embedding = embedding

    async def asave(self, record: ExperienceRecord) -> ExperienceRecord:
        # model_validator 已填充 content / metadata.outcome
        vector = await self._embedding.embed_query(record.content)
        stored = record.model_copy(
            update={
                "embedding": vector,
                "created_at": record.created_at or datetime.now(UTC),
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
    ) -> list[ScoredExperienceHit]:
        vector = await self._embedding.embed_query(query)
        hits = await self._vectors.asearch(
            _NS, vector=vector, top_k=top_k, filters=filters
        )
        results: list[ScoredExperienceHit] = []
        for record, score in hits:
            item = (
                record
                if isinstance(record, ExperienceRecord)
                else ExperienceRecord.model_validate(record.model_dump())
            )
            results.append(ScoredExperienceHit(item=item, score=score))
        return results
