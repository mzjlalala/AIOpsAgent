"""RAG 入库 / 检索流水线与 Store 单测。"""

from __future__ import annotations

import pytest

from app.providers.embedding import MockEmbeddingProvider
from app.rag import (
    Document,
    DocumentChunk,
    MetadataFilter,
    RawDocument,
    TextDocumentLoader,
    VectorStoreError,
    build_rag_bundle,
)
from app.rag.retriever import Retriever
from app.rag.splitter import SimpleTextSplitter
from app.rag.store.memory import InMemoryVectorStore


@pytest.mark.asyncio
async def test_loader_and_ingest_retrieve_roundtrip() -> None:
    loader = TextDocumentLoader()
    raw = RawDocument(
        source="runbook/cpu-high.md",
        content="# CPU 打满排查\n\n检查进程 CPU、最近发布与慢查询。",
        metadata={"category": "cpu", "namespace": "ops"},
    )
    doc = await loader.load(raw)
    assert doc.title == "CPU 打满排查"
    assert doc.namespace == "ops"

    bundle = build_rag_bundle(
        splitter=SimpleTextSplitter(chunk_size=80, chunk_overlap=10)
    )
    count = await bundle.ingest.arun([doc])
    assert count >= 1

    result = await bundle.retrieve.arun(
        "CPU 打满排查",
        top_k=3,
        namespace="ops",
    )
    assert result.query == "CPU 打满排查"
    assert result.namespace == "ops"
    assert len(result.hits) >= 1
    hit = result.hits[0]
    assert hit.chunk_id
    assert hit.document_id == doc.document_id
    assert hit.content
    assert result.citations[0].score is not None
    assert result.citations[0].chunk_id == hit.chunk_id

    dumped = result.model_dump()
    assert "hits" in dumped and "citations" in dumped
    assert dumped["hits"][0]["rank"] == 1


@pytest.mark.asyncio
async def test_vector_store_requires_embedding_and_namespace_filter() -> None:
    store = InMemoryVectorStore()
    bare = DocumentChunk(
        chunk_id="chk-1",
        document_id="doc-1",
        title="t",
        content="hello",
        source="s",
        namespace="ns-a",
        metadata={"env": "prod"},
        embedding=None,
    )
    with pytest.raises(VectorStoreError):
        await store.aadd([bare], namespace="ns-a")

    emb = MockEmbeddingProvider(dimensions=32)
    vector = await emb.embed_query("hello")
    chunk = bare.model_copy(update={"embedding": vector})
    await store.aadd([chunk], namespace="ns-a")

    # 不同 namespace 不可见
    miss = await store.asearch(vector=vector, top_k=5, namespace="ns-b")
    assert miss == []

    hit = await store.asearch(
        vector=vector,
        top_k=5,
        namespace="ns-a",
        filters=[MetadataFilter(field="env", operator="eq", value="prod")],
    )
    assert len(hit) == 1
    assert hit[0][0].chunk_id == "chk-1"

    filtered_out = await store.asearch(
        vector=vector,
        top_k=5,
        namespace="ns-a",
        filters=[MetadataFilter(field="env", operator="eq", value="dev")],
    )
    assert filtered_out == []


@pytest.mark.asyncio
async def test_retriever_does_not_need_embedding_provider() -> None:
    """Retriever 只接受向量，不依赖 EmbeddingProvider。"""
    store = InMemoryVectorStore()
    emb = MockEmbeddingProvider(dimensions=32)
    vector = await emb.embed_query("redis OOM")
    chunk = DocumentChunk(
        chunk_id="chk-r1",
        document_id="doc-r1",
        title="redis",
        content="redis OOM 处理",
        source="runbook/redis.md",
        namespace="default",
        embedding=vector,
    )
    await store.aadd([chunk])
    retriever = Retriever(store)
    results = await retriever.search(vector, top_k=1)
    assert results[0][0].chunk_id == "chk-r1"


@pytest.mark.asyncio
async def test_faiss_adapter_optional() -> None:
    faiss = pytest.importorskip("faiss")
    _ = faiss
    from app.rag.adapters.vectorstore.faiss import FaissVectorStore

    store = FaissVectorStore()
    emb = MockEmbeddingProvider(dimensions=32)
    vector = await emb.embed_query("faiss demo")
    chunk = DocumentChunk(
        chunk_id="chk-f1",
        document_id="doc-f1",
        title="faiss",
        content="faiss demo",
        source="s",
        embedding=vector,
    )
    await store.aadd([chunk])
    hits = await store.asearch(vector=vector, top_k=1)
    assert hits[0][0].chunk_id == "chk-f1"


@pytest.mark.asyncio
async def test_document_model_for_ingest() -> None:
    bundle = build_rag_bundle()
    doc = Document(
        document_id="doc-manual",
        knowledge_id="kn-manual",
        title="发布回滚",
        source="runbook/rollback.md",
        content="核对变更窗口，执行上一版本回滚并观察错误率。",
        namespace="default",
        metadata={"category": "deploy"},
    )
    n = await bundle.ingest.arun([doc])
    assert n >= 1
    result = await bundle.retrieve.arun("回滚", top_k=2)
    assert isinstance(result.hits[0].rank, int)
