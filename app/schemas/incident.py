"""Incident / Workflow API Schema。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """启动事故排查工作流。"""

    query: str = Field(min_length=1, description="用户故障描述。")
    scenario: str | None = Field(
        default=None,
        description="MockLLM scenario：cpu_high / memory_leak 等。",
    )


class ApproveRequest(BaseModel):
    """人工审批决策。"""

    approved: bool
    comment: str | None = None


class WorkflowRunResponse(BaseModel):
    """Workflow 状态 JSON 投影。"""

    workflow_id: str
    thread_id: str
    status: Literal[
        "running",
        "waiting_approval",
        "completed",
        "completed_with_failures",
        "failed",
    ]
    user_query: str = ""
    plan_steps: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: dict[str, Any] | None = None
    error: str | None = None
    current_step_id: str | None = None

    @classmethod
    def from_run(cls, run: Any) -> WorkflowRunResponse:
        return cls.model_validate(run.model_dump())
