"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.health import router as health_router
from app.config.logging import setup_logging
from app.config.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan hooks."""
    logger.info("OpsAgent starting")
    yield
    logger.info("OpsAgent shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful in tests).

    Returns:
        Configured FastAPI application instance.
    """
    resolved = settings or get_settings()
    setup_logging(resolved)

    application = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        debug=resolved.api_debug and resolved.is_dev,
        lifespan=lifespan,
    )
    application.state.settings = resolved
    application.include_router(health_router)
    return application


app = create_app()
