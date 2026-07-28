"""Agent 图状态：固定字段 + artifacts / plan_steps（dict 序列化）。"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph 共享状态。

    ``plan_steps`` / ``artifacts`` 存 ``PlanStep`` / ``AgentArtifact`` 的
    ``model_dump(mode=\"json\")`` 结果，便于 Checkpoint。
    禁止为每个专家无限增加 ``*_result`` 顶层字段。
    """

    trace_id: str
    user_query: str
    conversation_id: str | None
    session_id: str | None
    plan_steps: list[dict[str, Any]]
    current_agent: str
    visited_agents: list[str]
    step_count: int
    artifacts: list[dict[str, Any]]
    report: str | None
    memory_snapshot: dict[str, Any]
    messages: list[dict[str, Any]]
