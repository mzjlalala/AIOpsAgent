"""ORM 元数据冒烟测试。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401
from app.config.settings import Settings
from app.db.base import Base

# 第二阶段规划的 15 张业务表
EXPECTED_TABLES = {
    "users",
    "user_sessions",
    "conversation",
    "message",
    "incident",
    "agent_trace",
    "tool_call",
    "tool_result",
    "documents",
    "knowledge",
    "chunk",
    "report",
    "experience",
    "workflow",
    "approval",
}


async def test_metadata_create_all_creates_fifteen_tables(settings: Settings) -> None:
    """全部规划业务表应能在 SQLite 上成功建表。"""
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        table_names = set(Base.metadata.tables.keys())

    await engine.dispose()
    assert EXPECTED_TABLES.issubset(table_names)
    assert len(EXPECTED_TABLES) == 15
