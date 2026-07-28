"""Application settings loaded from environment variables."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    """Supported deployment environments."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class Settings(BaseSettings):
    """Central configuration for OpsAgent.

    Values are read from environment variables and an optional ``.env`` file.
    Business code must depend on this object rather than reading ``os.environ``
    directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="OpsAgent", description="Service display name.")
    app_env: AppEnv = Field(default=AppEnv.DEV, description="Runtime environment.")
    log_level: str = Field(default="INFO", description="Loguru log level.")
    api_host: str = Field(default="0.0.0.0", description="Uvicorn bind host.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Uvicorn port.")
    api_debug: bool = Field(
        default=False,
        description="Enable FastAPI debug mode (dev only).",
    )

    @property
    def is_dev(self) -> bool:
        """Return True when running in the development environment."""
        return self.app_env == AppEnv.DEV

    @property
    def is_prod(self) -> bool:
        """Return True when running in the production environment."""
        return self.app_env == AppEnv.PROD


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
