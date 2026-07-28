"""领域 Schema 与抽象类约束测试。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from app.adapters.mcp import MCPToolAdapter
from app.tools.context import ToolContext
from app.tools.executor import BaseExecutorTool, ExecuteRequest
from app.tools.knowledge import BaseKnowledgeTool, KnowledgeSearchQuery
from app.tools.log import BaseLogTool, LogSearchQuery
from app.tools.metric import BaseMetricTool, MetricInstantQuery, MetricRangeQuery
from app.tools.results import ToolMetadata, ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory, ToolOutput


def test_metric_and_log_schemas() -> None:
    now = datetime.now(UTC)
    MetricRangeQuery(metric="cpu", start=now, end=now, labels={"app": "api"})
    MetricInstantQuery(metric="mem", labels={"app": "api"})
    LogSearchQuery(service="api", start=now, end=now, keyword="error")


def test_executor_and_knowledge_schemas() -> None:
    req = ExecuteRequest(action="restart", target="pod/a", dry_run=True)
    assert req.dry_run is True
    KnowledgeSearchQuery(query="OOM", top_k=3, filters={"env": "prod"})


def test_tool_result_requires_typed_metadata() -> None:
    result = ToolResult(
        success=True,
        trace_id="t1",
        data={"ok": True},
        metadata=ToolMetadata(
            tool_name="x",
            category=ToolCategory.METRIC,
            attempt=1,
        ),
    )
    assert result.trace_id == "t1"
    with pytest.raises(ValidationError):
        ToolResult(
            success=True,
            trace_id="t1",
            data={"ok": True},
            metadata="bad",  # type: ignore[arg-type]
        )


def test_domain_and_mcp_abstract_cannot_instantiate() -> None:
    """领域抽象与 MCP Adapter 不可直接实例化。"""
    with pytest.raises(TypeError):
        BaseMetricTool()  # type: ignore[abstract, call-arg]
    with pytest.raises(TypeError):
        BaseLogTool()  # type: ignore[abstract, call-arg]
    with pytest.raises(TypeError):
        BaseExecutorTool()  # type: ignore[abstract, call-arg]
    with pytest.raises(TypeError):
        BaseKnowledgeTool()  # type: ignore[abstract, call-arg]
    with pytest.raises(TypeError):
        MCPToolAdapter()  # type: ignore[abstract, call-arg]


class _CaptureExecutorTool(BaseExecutorTool):
    """捕获实际进入 _execute 的请求，用于验证 dry_run 强制语义。"""

    name = "capture_executor"
    description = "capture executor"
    timeout_seconds = 1.0

    def __init__(self) -> None:
        self.last_request: ExecuteRequest | None = None

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        assert isinstance(request, ExecuteRequest)
        self.last_request = request
        return {"dry_run": request.dry_run, "action": request.action}


@pytest.mark.asyncio
async def test_executor_dry_run_forces_true() -> None:
    """dry_run() 即使入参 dry_run=False 也必须强制为 True。"""
    tool = _CaptureExecutorTool()
    request = ExecuteRequest(action="restart_pod", target="pod/a", dry_run=False)
    result = await tool.dry_run(request)

    assert result.success is True
    assert tool.last_request is not None
    assert tool.last_request.dry_run is True
    assert request.dry_run is False
