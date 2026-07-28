"""Health-check API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Payload returned by ``GET /health``."""

    status: str = Field(description="Service liveness indicator.")
    service: str = Field(description="Service name.")
    env: str = Field(description="Active application environment.")
    version: str = Field(description="Application version.")
