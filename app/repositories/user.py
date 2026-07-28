"""用户与会话 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserSession
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户数据访问。"""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_username(self, username: str) -> User | None:
        """按用户名查询用户。"""
        stmt = select(User).where(User.username == username)
        return await self.session.scalar(stmt)


class UserSessionRepository(BaseRepository[UserSession]):
    """用户会话数据访问。"""

    model = UserSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        """按 token 哈希查询会话。"""
        stmt = select(UserSession).where(UserSession.token_hash == token_hash)
        return await self.session.scalar(stmt)
