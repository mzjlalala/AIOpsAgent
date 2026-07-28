"""Tool 层基础类型定义。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

# JSON 可序列化标量与嵌套结构（禁止 Any）
type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)

# _execute / ToolResult.data 的统一输出类型
type ToolOutput = Mapping[str, JsonValue] | Sequence[JsonValue] | None


class ToolCategory(StrEnum):
    """工具分类。"""

    METRIC = "metric"
    LOG = "log"
    EXECUTOR = "executor"
    KNOWLEDGE = "knowledge"
    MCP = "mcp"
