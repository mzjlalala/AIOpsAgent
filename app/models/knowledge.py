"""文档、知识条目与分块 ORM 模型。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Document(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """知识库原始文档。"""

    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, default="1")
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    knowledge_items: Mapped[list[Knowledge]] = relationship(back_populates="document")


class Knowledge(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """由文档衍生的逻辑知识条目。"""

    __tablename__ = "knowledge"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    document: Mapped[Document] = relationship(back_populates="knowledge_items")
    chunks: Mapped[list[Chunk]] = relationship(back_populates="knowledge")


class Chunk(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """文本分块；向量仅存 Milvus 引用 ID，不在 MySQL 存向量本身。"""

    __tablename__ = "chunk"

    knowledge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    milvus_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    knowledge: Mapped[Knowledge] = relationship(back_populates="chunks")
