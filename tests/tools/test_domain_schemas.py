"""领域 Schema 与抽象类约束测试。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.adapters.mcp import MCPToolAdapter
from app.tools.executor import ExecuteRequest
from app.tools.knowledge import KnowledgeSearchQuery
from app.tools.log import LogSearchQuery
from app.tools.metric import MetricInstantQuery, MetricRangeQuery
from app.tools.results import ToolMetadata, ToolResult
from app.tools.types import ToolCategory


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
    with pytest.raises(TypeError):
        MCPToolAdapter()  # type: ignore[abstract, call-arg]
