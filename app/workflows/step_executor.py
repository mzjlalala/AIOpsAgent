"""StepExecutor：仅经 AgentRuntime.tools 执行 PlanStep。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.agents.models import AgentArtifact, PlanStep
from app.agents.runtime import AgentRuntime
from app.tools.context import ToolContext
from app.tools.executor import BaseExecutorTool, ExecuteRequest
from app.tools.knowledge import BaseKnowledgeTool, KnowledgeSearchQuery
from app.tools.log import BaseLogTool, LogSearchQuery
from app.tools.metric import BaseMetricTool, MetricInstantQuery
from app.tools.results import ToolResult
from app.workflows.models import StepResult, WorkflowState
from app.workflows.policies import (
    AttemptFailed,
    FallbackPolicy,
    RetryPolicy,
    TimeoutPolicy,
    run_with_retry,
)


def _artifact_from_tool_result(
    *,
    agent_name: str,
    result: ToolResult,
) -> AgentArtifact:
    meta = result.metadata
    tool_dump = {
        "success": result.success,
        "trace_id": result.trace_id,
        "data": result.data,
        "error": result.error,
        "latency_ms": result.latency_ms,
        "metadata": {
            "tool_name": meta.tool_name,
            "category": str(meta.category),
            "attempt": meta.attempt,
            "tags": dict(meta.tags),
        },
    }
    return AgentArtifact(
        agent_name=agent_name,
        artifact_type="tool_result",
        success=result.success,
        data={"tool_result": tool_dump},
    )


class StepExecutor:
    """按 agent 调用对应 mock tool；Retry/Timeout/Fallback 包在内部。"""

    def __init__(
        self,
        runtime: AgentRuntime,
        *,
        retry: RetryPolicy | None = None,
        timeout: TimeoutPolicy | None = None,
        fallback: FallbackPolicy | None = None,
        forced_failures: int = 0,
    ) -> None:
        self.runtime = runtime
        self.retry = retry or RetryPolicy()
        self.timeout = timeout or TimeoutPolicy()
        self.fallback = fallback or FallbackPolicy()
        self._forced_failures = forced_failures

    async def execute(self, step: PlanStep, state: WorkflowState) -> StepResult:
        async def _once() -> AgentArtifact:
            if self._forced_failures > 0:
                self._forced_failures -= 1
                raise AttemptFailed("forced failure for retry test")
            result = await self._call_tool(step, state)
            if not result.success:
                raise AttemptFailed(result.error or "tool failed")
            return _artifact_from_tool_result(agent_name=step.agent, result=result)

        try:
            artifact = await run_with_retry(
                _once,
                retry=self.retry,
                timeout=self.timeout,
            )
            return StepResult(
                success=True,
                abort=False,
                artifact=artifact.to_state_dict(),
            )
        except AttemptFailed as exc:
            abort = self.fallback.on_exhausted == "abort"
            return StepResult(success=False, abort=abort, error=exc.message)

    async def _call_tool(self, step: PlanStep, state: WorkflowState) -> ToolResult:
        trace_id = state.get("trace_id") or f"wf-{uuid.uuid4()}"
        ctx = ToolContext(trace_id=trace_id)
        service = self.runtime.config.default_service
        agent = step.agent

        if agent == "metric":
            tool = cast(BaseMetricTool, self.runtime.tools.get("mock.metric"))
            return await tool.query_instant(
                MetricInstantQuery(
                    metric="cpu_usage",
                    at=datetime.now(UTC),
                    labels={"service": service},
                ),
                context=ctx,
            )
        if agent == "log":
            tool = cast(BaseLogTool, self.runtime.tools.get("mock.log"))
            now = datetime.now(UTC)
            return await tool.search(
                LogSearchQuery(
                    service=service,
                    start=now - timedelta(minutes=15),
                    end=now,
                    keyword="error",
                    limit=20,
                ),
                context=ctx,
            )
        if agent == "knowledge":
            tool = cast(BaseKnowledgeTool, self.runtime.tools.get("mock.knowledge"))
            query = state.get("user_query") or step.goal or "运维排查"
            return await tool.search(
                KnowledgeSearchQuery(query=query, top_k=3),
                context=ctx,
            )
        if agent == "executor":
            tool = cast(BaseExecutorTool, self.runtime.tools.get("mock.executor"))
            return await tool.dry_run(
                ExecuteRequest(
                    action="restart_pod",
                    target=f"pod/{service}",
                    dry_run=True,
                ),
                context=ctx,
            )
        raise AttemptFailed(f"unsupported agent: {agent}")


def step_result_to_state_update(result: StepResult) -> dict[str, Any]:
    """将 StepResult 写入 WorkflowState 局部更新。"""
    return {
        "last_step_success": result.success,
        "last_step_abort": result.abort,
        "last_step_error": result.error,
        "last_artifact": result.artifact,
    }
