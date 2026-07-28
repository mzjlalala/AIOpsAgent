"""工作流与审批 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Approval, Workflow
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """工作流数据访问。"""

    model = Workflow

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_incident(self, incident_id: int) -> list[Workflow]:
        """列出某事故关联的工作流。"""
        stmt = (
            select(Workflow)
            .where(Workflow.incident_id == incident_id)
            .order_by(Workflow.id.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class ApprovalRepository(BaseRepository[Approval]):
    """审批数据访问。"""

    model = Approval

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_pending_by_incident(self, incident_id: int) -> list[Approval]:
        """列出某事故下待审批记录。"""
        stmt = select(Approval).where(
            Approval.incident_id == incident_id,
            Approval.status == "pending",
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
