"""Agent 领域模型（PlanStep / Artifact；与 LangGraph State 解耦）。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """可追踪的计划步骤（为 Phase8 Workflow 预留 status）。"""

    step_id: str
    agent: str = Field(description="目标专家：metric/log/knowledge/executor 等。")
    goal: str
    status: Literal["pending", "running", "success", "failed", "retry"] = "pending"


class AgentArtifact(BaseModel):
    """统一证据链载体；Reporter / Reflection 只消费 artifacts。"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    artifact_type: str = Field(description="如 plan / tool_result / note。")
    success: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_state_dict(self) -> dict[str, Any]:
        """写入 LangGraph State 的可序列化形式。"""
        return self.model_dump(mode="json")

    @classmethod
    def from_state_dict(cls, raw: dict[str, Any]) -> AgentArtifact:
        return cls.model_validate(raw)
