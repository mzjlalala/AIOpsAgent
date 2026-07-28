"""pytest 共享 Fixture。"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.config.settings import AppEnv, Settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """返回测试用确定性配置。"""
    return Settings(
        app_name="OpsAgent",
        app_env=AppEnv.TEST,
        log_level="WARNING",
        api_host="127.0.0.1",
        api_port=8000,
        api_debug=False,
        database_url="sqlite+aiosqlite:///:memory:",
        database_url_sync="sqlite:///:memory:",
        database_echo=False,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """返回绑定到新应用实例的 HTTP 测试客户端。"""
    application = create_app(settings=settings)
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """产出基于内存 SQLite 的异步 Session。"""
    engine = create_async_engine(settings.database_url, echo=settings.database_echo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()
