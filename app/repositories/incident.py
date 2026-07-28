"""事故相关 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Experience, Incident, Report
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    """事故数据访问。"""

    model = Incident

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_status(
        self, status: str, *, offset: int = 0, limit: int = 100
    ) -> list[Incident]:
        """按状态筛选事故列表。"""
        stmt = (
            select(Incident)
            .where(Incident.status == status)
            .offset(offset)
            .limit(limit)
            .order_by(Incident.id.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class ReportRepository(BaseRepository[Report]):
    """复盘报告数据访问。"""

    model = Report

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_incident(self, incident_id: int) -> list[Report]:
        """列出某事故的复盘报告。"""
        stmt = select(Report).where(Report.incident_id == incident_id)
        result = await self.session.scalars(stmt)
        return list(result.all())


class ExperienceRepository(BaseRepository[Experience]):
    """经验库数据访问。"""

    model = Experience

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
