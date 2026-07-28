"""FAISS 向量库适配器（可选依赖，非 RAG 核心）。"""

from __future__ import annotations

from collections.abc import Sequence

from app.rag.models import DocumentChunk
from app.rag.store.base import VectorStore, VectorStoreError
from app.rag.store.memory import InMemoryVectorStore
from app.schemas.filters import MetadataFilter


def _require_faiss() -> object:
    try:
        import faiss  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "未安装 faiss，请使用: uv sync --group faiss " "或 pip install faiss-cpu"
        ) from exc
    return faiss


class FaissVectorStore(VectorStore):
    """基于 FAISS IndexFlatIP（需 L2 归一化向量）的可选适配器。

    元数据与 filter 仍由内存侧车索引维护；本阶段以正确性优先。
    """

    def __init__(self, *, dimensions: int | None = None) -> None:
        _require_faiss()
        self._dimensions = dimensions
        # 侧车：复用 InMemory 的 payload / filter / namespace 语义
        self._sidecar = InMemoryVectorStore()
        self._indexes: dict[str, object] = {}
        self._id_lists: dict[str, list[str]] = {}

    async def aadd(
        self,
        chunks: Sequence[DocumentChunk],
        *,
        namespace: str = "default",
    ) -> None:
        faiss = _require_faiss()
        if not chunks:
            return
        for chunk in chunks:
            if chunk.embedding is None:
                raise VectorStoreError(
                    f"chunk.embedding 为空，无法入库: {chunk.chunk_id}"
                )
            dim = len(chunk.embedding)
            if self._dimensions is None:
                self._dimensions = dim
            elif dim != self._dimensions:
                raise VectorStoreError(
                    f"向量维度不一致: expect={self._dimensions} got={dim}"
                )

        await self._sidecar.aadd(chunks, namespace=namespace)

        import numpy as np

        vectors = np.array(
            [list(chunk.embedding) for chunk in chunks],  # type: ignore[arg-type]
            dtype="float32",
        )
        # IndexFlatIP 期望归一化向量；Mock 已归一化
        index = self._indexes.get(namespace)
        if index is None:
            index = faiss.IndexFlatIP(self._dimensions)  # type: ignore[attr-defined]
            self._indexes[namespace] = index
            self._id_lists[namespace] = []
        index.add(vectors)  # type: ignore[union-attr]
        self._id_lists[namespace].extend(chunk.chunk_id for chunk in chunks)

    async def asearch(
        self,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        namespace: str = "default",
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        # filter / namespace 语义与内存实现一致；有 filter 时走 sidecar 保证正确性
        if filters:
            return await self._sidecar.asearch(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                filters=filters,
            )
        faiss = _require_faiss()
        _ = faiss
        index = self._indexes.get(namespace)
        if index is None or top_k <= 0:
            return []

        import numpy as np

        query = np.array([list(vector)], dtype="float32")
        scores, indices = index.search(query, top_k)  # type: ignore[union-attr]
        id_list = self._id_lists.get(namespace, [])
        results: list[tuple[DocumentChunk, float]] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0 or idx >= len(id_list):
                continue
            chunk = self._sidecar.get_chunk(id_list[idx], namespace=namespace)
            if chunk is None:
                continue
            results.append((chunk, float(score)))
        return results

    async def adelete(
        self,
        *,
        ids: Sequence[str],
        namespace: str = "default",
    ) -> None:
        # FAISS IndexFlatIP 不支持高效按 id 删除；清空索引后按侧车重建
        await self._sidecar.adelete(ids=ids, namespace=namespace)
        self._indexes.pop(namespace, None)
        self._id_lists.pop(namespace, None)
        remaining = self._sidecar.list_chunks(namespace=namespace)
        if remaining:
            await self.aadd(remaining, namespace=namespace)
