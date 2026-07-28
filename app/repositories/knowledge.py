"""知识库相关 Repository。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Chunk, Document, Knowledge
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """原始文档数据访问。"""

    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)


class KnowledgeRepository(BaseRepository[Knowledge]):
    """知识条目数据访问。"""

    model = Knowledge

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_document(self, document_id: int) -> list[Knowledge]:
        """列出某文档下的知识条目。"""
        stmt = select(Knowledge).where(Knowledge.document_id == document_id)
        result = await self.session.scalars(stmt)
        return list(result.all())


class ChunkRepository(BaseRepository[Chunk]):
    """分块数据访问。"""

    model = Chunk

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_knowledge(self, knowledge_id: int) -> list[Chunk]:
        """按序号列出某知识条目的分块。"""
        stmt = (
            select(Chunk)
            .where(Chunk.knowledge_id == knowledge_id)
            .order_by(Chunk.ordinal.asc(), Chunk.id.asc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
