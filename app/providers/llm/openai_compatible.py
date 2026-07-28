"""OpenAI 兼容 Chat Completions（DeepSeek / Qwen / OpenAI）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.providers.llm.base import BaseLLMProvider


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    """调用 ``/v1/chat/completions``，支持普通与 stream 补全。"""

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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _messages(self, *, system: str, prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    async def acomplete(self, *, system: str, prompt: str) -> str:
        url = f"{self._base_url}/v1/chat/completions"
        payload = {
            "model": self._model_name,
            "messages": self._messages(system=system, prompt=prompt),
            "temperature": 0.2,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"unexpected LLM response: {data!r}") from exc
        if not isinstance(content, str):
            raise ValueError("LLM content is not a string")
        return content

    async def astream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        url = f"{self._base_url}/v1/chat/completions"
        payload = {
            "model": self._model_name,
            "messages": self._messages(system=system, prompt=prompt),
            "temperature": 0.2,
            "stream": True,
        }
        timeout = httpx.Timeout(self._timeout, connect=30.0)
        async with (
            httpx.AsyncClient(timeout=timeout) as client,
            client.stream(
                "POST",
                url,
                headers=self._headers(),
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                try:
                    delta = chunk["choices"][0]["delta"].get("content")
                except (KeyError, IndexError, TypeError, AttributeError):
                    continue
                if isinstance(delta, str) and delta:
                    yield delta
