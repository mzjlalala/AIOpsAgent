"""RAG 领域模型（与 ORM 无关，供流水线与 Agent 消费）。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.types import JsonValue


class RawDocument(BaseModel):
    """Loader 输入的原始文档。"""

    source: str = Field(description="来源路径或标识。")
    content: str = Field(description="原始正文。")
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class Document(BaseModel):
    """清洗后、切分前的逻辑文档。"""

    document_id: str
    knowledge_id: str | None = None
    title: str
    source: str
    content: str
    namespace: str = "default"
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """文本分块；embedding 由 Pipeline 写入，Store 只读取。"""

    chunk_id: str
    document_id: str
    knowledge_id: str | None = None
    title: str
    content: str
    source: str
    namespace: str = "default"
    ordinal: int = 0
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    embedding: list[float] | None = None


class Citation(BaseModel):
    """独立引用模型，供 Agent 回答时标注来源。"""

    chunk_id: str
    source: str
    title: str
    document_id: str | None = None
    knowledge_id: str | None = None
    score: float | None = None


class RetrievedHit(BaseModel):
    """单条检索命中（扁平结构，对齐 Phase4 Knowledge / Agent）。"""

    rank: int
    score: float
    document_id: str
    knowledge_id: str | None = None
    chunk_id: str
    title: str
    content: str
    source: str
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class RetrieveResult(BaseModel):
    """检索结果；可 model_dump 供后续 KnowledgeTool / Agent 使用。"""

    query: str
    top_k: int
    namespace: str | None = None
    hits: list[RetrievedHit] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class MetadataFilter(BaseModel):
    """元数据过滤条件；本阶段 VectorStore 仅实现 eq。"""

    field: str
    operator: str = "eq"
    value: JsonValue
