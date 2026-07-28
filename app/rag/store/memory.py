"""内存向量存储（余弦相似度）。"""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.rag.models import DocumentChunk
from app.rag.store.base import VectorStore, VectorStoreError
from app.schemas.filters import MetadataFilter
from app.tools.types import JsonValue


class InMemoryVectorStore(VectorStore):
    """进程内向量库；按 namespace 隔离；本阶段 filter 仅支持 eq。"""

    def __init__(self) -> None:
        self._namespaces: dict[str, dict[str, DocumentChunk]] = {}

    async def aadd(
        self,
        chunks: Sequence[DocumentChunk],
        *,
        namespace: str = "default",
    ) -> None:
        bucket = self._namespaces.setdefault(namespace, {})
        for chunk in chunks:
            if chunk.embedding is None:
                raise VectorStoreError(
                    f"chunk.embedding 为空，无法入库: {chunk.chunk_id}"
                )
            # 以调用方 namespace 为准写入副本，避免 Document 与参数不一致
            stored = chunk.model_copy(update={"namespace": namespace})
            bucket[chunk.chunk_id] = stored

    async def asearch(
        self,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        namespace: str = "default",
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        if top_k <= 0:
            return []
        bucket = self._namespaces.get(namespace, {})
        scored: list[tuple[DocumentChunk, float]] = []
        for chunk in bucket.values():
            if chunk.embedding is None:
                continue
            if filters and not _match_filters(chunk, filters):
                continue
            score = _cosine_similarity(vector, chunk.embedding)
            scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    async def adelete(
        self,
        *,
        ids: Sequence[str],
        namespace: str = "default",
    ) -> None:
        bucket = self._namespaces.get(namespace)
        if not bucket:
            return
        for chunk_id in ids:
            bucket.pop(chunk_id, None)

    def get_chunk(
        self, chunk_id: str, *, namespace: str = "default"
    ) -> DocumentChunk | None:
        """按 id 读取分块（供适配器侧车使用）。"""
        return self._namespaces.get(namespace, {}).get(chunk_id)

    def list_chunks(self, *, namespace: str = "default") -> list[DocumentChunk]:
        """列出某 namespace 下全部分块。"""
        return list(self._namespaces.get(namespace, {}).values())


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise VectorStoreError(f"向量维度不一致: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _match_filters(chunk: DocumentChunk, filters: Sequence[MetadataFilter]) -> bool:
    for flt in filters:
        if flt.operator != "eq":
            raise VectorStoreError(f"暂不支持的 filter operator: {flt.operator}")
        actual = _resolve_field(chunk, flt.field)
        if actual != flt.value:
            return False
    return True


def _resolve_field(chunk: DocumentChunk, field: str) -> JsonValue:
    known = {
        "chunk_id",
        "document_id",
        "knowledge_id",
        "title",
        "source",
        "namespace",
    }
    if field in known:
        return getattr(chunk, field)
    return chunk.metadata.get(field)
