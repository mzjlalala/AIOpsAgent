"""OpenAI 兼容 Chat Completions（DeepSeek / Qwen / OpenAI）。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx

from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.types import (
    ChatMessage,
    LLMCompletion,
    ToolCall,
    ToolSpec,
)


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    """调用 ``/v1/chat/completions``，支持普通与 stream / Function Calling。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model_name: str = "deepseek-v4-pro",
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

    def _to_api_messages(self, messages: Sequence[ChatMessage]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for msg in messages:
            item: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                item["content"] = msg.content
            elif msg.role != "assistant" or not msg.tool_calls:
                item["content"] = ""
            if msg.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            if msg.name:
                item["name"] = msg.name
            out.append(item)
        return out

    @staticmethod
    def _parse_tool_calls(raw: Any) -> list[ToolCall]:
        if not isinstance(raw, list):
            return []
        calls: list[ToolCall] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            fn = item.get("function") or {}
            if not isinstance(fn, dict):
                continue
            name = fn.get("name")
            if not isinstance(name, str) or not name:
                continue
            args_raw = fn.get("arguments", "{}")
            arguments: dict[str, Any]
            if isinstance(args_raw, dict):
                arguments = args_raw
            elif isinstance(args_raw, str):
                try:
                    parsed = json.loads(args_raw or "{}")
                    arguments = parsed if isinstance(parsed, dict) else {}
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = {}
            call_id = item.get("id")
            if not isinstance(call_id, str) or not call_id:
                call_id = f"call_{len(calls)}"
            calls.append(ToolCall(id=call_id, name=name, arguments=arguments))
        return calls

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

    async def acomplete_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        tool_choice: str = "auto",
    ) -> LLMCompletion:
        url = f"{self._base_url}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": self._to_api_messages(messages),
            "temperature": 0.2,
            "stream": False,
        }
        if tools:
            payload["tools"] = [t.model_dump() for t in tools]
            payload["tool_choice"] = tool_choice
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"unexpected LLM response: {data!r}") from exc
        content = message.get("content")
        if content is not None and not isinstance(content, str):
            content = str(content)
        return LLMCompletion(
            content=content,
            tool_calls=self._parse_tool_calls(message.get("tool_calls")),
        )

    async def astream_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
    ) -> AsyncIterator[str]:
        url = f"{self._base_url}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": self._to_api_messages(messages),
            "temperature": 0.2,
            "stream": True,
        }
        if tools:
            payload["tools"] = [t.model_dump() for t in tools]
            payload["tool_choice"] = "none"
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
