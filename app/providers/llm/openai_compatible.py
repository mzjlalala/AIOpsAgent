"""OpenAI 兼容 Chat Completions（DeepSeek / Qwen / OpenAI）。"""

from __future__ import annotations

import httpx

from app.providers.llm.base import BaseLLMProvider


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    """调用 ``/v1/chat/completions``，返回 assistant 文本。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model_name: str = "deepseek-chat",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout = timeout_seconds

    @property
    def model_name(self) -> str:
        return self._model_name

    async def acomplete(self, *, system: str, prompt: str) -> str:
        url = f"{self._base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"unexpected LLM response: {data!r}") from exc
        if not isinstance(content, str):
            raise ValueError("LLM content is not a string")
        return content
