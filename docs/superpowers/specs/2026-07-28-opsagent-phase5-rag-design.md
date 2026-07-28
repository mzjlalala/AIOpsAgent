# OpsAgent 第五阶段：Embedding Provider + RAG（分层接口）

Date: 2026-07-28

## 目标

落地 EmbeddingProvider 抽象与 sha256 Mock，以及分层 RAG 流水线（Ingest / Retrieve 分离），检索输出对齐后续 Agent / Phase4 Knowledge 形态。

## 关键决策

- 分层接口；`IngestPipeline` + `RetrievePipeline`
- `DocumentChunk.embedding` 由 Pipeline 写入；`VectorStore.aadd(chunks)` 不生成向量
- `RetrieveResult.hits: list[RetrievedHit]` + 独立 `Citation`（含 `score`）
- Retriever **仅** `vector → store`，不调用 Embedding
- `DocumentChunk.namespace`；`MetadataFilter`（本阶段 `eq`）
- `TextSplitter` ABC + `SimpleTextSplitter`；`RawDocument` + Loader
- FAISS 位于 `app/rag/adapters/vectorstore/faiss.py`（optional group `faiss`）
- 不接 Tool / API / MySQL / 真实 Embedding / Milvus

## 目录

见仓库 `app/providers/embedding/` 与 `app/rag/`。

## 数据流

RawDocument → Loader → Document → Clean → Split → Embed → Chunk.embedding → Store

Query → Embed → Retriever(store) → Reranker → RetrieveResult

## 验收

- Mock Embedding 确定性；Store 缺 embedding 报错；namespace / filter 生效
- Ingest → Retrieve 命中；citations 含 score；FAISS importorskip
- pytest / ruff / black / isort 通过
