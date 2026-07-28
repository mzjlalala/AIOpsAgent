"""RAG 工厂：组装 Ingest / Retrieve 流水线。"""

from __future__ import annotations

from typing import NamedTuple

from app.providers.embedding.base import EmbeddingProvider
from app.providers.embedding.mock import MockEmbeddingProvider
from app.rag.cleaner import TextCleaner
from app.rag.ingest import IngestPipeline
from app.rag.reranker import NoopReranker, Reranker
from app.rag.retrieve import RetrievePipeline
from app.rag.retriever import Retriever
from app.rag.splitter import SimpleTextSplitter, TextSplitter
from app.rag.store.base import VectorStore
from app.rag.store.memory import InMemoryVectorStore


class RagBundle(NamedTuple):
    """共享 embedding/store 的入库与检索管线组合。"""

    ingest: IngestPipeline
    retrieve: RetrievePipeline
    embedding: EmbeddingProvider
    store: VectorStore


def build_vector_store(*, use_faiss: bool = False) -> VectorStore:
    """构建向量库；use_faiss 时走可选 adapter。"""
    if use_faiss:
        from app.rag.adapters.vectorstore.faiss import FaissVectorStore

        return FaissVectorStore()
    return InMemoryVectorStore()


def build_ingest_pipeline(
    *,
    embedding: EmbeddingProvider | None = None,
    store: VectorStore | None = None,
    splitter: TextSplitter | None = None,
    cleaner: TextCleaner | None = None,
    use_faiss: bool = False,
) -> IngestPipeline:
    """默认 MockEmbedding + InMemory。"""
    emb = embedding or MockEmbeddingProvider()
    vs = store or build_vector_store(use_faiss=use_faiss)
    return IngestPipeline(
        cleaner=cleaner or TextCleaner(),
        splitter=splitter or SimpleTextSplitter(),
        embedding=emb,
        store=vs,
    )


def build_retrieve_pipeline(
    *,
    embedding: EmbeddingProvider | None = None,
    store: VectorStore | None = None,
    reranker: Reranker | None = None,
    use_faiss: bool = False,
) -> RetrievePipeline:
    """默认 MockEmbedding + InMemory + NoopReranker。"""
    emb = embedding or MockEmbeddingProvider()
    vs = store or build_vector_store(use_faiss=use_faiss)
    return RetrievePipeline(
        embedding=emb,
        retriever=Retriever(vs),
        reranker=reranker or NoopReranker(),
    )


def build_rag_bundle(
    *,
    embedding: EmbeddingProvider | None = None,
    store: VectorStore | None = None,
    splitter: TextSplitter | None = None,
    cleaner: TextCleaner | None = None,
    reranker: Reranker | None = None,
    use_faiss: bool = False,
) -> RagBundle:
    """构建共享依赖的入库 + 检索组合。"""
    emb = embedding or MockEmbeddingProvider()
    vs = store or build_vector_store(use_faiss=use_faiss)
    ingest = IngestPipeline(
        cleaner=cleaner or TextCleaner(),
        splitter=splitter or SimpleTextSplitter(),
        embedding=emb,
        store=vs,
    )
    retrieve = RetrievePipeline(
        embedding=emb,
        retriever=Retriever(vs),
        reranker=reranker or NoopReranker(),
    )
    return RagBundle(ingest=ingest, retrieve=retrieve, embedding=emb, store=vs)
