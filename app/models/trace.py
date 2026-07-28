"""Agent 链路追踪与工具调用 ORM 模型。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class AgentTrace(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """工作流中单个 Agent/节点的执行 Span。"""

    __tablename__ = "agent_trace"

    workflow_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workflow.id"), nullable=False, index=True
    )
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    workflow: Mapped[Workflow] = relationship(back_populates="traces")
    tool_calls: Mapped[list[ToolCall]] = relationship(back_populates="trace")


class ToolCall(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """工具调用记录。"""

    __tablename__ = "tool_call"

    trace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("agent_trace.id"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    trace: Mapped[AgentTrace] = relationship(back_populates="tool_calls")
    result: Mapped[ToolResult | None] = relationship(
        back_populates="tool_call", uselist=False
    )


class ToolResult(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """工具调用结果。"""

    __tablename__ = "tool_result"

    tool_call_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tool_call.id"), unique=True, nullable=False
    )
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    tool_call: Mapped[ToolCall] = relationship(back_populates="result")
