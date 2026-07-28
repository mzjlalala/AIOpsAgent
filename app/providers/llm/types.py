"""LLM 多轮消息与 Function Calling 类型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ChatRole = Literal["system", "user", "assistant", "tool"]


class ToolCall(BaseModel):
    """一次函数调用。"""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """OpenAI 兼容 chat message。"""

    role: ChatRole
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ToolFunctionSpec(BaseModel):
    """function 字段。"""

    name: str
    description: str
    parameters: dict[str, Any]


class ToolSpec(BaseModel):
    """OpenAI tools[] 单项。"""

    type: Literal["function"] = "function"
    function: ToolFunctionSpec


class LLMCompletion(BaseModel):
    """非流式补全结果（可含 tool_calls）。"""

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
