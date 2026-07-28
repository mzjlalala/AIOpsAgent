"""知识检索工具抽象与 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.results import ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import JsonValue, ToolCategory


class KnowledgeSearchQuery(BaseModel):
    """知识库检索请求。"""

    query: str = Field(description="检索语句。")
    top_k: int = Field(default=5, ge=1, le=50, description="返回条数。")
    filters: dict[str, JsonValue] = Field(
        default_factory=dict, description="过滤条件。"
    )


class BaseKnowledgeTool(BaseTool):
    """知识检索工具抽象基类。"""

    category: ToolCategory = ToolCategory.KNOWLEDGE

    async def search(
        self,
        request: KnowledgeSearchQuery,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """检索知识库。"""
        return await self.ainvoke(request, context=context, runtime=runtime)
