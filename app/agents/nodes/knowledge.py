"""Knowledge 专家节点。"""

from __future__ import annotations

from typing import Any, cast

from app.agents.nodes.base import BaseAgentNode
from app.agents.state import AgentState
from app.tools.context import ToolContext
from app.tools.knowledge import BaseKnowledgeTool, KnowledgeSearchQuery


class KnowledgeAgentNode(BaseAgentNode):
    """调用 mock.knowledge，完整 ToolResult 写入 artifact。"""

    name = "knowledge"

    async def run(self, state: AgentState) -> dict[str, Any]:
        tool = cast(BaseKnowledgeTool, self.runtime.tools.get("mock.knowledge"))
        ctx = ToolContext(trace_id=state.get("trace_id") or "agent-trace")
        query = state.get("user_query") or "运维排查"
        result = await tool.search(
            KnowledgeSearchQuery(query=query, top_k=3),
            context=ctx,
        )
        visited = list(state.get("visited_agents") or [])
        if self.name not in visited:
            visited.append(self.name)
        artifact = self.artifact_from_tool_result(state, result)
        data = dict(artifact.data)
        if self.runtime.rag is not None:
            rag_result = await self.runtime.rag.arun(query, top_k=3)
            data["rag"] = rag_result.model_dump(mode="json")
            artifact = artifact.model_copy(update={"data": data})
        return {
            "visited_agents": visited,
            "artifacts": self.with_artifact(state, artifact),
        }
