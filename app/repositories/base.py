"""通用异步 Repository 基类。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    """单个 ORM 模型的通用 CRUD 封装。"""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """按主键查询实体。"""
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        """新增实体并 flush，以便拿到自增 ID。"""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def save(self, entity: ModelT) -> ModelT:
        """保存已跟踪实体的待提交变更。"""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def soft_delete(self, entity: ModelT) -> None:
        """软删除：要求模型具备 SoftDeleteMixin。"""
        if not hasattr(entity, "deleted_at"):
            raise TypeError(f"{self.model.__name__} 不支持软删除")
        entity.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        await self.session.flush()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        """按主键分页列表查询。"""
        stmt = (
            select(self.model)
            .offset(offset)
            .limit(limit)
            .order_by(self.model.id)  # type: ignore[attr-defined]
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
