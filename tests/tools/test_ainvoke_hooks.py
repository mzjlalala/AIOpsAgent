"""BaseTool ainvoke / Hook / 同步异步 _execute 测试。"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel, ValidationError

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.results import ToolResult
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory, ToolOutput


class _EchoRequest(BaseModel):
    value: str


class _AsyncEchoTool(BaseTool):
    name = "async_echo"
    description = "async echo"
    category = ToolCategory.METRIC
    timeout_seconds = 2.0
    max_retries = 0

    def __init__(self) -> None:
        self.hooks: list[str] = []

    async def before(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> None:
        self.hooks.append("before")

    async def on_result(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        result: ToolResult,
    ) -> None:
        self.hooks.append("on_result")

    async def after(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        result: ToolResult,
    ) -> None:
        self.hooks.append("after")

    async def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        assert isinstance(request, _EchoRequest)
        return {"echo": request.value, "trace_id": context.trace_id}


class _SyncEchoTool(BaseTool):
    name = "sync_echo"
    description = "sync echo"
    category = ToolCategory.LOG
    timeout_seconds = 2.0

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        assert isinstance(request, _EchoRequest)
        return {"echo": request.value, "mode": "sync"}


class _TimeoutTool(BaseTool):
    name = "timeout_tool"
    description = "sleep forever-ish"
    category = ToolCategory.EXECUTOR
    timeout_seconds = 0.05
    max_retries = 0

    async def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        await asyncio.sleep(1.0)
        return {"ok": True}


class _FlakyTool(BaseTool):
    name = "flaky"
    description = "fails then succeeds"
    category = ToolCategory.KNOWLEDGE
    timeout_seconds = 2.0
    max_retries = 2
    retry_interval_seconds = 0.01

    def __init__(self) -> None:
        self.calls = 0
        self.errors = 0

    async def on_error(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
        exc: Exception,
    ) -> None:
        self.errors += 1

    async def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        self.calls += 1
        if self.calls < 2:
            raise RuntimeError("transient")
        return {"ok": True, "calls": self.calls}


@pytest.mark.asyncio
async def test_ainvoke_async_execute_and_hook_order() -> None:
    tool = _AsyncEchoTool()
    ctx = ToolContext(trace_id="trace-async")
    result = await tool.ainvoke(_EchoRequest(value="hello"), context=ctx)

    assert result.success is True
    assert result.trace_id == "trace-async"
    assert result.data == {"echo": "hello", "trace_id": "trace-async"}
    assert result.latency_ms is not None and result.latency_ms >= 0
    assert result.metadata.tool_name == "async_echo"
    assert tool.hooks == ["before", "on_result", "after"]


@pytest.mark.asyncio
async def test_ainvoke_sync_execute_via_to_thread() -> None:
    tool = _SyncEchoTool()
    result = await tool.ainvoke(_EchoRequest(value="world"))

    assert result.success is True
    assert result.data == {"echo": "world", "mode": "sync"}
    assert result.trace_id
    assert result.metadata.category == ToolCategory.LOG


@pytest.mark.asyncio
async def test_ainvoke_timeout() -> None:
    tool = _TimeoutTool()
    result = await tool.ainvoke(
        _EchoRequest(value="x"), context=ToolContext(trace_id="t-timeout")
    )

    assert result.success is False
    assert result.trace_id == "t-timeout"
    assert result.error is not None
    assert "超时" in result.error


@pytest.mark.asyncio
async def test_ainvoke_retry_then_success() -> None:
    tool = _FlakyTool()
    result = await tool.ainvoke(_EchoRequest(value="x"))

    assert result.success is True
    assert tool.calls == 2
    assert tool.errors == 1
    assert result.metadata.attempt == 2


def test_tool_context_is_frozen() -> None:
    ctx = ToolContext(trace_id="t1")
    with pytest.raises(ValidationError):
        ctx.trace_id = "t2"  # type: ignore[misc]


def test_runtime_dependencies_extensions() -> None:
    runtime = RuntimeDependencies(extensions={"http_client": object()})
    assert runtime.require("http_client") is not None
    with pytest.raises(KeyError):
        runtime.require("missing")
