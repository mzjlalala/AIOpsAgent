"""MCP Tool 适配器抽象。"""

from __future__ import annotations

from abc import abstractmethod

from app.tools.base import BaseTool
from app.tools.types import JsonValue, ToolCategory


class MCPToolAdapter(BaseTool):
    """将 MCP Server 上的 tool 适配为本地 BaseTool 契约。

    本阶段仅定义接口，不引入 MCP SDK，不做真实远程调用。
    """

    category: ToolCategory = ToolCategory.MCP
    mcp_server: str
    mcp_tool_name: str

    @abstractmethod
    async def list_remote_tools(self) -> list[dict[str, JsonValue]]:
        """列出远端 MCP Server 上的工具描述。"""
