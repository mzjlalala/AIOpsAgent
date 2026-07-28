"""FastAPI 应用工厂与 ASGI 入口。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from app.api.health import router as health_router
from app.api.incident import router as incident_router
from app.api.ops import router as ops_router
from app.api.workflows import router as workflows_router
from app.config.logging import setup_logging
from app.config.settings import Settings, get_settings
from app.services.incident import IncidentService
from app.workflows.factory import build_workflow_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：注入共享 MemorySaver WorkflowEngine。"""
    checkpointer = MemorySaver()
    settings: Settings = app.state.settings
    engine = build_workflow_engine(
        checkpointer=checkpointer,
        with_memory=False,
        settings=settings,
    )
    app.state.workflow_checkpointer = checkpointer
    app.state.workflow_engine = engine
    app.state.incident_service = IncidentService(
        checkpointer=checkpointer,
        default_engine=engine,
        settings=settings,
    )
    logger.info(
        "OpsAgent starting | llm_provider={} model={}",
        settings.llm_provider,
        settings.llm_model,
    )
    yield
    logger.info("OpsAgent shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """构建并配置 FastAPI 应用。

    Args:
        settings: 可选配置覆盖（测试场景常用）。

    Returns:
        已配置的 FastAPI 应用实例。
    """
    resolved = settings or get_settings()
    setup_logging(resolved)

    application = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        debug=resolved.api_debug and resolved.is_dev,
        lifespan=lifespan,
    )
    # 将配置挂到 app.state，便于路由与测试注入
    application.state.settings = resolved
    application.include_router(health_router)
    application.include_router(incident_router)
    application.include_router(ops_router)
    application.include_router(workflows_router)
    return application


app = create_app()
