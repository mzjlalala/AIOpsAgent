"""Agent 节点基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.agents.models import AgentArtifact
from app.agents.runtime import AgentRuntime
from app.agents.state import AgentState
from app.tools.results import ToolResult


class BaseAgentNode(ABC):
    """所有图节点的统一基类。"""

    name: str = "base"

    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        result = await self.run(state)
        bus = self.runtime.event_bus
        if bus is not None:
            await bus.emit(
                "agent.node.completed",
                {
                    "agent": self.name,
                    "trace_id": state.get("trace_id"),
                    "keys": list(result),
                },
            )
        return result

    @abstractmethod
    async def run(self, state: AgentState) -> dict[str, Any]:
        """返回 State 局部更新。"""

    def with_artifact(
        self,
        state: AgentState,
        artifact: AgentArtifact,
    ) -> list[dict[str, Any]]:
        """追加一条 artifact（序列化后）并返回新列表。"""
        current = list(state.get("artifacts") or [])
        current.append(artifact.to_state_dict())
        return current

    def artifact_from_tool_result(
        self,
        state: AgentState,
        result: ToolResult,
        *,
        artifact_type: str = "tool_result",
        agent: str | None = None,
    ) -> AgentArtifact:
        """保留完整 ToolResult 链路（trace_id / success / metadata / data）。"""
        _ = state
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
            agent_name=agent or self.name,
            artifact_type=artifact_type,
            success=result.success,
            data={"tool_result": tool_dump},
        )

    @staticmethod
    def has_artifact(
        state: AgentState,
        agent_name: str,
        *,
        artifact_type: str | None = None,
    ) -> bool:
        for raw in state.get("artifacts") or []:
            item = AgentArtifact.from_state_dict(raw)
            if item.agent_name != agent_name:
                continue
            if artifact_type is None or item.artifact_type == artifact_type:
                return True
        return False
