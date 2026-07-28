"""ApprovalGate：interrupt 无副作用；恢复后分支。"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from app.workflows.models import WorkflowState


def approval_gate_node(state: WorkflowState) -> dict[str, Any]:
    """人工审批闸门。

    ``interrupt()`` 之前禁止写 store / 改 step / artifacts。
    恢复后从节点开头重跑，仅在拿到 resume 值后返回分支字段。
    """
    step_id = state.get("current_step_id")
    steps = list(state.get("plan_steps") or [])
    step = next((s for s in steps if s.get("step_id") == step_id), None)
    payload = {
        "workflow_id": state.get("workflow_id"),
        "thread_id": state.get("thread_id") or state.get("workflow_id"),
        "step_id": step_id,
        "agent": (step or {}).get("agent"),
        "goal": (step or {}).get("goal"),
        "action": "approve_step",
    }
    decision = interrupt(payload)
    approved = False
    comment: str | None = None
    if isinstance(decision, dict):
        approved = bool(decision.get("approved"))
        raw_comment = decision.get("comment")
        comment = str(raw_comment) if raw_comment is not None else None
    if approved:
        return {
            "approval_approved": True,
            "pending_approval": None,
            "status": "running",
            "last_step_error": None,
        }
    err = "approval_rejected"
    if comment:
        err = f"{err}: {comment}"
    return {
        "approval_approved": False,
        "pending_approval": None,
        "status": "running",
        "last_step_success": False,
        "last_step_abort": False,
        "last_step_error": err,
        "last_artifact": None,
    }
