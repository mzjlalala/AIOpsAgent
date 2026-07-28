"""健康检查接口冒烟测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health 应返回服务存活信息。"""
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "OpsAgent"
    assert payload["env"] == "test"
    assert "version" in payload
