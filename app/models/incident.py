"""事故、复盘报告与经验库 ORM 模型。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Incident(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """生产事故 / 告警案例。"""

    __tablename__ = "incident"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="p2")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporter_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    conversations: Mapped[list[Conversation]] = relationship(back_populates="incident")
    workflows: Mapped[list[Workflow]] = relationship(back_populates="incident")
    approvals: Mapped[list[Approval]] = relationship(back_populates="incident")
    reports: Mapped[list[Report]] = relationship(back_populates="incident")
    experiences: Mapped[list[Experience]] = relationship(back_populates="incident")


class Report(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """事故复盘报告。"""

    __tablename__ = "report"

    incident_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("incident.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="markdown")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")

    incident: Mapped[Incident] = relationship(back_populates="reports")


class Experience(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """可复用的成功/失败经验，供后续 Agent 学习。"""

    __tablename__ = "experience"

    incident_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("incident.id"), nullable=True, index=True
    )
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    incident: Mapped[Incident | None] = relationship(back_populates="experiences")
