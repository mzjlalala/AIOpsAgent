"""工作流与人工审批 ORM 模型。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Workflow(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """事故对应的 Plan-Execute 工作流实例。"""

    __tablename__ = "workflow"

    incident_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("incident.id"), nullable=False, index=True
    )
    plan_json: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    checkpoint_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_step: Mapped[str | None] = mapped_column(String(128), nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="workflows")
    traces: Mapped[list[AgentTrace]] = relationship(back_populates="workflow")
    approvals: Mapped[list[Approval]] = relationship(back_populates="workflow")


class Approval(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """执行修复操作前的人工审批门禁。"""

    __tablename__ = "approval"

    incident_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("incident.id"), nullable=False, index=True
    )
    workflow_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workflow.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    approver_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="approvals")
    workflow: Mapped[Workflow] = relationship(back_populates="approvals")
