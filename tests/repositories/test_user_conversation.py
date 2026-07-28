"""用户与对话 Repository CRUD 冒烟测试。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.user import User, UserSession
from app.repositories.conversation import ConversationRepository, MessageRepository
from app.repositories.user import UserRepository, UserSessionRepository


async def test_user_and_conversation_crud(db_session: AsyncSession) -> None:
    """创建用户/会话/对话/消息并回查。"""
    users = UserRepository(db_session)
    sessions = UserSessionRepository(db_session)
    conversations = ConversationRepository(db_session)
    messages = MessageRepository(db_session)

    user = await users.add(
        User(
            username="alice",
            email="alice@example.com",
            password_hash="hashed",
            role="admin",
        )
    )
    assert user.id is not None
    assert (await users.get_by_username("alice")) is not None

    session = await sessions.add(
        UserSession(
            user_id=user.id,
            token_hash="token-1",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    assert session.user_id == user.id

    conversation = await conversations.add(
        Conversation(
            user_id=user.id,
            session_id=session.id,
            title="CPU spike",
            status="active",
        )
    )
    await messages.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content="CPU is 100%",
            token_usage=12,
        )
    )

    listed = await messages.list_by_conversation(conversation.id)
    assert len(listed) == 1
    assert listed[0].content == "CPU is 100%"

    await users.soft_delete(user)
    assert user.deleted_at is not None
