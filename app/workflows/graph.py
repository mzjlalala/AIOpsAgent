"""Plan-Execute LangGraph 图（MemorySaver 强制）。"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.json_parse import parse_json_payload
from app.agents.models import PlanStep
from app.agents.runtime import AgentRuntime
from app.workflows.approval import approval_gate_node
from app.workflows.models import StepResult, WorkflowState
from app.workflows.normalize import normalize_plan
from app.workflows.policies import FallbackPolicy, RetryPolicy, TimeoutPolicy
from app.workflows.step_executor import StepExecutor, step_result_to_state_update


def _find_step(
    steps: list[dict[str, Any]],
    step_id: str | None,
) -> dict[str, Any] | None:
    if not step_id:
        return None
    return next((s for s in steps if s.get("step_id") == step_id), None)


def _set_step_status(
    steps: list[dict[str, Any]],
    step_id: str | None,
    status: str,
) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for item in steps:
        if item.get("step_id") == step_id:
            updated.append({**item, "status": status})
        else:
            updated.append(dict(item))
    return updated


def build_plan_execute_graph(
    runtime: AgentRuntime,
    *,
    checkpointer: Any | None = None,
    retry: RetryPolicy | None = None,
    timeout: TimeoutPolicy | None = None,
    fallback: FallbackPolicy | None = None,
    forced_failures: int = 0,
) -> Any:
    """编译 Plan-Execute 图；无 checkpointer 时使用 MemorySaver。"""
    saver = checkpointer if checkpointer is not None else MemorySaver()
    executor = StepExecutor(
        runtime,
        retry=retry,
        timeout=timeout,
        fallback=fallback,
        forced_failures=forced_failures,
    )

    async def load_or_init_plan(state: WorkflowState) -> dict[str, Any]:
        existing = list(state.get("plan_steps") or [])
        if existing:
            # 入参可能已归一化；再走一遍保证显式/缺省语义一致
            steps = normalize_plan(existing)
            return {
                "plan_steps": [s.model_dump(mode="json") for s in steps],
                "status": state.get("status") or "running",
                "artifacts": list(state.get("artifacts") or []),
                "last_step_abort": False,
            }
        query = state.get("user_query") or ""
        raw_text = await runtime.llm.acomplete(
            system=(
                "你是运维规划助手。只输出 JSON 数组，不要 Markdown 围栏以外的解释。"
                "每个元素必须含 step_id(字符串)、agent、goal。"
                "agent 只能是: metric, log, knowledge, executor。"
            ),
            prompt=(
                "请为以下运维目标制定排查/巡检 plan steps（JSON 数组）。\n"
                f"目标: {query}\n"
                "字段: step_id, agent, goal。"
                "全部为查询类步骤，不要设置 requires_approval=true。"
            ),
        )
        parsed = parse_json_payload(raw_text)
        if not isinstance(parsed, list):
            raise ValueError("LLM plan payload must be a list")
        steps = normalize_plan([dict(item) for item in parsed])
        return {
            "plan_steps": [s.model_dump(mode="json") for s in steps],
            "status": "running",
            "artifacts": list(state.get("artifacts") or []),
            "last_step_abort": False,
            "error": None,
        }

    def pick_next_step(state: WorkflowState) -> dict[str, Any]:
        steps = list(state.get("plan_steps") or [])
        nxt = next((s for s in steps if s.get("status") == "pending"), None)
        if nxt is None:
            return {"current_step_id": None}
        step_id = str(nxt["step_id"])
        return {
            "current_step_id": step_id,
            "plan_steps": _set_step_status(steps, step_id, "running"),
            "approval_approved": None,
            "status": "running",
        }

    def route_after_pick(
        state: WorkflowState,
    ) -> Literal["finalize", "approval_gate", "execute_step"]:
        step_id = state.get("current_step_id")
        if not step_id:
            return "finalize"
        step = _find_step(list(state.get("plan_steps") or []), step_id)
        if step and step.get("requires_approval"):
            return "approval_gate"
        return "execute_step"

    def route_after_approval(
        state: WorkflowState,
    ) -> Literal["execute_step", "mark_step_failed"]:
        if state.get("approval_approved"):
            return "execute_step"
        return "mark_step_failed"

    async def execute_step(state: WorkflowState) -> dict[str, Any]:
        step_id = state.get("current_step_id")
        raw = _find_step(list(state.get("plan_steps") or []), step_id)
        if raw is None:
            return step_result_to_state_update(
                StepResult(success=False, abort=False, error="missing step")
            )
        step = PlanStep.model_validate(raw)
        result = await executor.execute(step, state)
        return step_result_to_state_update(result)

    def route_after_execute(
        state: WorkflowState,
    ) -> Literal["update_step_success", "mark_step_failed"]:
        if state.get("last_step_success"):
            return "update_step_success"
        return "mark_step_failed"

    def update_step_success(state: WorkflowState) -> dict[str, Any]:
        steps = _set_step_status(
            list(state.get("plan_steps") or []),
            state.get("current_step_id"),
            "success",
        )
        artifacts = list(state.get("artifacts") or [])
        art = state.get("last_artifact")
        if art is not None:
            artifacts.append(art)
        return {
            "plan_steps": steps,
            "artifacts": artifacts,
            "last_step_abort": False,
        }

    def mark_step_failed(state: WorkflowState) -> dict[str, Any]:
        steps = _set_step_status(
            list(state.get("plan_steps") or []),
            state.get("current_step_id"),
            "failed",
        )
        abort = bool(state.get("last_step_abort"))
        return {
            "plan_steps": steps,
            "last_step_abort": abort,
            "error": state.get("last_step_error") or state.get("error"),
        }

    def route_after_failed(
        state: WorkflowState,
    ) -> Literal["pick_next_step", "finalize"]:
        if state.get("last_step_abort"):
            return "finalize"
        return "pick_next_step"

    def finalize(state: WorkflowState) -> dict[str, Any]:
        steps = list(state.get("plan_steps") or [])
        statuses = [str(s.get("status")) for s in steps]
        if state.get("last_step_abort"):
            terminal: str = "failed"
        elif any(st == "failed" for st in statuses):
            terminal = "completed_with_failures"
        else:
            terminal = "completed"
        return {
            "status": terminal,
            "current_step_id": None,
            "pending_approval": None,
        }

    graph = StateGraph(WorkflowState)
    graph.add_node("load_or_init_plan", load_or_init_plan)
    graph.add_node("pick_next_step", pick_next_step)
    graph.add_node("approval_gate", approval_gate_node)
    graph.add_node("execute_step", execute_step)
    graph.add_node("update_step_success", update_step_success)
    graph.add_node("mark_step_failed", mark_step_failed)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "load_or_init_plan")
    graph.add_edge("load_or_init_plan", "pick_next_step")
    graph.add_conditional_edges(
        "pick_next_step",
        route_after_pick,
        {
            "finalize": "finalize",
            "approval_gate": "approval_gate",
            "execute_step": "execute_step",
        },
    )
    graph.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "execute_step": "execute_step",
            "mark_step_failed": "mark_step_failed",
        },
    )
    graph.add_conditional_edges(
        "execute_step",
        route_after_execute,
        {
            "update_step_success": "update_step_success",
            "mark_step_failed": "mark_step_failed",
        },
    )
    graph.add_edge("update_step_success", "pick_next_step")
    graph.add_conditional_edges(
        "mark_step_failed",
        route_after_failed,
        {
            "pick_next_step": "pick_next_step",
            "finalize": "finalize",
        },
    )
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=saver)
