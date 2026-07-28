"""Workflow 领域模型与 LangGraph State。"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class ApprovalDecision(BaseModel):
    """人工审批恢复载荷（Command.resume）。"""

    approved: bool
    comment: str | None = None


class StepResult(BaseModel):
    """单步执行结果；abort=True 时图路由到 Finalize。"""

    success: bool
    abort: bool = False
    error: str | None = None
    artifact: dict[str, Any] | None = None


class WorkflowState(TypedDict, total=False):
    """Plan-Execute 图状态（可 checkpoint）。"""

    workflow_id: str
    trace_id: str
    user_query: str
    plan_steps: list[dict[str, Any]]
    current_step_id: str | None
    artifacts: list[dict[str, Any]]
    pending_approval: dict[str, Any] | None
    last_step_abort: bool
    last_step_success: bool
    last_step_error: str | None
    last_artifact: dict[str, Any] | None
    approval_approved: bool | None
    status: str
    error: str | None
    thread_id: str


WorkflowStatus = Literal[
    "running",
    "waiting_approval",
    "completed",
    "completed_with_failures",
    "failed",
]


class WorkflowRun(BaseModel):
    """引擎对外投影。"""

    workflow_id: str
    thread_id: str
    status: WorkflowStatus
    user_query: str = ""
    plan_steps: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: dict[str, Any] | None = None
    error: str | None = None
    current_step_id: str | None = None

    @classmethod
    def from_state(
        cls,
        values: dict[str, Any] | None,
        *,
        interrupted: bool = False,
        interrupt_value: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        data = dict(values or {})
        status = str(data.get("status") or "running")
        pending = data.get("pending_approval")
        if interrupted:
            status = "waiting_approval"
            if interrupt_value is not None:
                pending = interrupt_value
        return cls(
            workflow_id=str(data.get("workflow_id") or ""),
            thread_id=str(data.get("thread_id") or data.get("workflow_id") or ""),
            status=status,  # type: ignore[arg-type]
            user_query=str(data.get("user_query") or ""),
            plan_steps=list(data.get("plan_steps") or []),
            artifacts=list(data.get("artifacts") or []),
            pending_approval=pending,
            error=data.get("error"),
            current_step_id=data.get("current_step_id"),
        )
