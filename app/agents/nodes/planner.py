"""Planner：LLM 规划 + JSON 解析为 PlanStep。"""

from __future__ import annotations

from typing import Any

from app.agents.json_parse import parse_json_payload
from app.agents.models import AgentArtifact, PlanStep
from app.agents.nodes.base import BaseAgentNode
from app.agents.state import AgentState


class PlannerNode(BaseAgentNode):
    """调用 LLM 获取规划 JSON，写入 plan_steps 与 artifact。"""

    name = "planner"

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state.get("user_query") or ""
        prompt = (
            "请为以下运维问题制定排查 steps（JSON 数组，元素含 step_id/agent/goal）。\n"
            f"问题: {query}\n"
            "输出字段: plan steps"
        )
        raw = await self.runtime.llm.acomplete(
            system="你是运维 Planner，只输出 JSON 数组。",
            prompt=prompt,
        )
        parsed = parse_json_payload(raw)
        if not isinstance(parsed, list):
            raise ValueError("Planner 期望 JSON 数组")
        steps = [PlanStep.model_validate(item) for item in parsed]
        visited = list(state.get("visited_agents") or [])
        if self.name not in visited:
            visited.append(self.name)
        artifact = AgentArtifact(
            agent_name=self.name,
            artifact_type="plan",
            success=True,
            data={
                "steps": [s.model_dump(mode="json") for s in steps],
                "raw": raw,
            },
        )
        return {
            "plan_steps": [s.model_dump(mode="json") for s in steps],
            "visited_agents": visited,
            "artifacts": self.with_artifact(state, artifact),
        }
