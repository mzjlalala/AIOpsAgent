"""Workflow 工厂：默认 Mock runtime + MemorySaver Plan-Execute 图。"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agents.factory import build_agent_runtime
from app.agents.runtime import AgentConfig, AgentRuntime
from app.workflows.engine import WorkflowEngine
from app.workflows.graph import build_plan_execute_graph
from app.workflows.policies import FallbackPolicy, RetryPolicy, TimeoutPolicy


def build_workflow_engine(
    *,
    runtime: AgentRuntime | None = None,
    scenario: str | None = None,
    config: AgentConfig | None = None,
    with_memory: bool = False,
    checkpointer: Any | None = None,
    retry: RetryPolicy | None = None,
    timeout: TimeoutPolicy | None = None,
    fallback: FallbackPolicy | None = None,
    forced_failures: int = 0,
) -> WorkflowEngine:
    """构建 WorkflowEngine；checkpointer 默认 MemorySaver（必选）。"""
    rt = runtime or build_agent_runtime(
        with_memory=with_memory,
        with_rag=False,
        config=config,
        scenario=scenario,
    )
    saver = checkpointer if checkpointer is not None else MemorySaver()
    graph = build_plan_execute_graph(
        rt,
        checkpointer=saver,
        retry=retry,
        timeout=timeout,
        fallback=fallback,
        forced_failures=forced_failures,
    )
    return WorkflowEngine(rt, graph)
