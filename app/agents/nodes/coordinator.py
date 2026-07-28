"""Coordinator：委托 RouteStrategy 做代码路由。"""

from __future__ import annotations

from typing import Any

from app.agents.nodes.base import BaseAgentNode
from app.agents.router.base import RouteStrategy
from app.agents.router.rule import RuleBasedRouter
from app.agents.runtime import AgentRuntime
from app.agents.state import AgentState


class CoordinatorNode(BaseAgentNode):
    """根据路由策略决定 current_agent；不调用 LLM。"""

    name = "coordinator"

    def __init__(
        self,
        runtime: AgentRuntime,
        *,
        router: RouteStrategy | None = None,
    ) -> None:
        super().__init__(runtime)
        self._router = router or RuleBasedRouter()

    async def run(self, state: AgentState) -> dict[str, Any]:
        step_count = int(state.get("step_count") or 0) + 1
        visited = list(state.get("visited_agents") or [])
        updates: dict[str, Any] = {
            "step_count": step_count,
            "visited_agents": visited,
        }

        memory = self.runtime.memory
        if memory is not None and not state.get("memory_snapshot"):
            conv_id = state.get("conversation_id") or "default"
            sess_id = state.get("session_id") or "default"
            ctx = await memory.get_context(
                conversation_id=conv_id,
                session_id=sess_id,
                query=None,
                message_limit=self.runtime.config.message_limit,
            )
            updates["memory_snapshot"] = ctx.model_dump(mode="json")

        if step_count > self.runtime.config.max_steps:
            updates["current_agent"] = "reporter"
            return updates

        decision = await self._router.route(state)
        updates["current_agent"] = decision.next_agent
        bus = self.runtime.event_bus
        if bus is not None:
            await bus.emit(
                "agent.route",
                {
                    "next_agent": decision.next_agent,
                    "reason": decision.reason,
                    "trace_id": state.get("trace_id"),
                },
            )
        return updates
