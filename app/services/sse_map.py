"""将 LangGraph astream updates 映射为 SSE 事件。"""

from __future__ import annotations

from typing import Any

from app.schemas.sse import SseEvent

_AGENT_MESSAGES: dict[str, str] = {
    "metric": "Query Metrics...",
    "log": "Searching Logs...",
    "knowledge": "Searching Knowledge...",
    "executor": "Executing...",
}


def _artifact_summary(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = raw.get("data") or {}
    tool = data.get("tool_result") or {}
    return {
        "agent_name": raw.get("agent_name"),
        "artifact_type": raw.get("artifact_type"),
        "success": raw.get("success"),
        "tool_name": (tool.get("metadata") or {}).get("tool_name"),
    }


def map_update_to_events(
    update: dict[str, Any],
    *,
    workflow_id: str,
) -> list[SseEvent]:
    """将单次 ``stream_mode=updates`` 块转为 0..N 条 SSE 事件。"""
    events: list[SseEvent] = []

    if "__interrupt__" in update:
        interrupts = update.get("__interrupt__") or ()
        payload: dict[str, Any] = {}
        step_id = None
        agent = None
        if interrupts:
            first = interrupts[0]
            value = getattr(first, "value", first)
            if isinstance(value, dict):
                payload = value
                step_id = value.get("step_id")
                agent = value.get("agent")
        events.append(
            SseEvent(
                workflow_id=workflow_id,
                type="waiting_approval",
                node="approval_gate",
                step_id=str(step_id) if step_id is not None else None,
                agent=str(agent) if agent is not None else None,
                message="Waiting Approval...",
                payload=payload,
            )
        )
        return events

    for node, patch in update.items():
        if not isinstance(patch, dict):
            continue
        if node == "load_or_init_plan":
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="step_started",
                    node=node,
                    message="Planning...",
                    payload={"plan_size": len(patch.get("plan_steps") or [])},
                )
            )
        elif node == "pick_next_step":
            step_id = patch.get("current_step_id")
            if not step_id:
                continue
            agent = None
            for step in patch.get("plan_steps") or []:
                if step.get("step_id") == step_id:
                    agent = step.get("agent")
                    break
            message = _AGENT_MESSAGES.get(str(agent or ""), "Analyzing...")
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="step_started",
                    node=node,
                    step_id=str(step_id),
                    agent=str(agent) if agent else None,
                    message=message,
                )
            )
        elif node == "update_step_success":
            steps = patch.get("plan_steps") or []
            done = next(
                (s for s in reversed(steps) if s.get("status") == "success"),
                None,
            )
            arts = patch.get("artifacts") or []
            last_art = arts[-1] if arts else None
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="step_succeeded",
                    node=node,
                    step_id=str(done["step_id"]) if done else None,
                    agent=str(done["agent"]) if done and done.get("agent") else None,
                    message="Step succeeded",
                    payload=_artifact_summary(last_art),
                )
            )
        elif node == "mark_step_failed":
            steps = patch.get("plan_steps") or []
            failed = next(
                (s for s in reversed(steps) if s.get("status") == "failed"),
                None,
            )
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="step_failed",
                    node=node,
                    step_id=str(failed["step_id"]) if failed else None,
                    agent=(
                        str(failed["agent"]) if failed and failed.get("agent") else None
                    ),
                    message="Step failed",
                    payload={"error": patch.get("error")},
                )
            )
        elif node == "finalize":
            status = patch.get("status") or "completed"
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="completed",
                    node=node,
                    message=f"Workflow {status}",
                    payload={"status": status},
                )
            )
    return events
