"""向量存储抽象；不负责 Embedding。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.rag.models import DocumentChunk
from app.schemas.filters import MetadataFilter


class VectorStoreError(Exception):
    """向量存储相关错误。"""


class VectorStore(ABC):
    """向量库抽象：只接收已带 embedding 的 DocumentChunk。"""

    @abstractmethod
    async def aadd(
        self,
        chunks: Sequence[DocumentChunk],
        *,
        namespace: str = "default",
    ) -> None:
        """写入分块；要求每个 chunk.embedding 非空。"""

    @abstractmethod
    async def asearch(
        self,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        namespace: str = "default",
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """按向量相似度检索，返回 (chunk, score) 列表。"""

    @abstractmethod
    async def adelete(
        self,
        *,
        ids: Sequence[str],
        namespace: str = "default",
    ) -> None:
        """按 chunk_id 删除。"""
