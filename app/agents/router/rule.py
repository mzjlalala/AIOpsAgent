"""基于规则的 Coordinator 路由。"""

from __future__ import annotations

import re

from app.agents.models import AgentArtifact, PlanStep
from app.agents.router.base import RouteDecision, RouteStrategy
from app.agents.state import AgentState


class RuleBasedRouter(RouteStrategy):
    """依据 plan_steps / artifacts / query 关键词做确定性路由。"""

    async def route(self, state: AgentState) -> RouteDecision:
        query = (state.get("user_query") or "").lower()
        steps = [PlanStep.model_validate(s) for s in (state.get("plan_steps") or [])]
        artifacts = [
            AgentArtifact.from_state_dict(a) for a in (state.get("artifacts") or [])
        ]

        if not steps and not _has_artifact(artifacts, "planner", "plan"):
            return RouteDecision(next_agent="planner", reason="缺少计划")

        need_metric = any(s.agent == "metric" for s in steps) or bool(
            re.search(r"cpu|打满|oom|内存|负载", query, re.I)
        )
        need_log = (
            any(s.agent == "log" for s in steps)
            or bool(re.search(r"log|日志|error|报错", query, re.I))
            or need_metric
        )
        need_executor = any(s.agent == "executor" for s in steps) or bool(
            re.search(r"重启|回滚|执行", query, re.I)
        )

        if need_metric and not _has_artifact(artifacts, "metric", "tool_result"):
            return RouteDecision(next_agent="metric", reason="待采集指标")
        if need_log and not _has_artifact(artifacts, "log", "tool_result"):
            return RouteDecision(next_agent="log", reason="待检索日志")
        if not _has_artifact(artifacts, "knowledge", "tool_result"):
            return RouteDecision(next_agent="knowledge", reason="待检索知识库")
        if need_executor and not _has_artifact(artifacts, "executor", "tool_result"):
            return RouteDecision(next_agent="executor", reason="待演练执行")
        return RouteDecision(next_agent="reporter", reason="证据齐全，生成报告")


def _has_artifact(
    artifacts: list[AgentArtifact], agent_name: str, artifact_type: str
) -> bool:
    return any(
        a.agent_name == agent_name and a.artifact_type == artifact_type
        for a in artifacts
    )
