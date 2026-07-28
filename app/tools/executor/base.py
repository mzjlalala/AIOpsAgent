"""执行类工具抽象与 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.results import ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import JsonValue, ToolCategory


class ExecuteRequest(BaseModel):
    """执行请求。

    生产实现必须尊重 dry_run：为 True 时只评估不落操作。
    """

    action: str = Field(description="动作名称，如 restart_pod。")
    target: str = Field(description="目标资源标识。")
    params: dict[str, JsonValue] = Field(default_factory=dict, description="动作参数。")
    dry_run: bool = Field(
        default=True, description="是否演练模式（默认 True，偏安全）。"
    )


class BaseExecutorTool(BaseTool):
    """执行类工具抽象基类。

    默认语义偏安全：``execute`` 透传请求；``dry_run`` 强制 dry_run=True。
    """

    category: ToolCategory = ToolCategory.EXECUTOR

    async def execute(
        self,
        request: ExecuteRequest,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """执行操作（是否真正落操作由请求 dry_run 与实现决定）。"""
        return await self.ainvoke(request, context=context, runtime=runtime)

    async def dry_run(
        self,
        request: ExecuteRequest,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """强制演练：即使请求 dry_run=False 也会改为 True。"""
        safe_request = request.model_copy(update={"dry_run": True})
        return await self.ainvoke(safe_request, context=context, runtime=runtime)
