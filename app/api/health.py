"""健康检查接口。"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app import __version__
from app.config.settings import Settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """返回服务存活信息。"""
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        env=settings.app_env.value,
        version=__version__,
    )
