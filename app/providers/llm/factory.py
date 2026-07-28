"""按 Settings 构建 LLM Provider。"""

from __future__ import annotations

from app.config.settings import AppEnv, Settings, get_settings
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLMProvider


def build_llm_provider(
    *,
    settings: Settings | None = None,
    scenario: str = "cpu_high",
) -> BaseLLMProvider:
    """``llm_provider=mock``、TEST 环境或缺少 api_key 时回落 Mock。"""
    cfg = settings or get_settings()
    if cfg.app_env == AppEnv.TEST:
        return MockLLMProvider(scenario=scenario)
    provider = (cfg.llm_provider or "mock").strip().lower()
    if provider in {"openai", "openai_compatible", "deepseek"}:
        if not cfg.llm_api_key:
            return MockLLMProvider(scenario=scenario)
        return OpenAICompatibleLLMProvider(
            api_key=cfg.llm_api_key,
            base_url=cfg.llm_base_url,
            model_name=cfg.llm_model,
            timeout_seconds=cfg.llm_timeout_seconds,
        )
    return MockLLMProvider(scenario=scenario)
