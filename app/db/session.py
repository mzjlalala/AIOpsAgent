"""异步 SQLAlchemy 引擎与 Session 辅助函数。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import Settings, get_settings

# 进程级缓存：避免重复创建引擎
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """根据应用配置创建异步引擎。"""
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """返回进程级异步引擎（首次调用时创建）。"""
    global _engine, _session_factory
    if _engine is None:
        resolved = settings or get_settings()
        _engine = create_engine_from_settings(resolved)
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _engine


def async_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """返回进程级异步 Session 工厂。"""
    get_engine(settings)
    assert _session_factory is not None
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：产出请求级异步 Session，成功则提交，异常则回滚。"""
    session_maker = async_session_factory()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_engine() -> None:
    """清空引擎/Session 工厂缓存（测试场景使用）。"""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
