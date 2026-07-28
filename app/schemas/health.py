"""健康检查 API Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """``GET /health`` 响应体。"""

    status: str = Field(description="服务存活状态。")
    service: str = Field(description="服务名称。")
    env: str = Field(description="当前运行环境。")
    version: str = Field(description="应用版本号。")
