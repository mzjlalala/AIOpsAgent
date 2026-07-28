"""Reporter：汇总 artifacts 与计划，产出报告。"""

from __future__ import annotations

from typing import Any

from app.agents.models import AgentArtifact, PlanStep
from app.agents.nodes.base import BaseAgentNode
from app.agents.state import AgentState


class ReporterNode(BaseAgentNode):
    """扫描 artifacts + plan，生成 report。"""

    name = "reporter"

    async def run(self, state: AgentState) -> dict[str, Any]:
        artifacts = [
            AgentArtifact.from_state_dict(a) for a in (state.get("artifacts") or [])
        ]
        plan = [PlanStep.model_validate(s) for s in (state.get("plan_steps") or [])]
        lines = [
            f"查询: {state.get('user_query', '')}",
            "计划:",
        ]
        for step in plan:
            lines.append(
                f"- [{step.status}] {step.step_id} -> {step.agent}: {step.goal}"
            )
        lines.append("Artifacts:")
        for item in artifacts:
            lines.append(
                f"- [{item.agent_name}/{item.artifact_type}] "
                f"success={item.success} id={item.id}"
            )
        prompt = "\n".join(lines)
        summary = await self.runtime.llm.acomplete(
            system="你是运维 Reporter，输出简短事故小结。",
            prompt=prompt,
        )
        visited = list(state.get("visited_agents") or [])
        if self.name not in visited:
            visited.append(self.name)
        report = f"{summary}\n\n---\n{prompt}"
        return {
            "report": report,
            "visited_agents": visited,
            "current_agent": "reporter",
        }
