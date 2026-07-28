"""工具注册表。"""

from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.exceptions import ToolAlreadyRegisteredError, ToolNotFoundError
from app.tools.types import ToolCategory


class ToolRegistry:
    """本地 Tool 注册与发现。"""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具；名称重复则抛错。"""
        if tool.name in self._tools:
            raise ToolAlreadyRegisteredError(f"工具已注册: {tool.name}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """按名称注销工具。"""
        if name not in self._tools:
            raise ToolNotFoundError(f"工具未注册: {name}")
        del self._tools[name]

    def get(self, name: str) -> BaseTool:
        """按名称获取工具。"""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"工具未注册: {name}") from exc

    def list(self, category: ToolCategory | None = None) -> list[BaseTool]:
        """列出工具；可按分类过滤。"""
        tools = list(self._tools.values())
        if category is None:
            return tools
        return [tool for tool in tools if tool.category == category]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
