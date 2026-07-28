"""Metric 专家节点。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from app.agents.nodes.base import BaseAgentNode
from app.agents.state import AgentState
from app.tools.context import ToolContext
from app.tools.metric import BaseMetricTool, MetricInstantQuery


class MetricAgentNode(BaseAgentNode):
    """调用 mock.metric，完整 ToolResult 写入 artifact。"""

    name = "metric"

    async def run(self, state: AgentState) -> dict[str, Any]:
        tool = cast(BaseMetricTool, self.runtime.tools.get("mock.metric"))
        ctx = ToolContext(trace_id=state.get("trace_id") or "agent-trace")
        result = await tool.query_instant(
            MetricInstantQuery(
                metric="cpu_usage",
                at=datetime.now(UTC),
                labels={"service": self.runtime.config.default_service},
            ),
            context=ctx,
        )
        visited = list(state.get("visited_agents") or [])
        if self.name not in visited:
            visited.append(self.name)
        artifact = self.artifact_from_tool_result(state, result)
        return {
            "visited_agents": visited,
            "artifacts": self.with_artifact(state, artifact),
        }
