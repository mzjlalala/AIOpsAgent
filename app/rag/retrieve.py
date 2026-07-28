"""检索流水线：embed query → retriever → reranker → RetrieveResult。"""

from __future__ import annotations

from collections.abc import Sequence

from app.providers.embedding.base import EmbeddingProvider
from app.rag.models import Citation, RetrievedHit, RetrieveResult
from app.rag.reranker import Reranker
from app.rag.retriever import Retriever
from app.schemas.filters import MetadataFilter


class RetrievePipeline:
    """编排检索；Embedding 仅在此调用，Retriever 只吃向量。"""

    def __init__(
        self,
        *,
        embedding: EmbeddingProvider,
        retriever: Retriever,
        reranker: Reranker,
    ) -> None:
        self._embedding = embedding
        self._retriever = retriever
        self._reranker = reranker

    async def arun(
        self,
        query: str,
        *,
        top_k: int = 5,
        namespace: str = "default",
        filters: Sequence[MetadataFilter] | None = None,
    ) -> RetrieveResult:
        """执行检索并组装 Agent 对齐结果。"""
        vector = await self._embedding.embed_query(query)
        # 先多取一些供 rerank 裁剪（noop 时等同 top_k）
        raw = await self._retriever.search(
            vector,
            top_k=top_k,
            namespace=namespace,
            filters=filters,
        )
        ranked = await self._reranker.rerank(query, raw, top_k=top_k)

        hits: list[RetrievedHit] = []
        citations: list[Citation] = []
        for index, (chunk, score) in enumerate(ranked, start=1):
            hits.append(
                RetrievedHit(
                    rank=index,
                    score=score,
                    document_id=chunk.document_id,
                    knowledge_id=chunk.knowledge_id,
                    chunk_id=chunk.chunk_id,
                    title=chunk.title,
                    content=chunk.content,
                    source=chunk.source,
                    metadata=dict(chunk.metadata),
                )
            )
            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    title=chunk.title,
                    document_id=chunk.document_id,
                    knowledge_id=chunk.knowledge_id,
                    score=score,
                )
            )

        return RetrieveResult(
            query=query,
            top_k=top_k,
            namespace=namespace,
            hits=hits,
            citations=citations,
        )
