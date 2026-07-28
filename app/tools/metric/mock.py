"""指标 Mock 工具：返回确定性内存假数据。"""

from __future__ import annotations

from pydantic import BaseModel

from app.tools.context import ToolContext
from app.tools.exceptions import ToolError
from app.tools.metric.base import BaseMetricTool, MetricInstantQuery, MetricRangeQuery
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolOutput


class MockMetricTool(BaseMetricTool):
    """Mock 指标工具（不访问真实 Prometheus）。"""

    name = "mock.metric"
    description = "返回确定性假指标数据，用于本地联调与测试。"
    timeout_seconds = 5.0

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        """按请求类型返回固定区间或瞬时指标。"""
        _ = runtime
        if isinstance(request, MetricRangeQuery):
            start_ts = request.start.isoformat()
            end_ts = request.end.isoformat()
            return {
                "metric": request.metric,
                "labels": dict(request.labels),
                "step": request.step,
                "points": [
                    {"ts": start_ts, "value": 72.5},
                    {"ts": end_ts, "value": 98.1},
                ],
                "trace_id": context.trace_id,
                "mock": True,
            }
        if isinstance(request, MetricInstantQuery):
            at = request.at.isoformat() if request.at is not None else None
            return {
                "metric": request.metric,
                "labels": dict(request.labels),
                "ts": at,
                "value": 95.0,
                "trace_id": context.trace_id,
                "mock": True,
            }
        raise ToolError(f"不支持的指标请求类型: {type(request).__name__}")
