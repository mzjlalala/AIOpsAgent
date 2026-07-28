"""链路追踪与工具调用 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace import AgentTrace, ToolCall, ToolResult
from app.repositories.base import BaseRepository


class AgentTraceRepository(BaseRepository[AgentTrace]):
    """Agent 链路数据访问。"""

    model = AgentTrace

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_workflow(self, workflow_id: int) -> list[AgentTrace]:
        """列出某工作流下的全部 Trace。"""
        stmt = (
            select(AgentTrace)
            .where(AgentTrace.workflow_id == workflow_id)
            .order_by(AgentTrace.id.asc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class ToolCallRepository(BaseRepository[ToolCall]):
    """工具调用数据访问。"""

    model = ToolCall

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)


class ToolResultRepository(BaseRepository[ToolResult]):
    """工具结果数据访问。"""

    model = ToolResult

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
