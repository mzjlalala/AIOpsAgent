"""Executor 专家节点。"""

from __future__ import annotations

from typing import Any, cast

from app.agents.nodes.base import BaseAgentNode
from app.agents.state import AgentState
from app.tools.context import ToolContext
from app.tools.executor import BaseExecutorTool, ExecuteRequest


class ExecutorAgentNode(BaseAgentNode):
    """调用 mock.executor（dry_run），完整 ToolResult 写入 artifact。"""

    name = "executor"

    async def run(self, state: AgentState) -> dict[str, Any]:
        tool = cast(BaseExecutorTool, self.runtime.tools.get("mock.executor"))
        ctx = ToolContext(trace_id=state.get("trace_id") or "agent-trace")
        result = await tool.dry_run(
            ExecuteRequest(
                action="restart_pod",
                target=f"pod/{self.runtime.config.default_service}",
                dry_run=True,
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
