"""日志工具抽象与 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.results import ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory


class LogSearchQuery(BaseModel):
    """日志检索请求。"""

    service: str = Field(description="服务名。")
    keyword: str | None = Field(default=None, description="关键词。")
    start: datetime = Field(description="开始时间。")
    end: datetime = Field(description="结束时间。")
    limit: int = Field(default=100, ge=1, le=10000, description="返回条数上限。")
    filters: dict[str, str] = Field(default_factory=dict, description="额外过滤条件。")


class BaseLogTool(BaseTool):
    """日志工具抽象基类。"""

    category: ToolCategory = ToolCategory.LOG

    async def search(
        self,
        request: LogSearchQuery,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """检索日志。"""
        return await self.ainvoke(request, context=context, runtime=runtime)
