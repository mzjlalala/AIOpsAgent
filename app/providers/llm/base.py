"""LLM Provider 抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence

from app.providers.llm.types import ChatMessage, LLMCompletion, ToolSpec


class BaseLLMProvider(ABC):
    """统一 LLM 抽象；纯文本与多轮 Function Calling。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称标识。"""

    @abstractmethod
    async def acomplete(self, *, system: str, prompt: str) -> str:
        """完成一次补全，返回纯文本。"""

    async def astream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        """流式补全；默认实现为一次 ``acomplete`` 后整段产出。"""
        text = await self.acomplete(system=system, prompt=prompt)
        if text:
            yield text

    async def acomplete_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        tool_choice: str = "auto",
    ) -> LLMCompletion:
        """多轮补全；默认忽略 tools，退化为 system+user 文本补全。"""
        _ = tools, tool_choice
        system, prompt = _flatten_for_text(messages)
        content = await self.acomplete(system=system, prompt=prompt)
        return LLMCompletion(content=content, tool_calls=[])

    async def astream_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
    ) -> AsyncIterator[str]:
        """多轮流式文本；默认忽略 tools。"""
        _ = tools
        system, prompt = _flatten_for_text(messages)
        async for delta in self.astream(system=system, prompt=prompt):
            yield delta


def _flatten_for_text(messages: Sequence[ChatMessage]) -> tuple[str, str]:
    system_parts: list[str] = []
    other: list[str] = []
    for msg in messages:
        text = msg.content or ""
        if msg.role == "system":
            if text:
                system_parts.append(text)
            continue
        if msg.role == "tool":
            other.append(f"[tool:{msg.name or msg.tool_call_id}] {text}")
        elif msg.role == "assistant" and msg.tool_calls:
            names = ", ".join(tc.name for tc in msg.tool_calls)
            other.append(f"[assistant tool_calls: {names}] {text}".strip())
        else:
            other.append(f"{msg.role}: {text}")
    system = "\n".join(system_parts) or "You are a helpful assistant."
    prompt = "\n".join(other) if other else ""
    return system, prompt
