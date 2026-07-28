"""WorkflowEngine：start / resume(Command) / get_status / astream。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from langgraph.types import Command

from app.agents.runtime import AgentRuntime
from app.workflows.models import WorkflowRun
from app.workflows.normalize import normalize_plan


class WorkflowNotFoundError(LookupError):
    """thread / workflow 在 checkpointer 中不存在。"""


class WorkflowEngine:
    """外层 Plan-Execute 引擎；真相源为 Checkpointer + WorkflowState。"""

    def __init__(self, runtime: AgentRuntime, graph: Any) -> None:
        self.runtime = runtime
        self.graph = graph

    def _config(self, workflow_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": workflow_id}}

    def _build_initial(
        self,
        *,
        user_query: str,
        plan_steps: list[dict[str, Any]] | None,
        workflow_id: str,
        trace_id: str | None,
    ) -> dict[str, Any]:
        tid = trace_id or f"trace-{workflow_id}"
        normalized: list[dict[str, Any]] = []
        if plan_steps is not None:
            normalized = [
                s.model_dump(mode="json") for s in normalize_plan(list(plan_steps))
            ]
        return {
            "workflow_id": workflow_id,
            "thread_id": workflow_id,
            "trace_id": tid,
            "user_query": user_query,
            "plan_steps": normalized,
            "current_step_id": None,
            "artifacts": [],
            "pending_approval": None,
            "last_step_abort": False,
            "last_step_success": False,
            "last_step_error": None,
            "last_artifact": None,
            "approval_approved": None,
            "status": "running",
            "error": None,
        }

    def _run_from_invoke(
        self,
        result: dict[str, Any],
        *,
        workflow_id: str,
    ) -> WorkflowRun:
        interrupts = result.get("__interrupt__") or ()
        interrupted = bool(interrupts)
        interrupt_value: dict[str, Any] | None = None
        if interrupted:
            first = interrupts[0]
            value = getattr(first, "value", first)
            if isinstance(value, dict):
                interrupt_value = value
        values = {k: v for k, v in result.items() if k != "__interrupt__"}
        if not values.get("workflow_id"):
            values["workflow_id"] = workflow_id
        if not values.get("thread_id"):
            values["thread_id"] = workflow_id
        return WorkflowRun.from_state(
            values,
            interrupted=interrupted,
            interrupt_value=interrupt_value,
        )

    async def start(
        self,
        *,
        user_query: str,
        plan_steps: list[dict[str, Any]] | None = None,
        workflow_id: str | None = None,
        trace_id: str | None = None,
    ) -> WorkflowRun:
        """启动工作流；命中闸门则 status=waiting_approval。"""
        wid = workflow_id or str(uuid.uuid4())
        initial = self._build_initial(
            user_query=user_query,
            plan_steps=plan_steps,
            workflow_id=wid,
            trace_id=trace_id,
        )
        result = await self.graph.ainvoke(initial, self._config(wid))
        return self._run_from_invoke(result, workflow_id=wid)

    async def resume(
        self,
        workflow_id: str,
        *,
        approved: bool,
        comment: str | None = None,
    ) -> WorkflowRun:
        """必须 Command(resume=...) + 同一 thread_id。"""
        result = await self.graph.ainvoke(
            Command(resume={"approved": approved, "comment": comment}),
            self._config(workflow_id),
        )
        return self._run_from_invoke(result, workflow_id=workflow_id)

    async def get_status(self, workflow_id: str) -> WorkflowRun:
        """从图 aget_state 投影；无 ApprovalIndex。"""
        snap = await self.graph.aget_state(self._config(workflow_id))
        values = snap.values or {}
        if not values.get("workflow_id"):
            raise WorkflowNotFoundError(workflow_id)
        interrupts = getattr(snap, "interrupts", ()) or ()
        interrupted = bool(interrupts)
        interrupt_value: dict[str, Any] | None = None
        if interrupted:
            value = getattr(interrupts[0], "value", None)
            if isinstance(value, dict):
                interrupt_value = value
        return WorkflowRun.from_state(
            values,
            interrupted=interrupted,
            interrupt_value=interrupt_value,
        )

    async def astream_start(
        self,
        *,
        user_query: str,
        plan_steps: list[dict[str, Any]] | None = None,
        workflow_id: str | None = None,
        trace_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """启动并以 updates 模式产出图更新（含 ``__interrupt__``）。"""
        wid = workflow_id or str(uuid.uuid4())
        initial = self._build_initial(
            user_query=user_query,
            plan_steps=plan_steps,
            workflow_id=wid,
            trace_id=trace_id,
        )
        async for update in self.graph.astream(
            initial,
            self._config(wid),
            stream_mode="updates",
        ):
            yield update

    async def astream_resume(
        self,
        workflow_id: str,
        *,
        approved: bool,
        comment: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Command(resume) 并以 updates 模式产出后续更新。"""
        async for update in self.graph.astream(
            Command(resume={"approved": approved, "comment": comment}),
            self._config(workflow_id),
            stream_mode="updates",
        ):
            yield update
