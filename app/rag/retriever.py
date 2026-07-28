"""检索器：仅负责 vector → VectorStore，不调用 Embedding。"""

from __future__ import annotations

from collections.abc import Sequence

from app.rag.models import DocumentChunk, MetadataFilter
from app.rag.store.base import VectorStore


class Retriever:
    """薄封装：向量检索入口，禁止内嵌 Embedding。"""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    async def search(
        self,
        vector: Sequence[float],
        *,
        top_k: int = 5,
        namespace: str = "default",
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        return await self._store.asearch(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            filters=filters,
        )
