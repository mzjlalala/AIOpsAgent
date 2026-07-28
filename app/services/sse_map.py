"""将 LangGraph astream updates 映射为面向问答的 SSE 事件。"""

from __future__ import annotations

from typing import Any

from app.schemas.sse import SseEvent

_AGENT_START: dict[str, str] = {
    "metric": "正在查看监控面板指标…",
    "log": "正在检索近期错误与告警日志…",
    "knowledge": "正在查阅运维知识库与排障手册…",
    "executor": "正在做只读/演练类查询…",
}

_AGENT_DONE: dict[str, str] = {
    "metric": "已拿到指标数据",
    "log": "已整理相关日志线索",
    "knowledge": "已检索到可参考的处置建议",
    "executor": "演练查询已完成",
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
        "snippet": _snippet_from_tool(tool),
    }


def _snippet_from_tool(tool: dict[str, Any]) -> str:
    data = tool.get("data")
    if not isinstance(data, dict):
        return ""
    if "value" in data:
        return f"指标值≈{data.get('value')}"
    if "total" in data:
        return f"命中日志 {data.get('total')} 条"
    hits = data.get("hits")
    if isinstance(hits, list) and hits:
        title = (hits[0] or {}).get("title") or ""
        return f"知识命中：{title}"[:80]
    return ""


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
                message="需要人工确认后继续",
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
                    message="正在理解问题并制定排查思路…",
                    payload={"plan_size": len(patch.get("plan_steps") or [])},
                )
            )
        elif node == "pick_next_step":
            step_id = patch.get("current_step_id")
            if not step_id:
                continue
            agent = None
            goal = None
            for step in patch.get("plan_steps") or []:
                if step.get("step_id") == step_id:
                    agent = step.get("agent")
                    goal = step.get("goal")
                    break
            message = _AGENT_START.get(str(agent or ""), "正在继续排查…")
            if goal:
                message = f"{message}（{goal}）"
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
            agent = str(done["agent"]) if done and done.get("agent") else None
            message = _AGENT_DONE.get(agent or "", "本步排查完成")
            summary = _artifact_summary(last_art)
            if summary.get("snippet"):
                message = f"{message}：{summary['snippet']}"
            events.append(
                SseEvent(
                    workflow_id=workflow_id,
                    type="step_succeeded",
                    node=node,
                    step_id=str(done["step_id"]) if done else None,
                    agent=agent,
                    message=message,
                    payload=summary,
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
                    message="本步排查未成功，将根据已有线索继续/收束",
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
                    message="排查过程结束，正在汇总结论…",
                    payload={"status": status},
                )
            )
    return events
