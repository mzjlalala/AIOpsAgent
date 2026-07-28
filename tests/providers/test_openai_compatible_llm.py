"""OpenAI 兼容 LLM Provider 单测（不打真实网络）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.settings import AppEnv, Settings
from app.providers.llm.factory import build_llm_provider
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLMProvider


def test_build_llm_provider_test_env_forces_mock() -> None:
    settings = Settings(
        app_env=AppEnv.TEST,
        llm_provider="openai_compatible",
        llm_api_key="sk-test",
    )
    llm = build_llm_provider(settings=settings, scenario="auto_ops")
    assert isinstance(llm, MockLLMProvider)


def test_build_llm_provider_openai_compatible() -> None:
    settings = Settings(
        app_env=AppEnv.DEV,
        llm_provider="openai_compatible",
        llm_api_key="sk-test",
        llm_base_url="https://api.deepseek.com",
        llm_model="deepseek-v4-pro",
    )
    llm = build_llm_provider(settings=settings)
    assert isinstance(llm, OpenAICompatibleLLMProvider)
    assert llm.model_name == "deepseek-v4-pro"


@pytest.mark.asyncio
async def test_openai_compatible_acomplete_parses_content() -> None:
    provider = OpenAICompatibleLLMProvider(
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        model_name="deepseek-v4-pro",
    )
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '[{"step_id":"1","agent":"metric","goal":"x"}]',
                }
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=fake_response)

    target = "app.providers.llm.openai_compatible.httpx.AsyncClient"
    with patch(target, return_value=mock_client):
        text = await provider.acomplete(system="sys", prompt="plan steps")
    assert "metric" in text
    mock_client.post.assert_awaited_once()
