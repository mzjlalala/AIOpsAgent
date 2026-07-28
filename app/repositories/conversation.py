"""对话与消息 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """对话数据访问。"""

    model = Conversation

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_user(
        self, user_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[Conversation]:
        """列出某用户的对话。"""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(Conversation.id.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class MessageRepository(BaseRepository[Message]):
    """消息数据访问。"""

    model = Message

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_conversation(
        self, conversation_id: int, *, offset: int = 0, limit: int = 200
    ) -> list[Message]:
        """按对话列出消息（升序）。"""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .offset(offset)
            .limit(limit)
            .order_by(Message.id.asc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
