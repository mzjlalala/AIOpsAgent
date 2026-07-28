"""重排序接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.rag.models import DocumentChunk


class Reranker(ABC):
    """重排序抽象；生产可接 CrossEncoder 等。"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        items: Sequence[tuple[DocumentChunk, float]],
        *,
        top_k: int | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """对检索结果重排；默认实现可透传。"""


class NoopReranker(Reranker):
    """透传重排器。"""

    async def rerank(
        self,
        query: str,
        items: Sequence[tuple[DocumentChunk, float]],
        *,
        top_k: int | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        _ = query
        ranked = list(items)
        if top_k is not None:
            return ranked[:top_k]
        return ranked
