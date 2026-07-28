"""工具执行结果与元数据类型。"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field

from app.tools.types import ToolCategory, ToolOutput


def _empty_tags() -> Mapping[str, str]:
    """默认空标签。"""
    return MappingProxyType({})


class ToolMetadata(BaseModel):
    """工具结果的类型化元数据（不可变）。"""

    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(description="工具名称。")
    category: ToolCategory = Field(description="工具分类。")
    attempt: int = Field(default=1, ge=1, description="第几次尝试。")
    tags: Mapping[str, str] = Field(
        default_factory=_empty_tags,
        description="额外字符串标签。",
    )


class ToolResult(BaseModel):
    """工具调用统一结果（不可变）。"""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(description="是否成功。")
    trace_id: str = Field(description="链路 ID，与 ToolContext.trace_id 对齐。")
    data: ToolOutput = Field(default=None, description="业务输出数据。")
    error: str | None = Field(default=None, description="失败时的错误信息。")
    latency_ms: float | None = Field(default=None, description="端到端耗时（毫秒）。")
    metadata: ToolMetadata = Field(description="类型化元数据。")
