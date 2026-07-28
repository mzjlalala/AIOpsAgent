"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import AppEnv, Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Return deterministic settings for tests."""
    return Settings(
        app_name="OpsAgent",
        app_env=AppEnv.TEST,
        log_level="WARNING",
        api_host="127.0.0.1",
        api_port=8000,
        api_debug=False,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Return an HTTP test client bound to a fresh app instance."""
    application = create_app(settings=settings)
    with TestClient(application) as test_client:
        yield test_client
