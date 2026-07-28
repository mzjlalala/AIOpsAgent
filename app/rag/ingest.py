"""入库流水线：clean → split → embed → store。"""

from __future__ import annotations

from collections.abc import Sequence

from app.providers.embedding.base import EmbeddingProvider
from app.rag.cleaner import TextCleaner
from app.rag.models import Document, DocumentChunk
from app.rag.splitter import TextSplitter
from app.rag.store.base import VectorStore


class IngestPipeline:
    """编排入库；Embedding 在此写入 chunk.embedding 后再交给 Store。"""

    def __init__(
        self,
        *,
        cleaner: TextCleaner,
        splitter: TextSplitter,
        embedding: EmbeddingProvider,
        store: VectorStore,
    ) -> None:
        self._cleaner = cleaner
        self._splitter = splitter
        self._embedding = embedding
        self._store = store

    async def arun(
        self,
        documents: Sequence[Document],
        *,
        namespace: str | None = None,
    ) -> int:
        """入库文档，返回写入的 chunk 数量。"""
        all_chunks: list[DocumentChunk] = []
        for document in documents:
            cleaned = self._cleaner.clean(document)
            chunks = await self._splitter.split(cleaned)
            if not chunks:
                continue
            vectors = await self._embedding.embed_documents(
                [chunk.content for chunk in chunks]
            )
            for chunk, vector in zip(chunks, vectors, strict=True):
                ns = namespace or chunk.namespace
                all_chunks.append(
                    chunk.model_copy(update={"embedding": vector, "namespace": ns})
                )

        if not all_chunks:
            return 0

        # 按 namespace 分组写入
        by_ns: dict[str, list[DocumentChunk]] = {}
        for chunk in all_chunks:
            by_ns.setdefault(chunk.namespace, []).append(chunk)
        for ns, group in by_ns.items():
            await self._store.aadd(group, namespace=ns)
        return len(all_chunks)
