"""指标工具抽象与 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.results import ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory


class MetricRangeQuery(BaseModel):
    """区间指标查询请求。"""

    metric: str = Field(description="指标名称。")
    start: datetime = Field(description="开始时间。")
    end: datetime = Field(description="结束时间。")
    step: str = Field(default="1m", description="采样步长。")
    labels: dict[str, str] = Field(default_factory=dict, description="标签过滤。")


class MetricInstantQuery(BaseModel):
    """瞬时指标查询请求。"""

    metric: str = Field(description="指标名称。")
    at: datetime | None = Field(default=None, description="查询时间点。")
    labels: dict[str, str] = Field(default_factory=dict, description="标签过滤。")


class BaseMetricTool(BaseTool):
    """指标工具抽象基类。"""

    category: ToolCategory = ToolCategory.METRIC

    async def query_range(
        self,
        request: MetricRangeQuery,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """查询区间指标。"""
        return await self.ainvoke(request, context=context, runtime=runtime)

    async def query_instant(
        self,
        request: MetricInstantQuery,
        context: ToolContext | None = None,
        runtime: RuntimeDependencies | None = None,
    ) -> ToolResult:
        """查询瞬时指标。"""
        return await self.ainvoke(request, context=context, runtime=runtime)
