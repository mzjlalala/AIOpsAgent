"""第四阶段 Mock Tool 与工厂单测。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

from app.tools.context import ToolContext
from app.tools.executor import ExecuteRequest, MockExecutorTool
from app.tools.factory import build_mock_registry
from app.tools.knowledge import KnowledgeSearchQuery, MockKnowledgeTool
from app.tools.log import LogSearchQuery, MockLogTool
from app.tools.metric import MetricInstantQuery, MetricRangeQuery, MockMetricTool
from app.tools.types import ToolCategory


@pytest.fixture
def ctx() -> ToolContext:
    return ToolContext(trace_id="trace-mock-1")


@pytest.mark.asyncio
async def test_mock_metric_range_and_instant(ctx: ToolContext) -> None:
    tool = MockMetricTool()
    now = datetime.now(UTC)
    range_result = await tool.query_range(
        MetricRangeQuery(
            metric="cpu_usage",
            start=now,
            end=now,
            step="1m",
            labels={"app": "api"},
        ),
        context=ctx,
    )
    assert range_result.success is True
    data = cast(dict[str, Any], range_result.data)
    assert data["metric"] == "cpu_usage"
    assert data["labels"] == {"app": "api"}
    assert data["step"] == "1m"
    assert len(data["points"]) == 2
    assert {"ts", "value"} <= set(data["points"][0])

    instant_result = await tool.query_instant(
        MetricInstantQuery(metric="mem", labels={"app": "api"}, at=now),
        context=ctx,
    )
    assert instant_result.success is True
    instant = cast(dict[str, Any], instant_result.data)
    assert instant["metric"] == "mem"
    assert instant["value"] == 95.0
    assert "ts" in instant


@pytest.mark.asyncio
async def test_mock_log_search(ctx: ToolContext) -> None:
    tool = MockLogTool()
    now = datetime.now(UTC)
    result = await tool.search(
        LogSearchQuery(
            service="checkout",
            start=now,
            end=now,
            keyword="timeout",
            limit=1,
            filters={"env": "prod"},
        ),
        context=ctx,
    )
    assert result.success is True
    data = cast(dict[str, Any], result.data)
    assert data["service"] == "checkout"
    assert data["total"] == 1
    event = data["events"][0]
    assert {"ts", "level", "message", "fields"} <= set(event)
    assert event["fields"]["env"] == "prod"


@pytest.mark.asyncio
async def test_mock_executor_never_applies(ctx: ToolContext) -> None:
    tool = MockExecutorTool()
    dry = await tool.dry_run(
        ExecuteRequest(action="restart_pod", target="pod/a", dry_run=False),
        context=ctx,
    )
    assert dry.success is True
    dry_data = cast(dict[str, Any], dry.data)
    assert dry_data["dry_run"] is True
    assert dry_data["simulated"] is True
    assert dry_data["applied"] is False
    assert "plan" in dry_data

    realish = await tool.execute(
        ExecuteRequest(
            action="restart_pod",
            target="pod/a",
            params={"grace": 30},
            dry_run=False,
        ),
        context=ctx,
    )
    assert realish.success is True
    real_data = cast(dict[str, Any], realish.data)
    assert real_data["dry_run"] is False
    assert real_data["simulated"] is True
    assert real_data["applied"] is False


@pytest.mark.asyncio
async def test_mock_knowledge_rag_shape(ctx: ToolContext) -> None:
    tool = MockKnowledgeTool()
    result = await tool.search(
        KnowledgeSearchQuery(query="CPU", top_k=2),
        context=ctx,
    )
    assert result.success is True
    data = cast(dict[str, Any], result.data)
    assert data["query"] == "CPU"
    assert data["top_k"] == 2
    assert len(data["hits"]) == 2
    hit = data["hits"][0]
    assert {
        "rank",
        "score",
        "document_id",
        "knowledge_id",
        "chunk_id",
        "title",
        "content",
        "source",
        "metadata",
    } <= set(hit)
    assert len(data["citations"]) == 2
    citation = data["citations"][0]
    assert {"chunk_id", "source", "title"} <= set(citation)


def test_build_mock_registry() -> None:
    registry = build_mock_registry()
    assert len(registry) == 4
    by_name = {t.name for t in registry.list()}
    assert by_name == {
        "mock.metric",
        "mock.log",
        "mock.executor",
        "mock.knowledge",
    }
    assert len(registry.list(ToolCategory.METRIC)) == 1
    assert len(registry.list(ToolCategory.LOG)) == 1
    assert len(registry.list(ToolCategory.EXECUTOR)) == 1
    assert len(registry.list(ToolCategory.KNOWLEDGE)) == 1
