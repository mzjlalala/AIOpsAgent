"""对话与消息 ORM 模型。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class Conversation(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """聊天 / 排查对话线程。"""

    __tablename__ = "conversation"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    session_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_sessions.id"), nullable=True, index=True
    )
    incident_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("incident.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    user: Mapped[User] = relationship(back_populates="conversations")
    session: Mapped[UserSession | None] = relationship(back_populates="conversations")
    incident: Mapped[Incident | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(back_populates="conversation")


class Message(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """对话中的单条消息。"""

    __tablename__ = "message"

    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversation.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 列名使用 metadata，属性名避免与 SQLAlchemy 保留属性冲突
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
