"""Incident 编排服务：Workflow astream → SSE。"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.schemas.sse import SseEvent
from app.services.sse_map import map_update_to_events
from app.workflows.engine import WorkflowEngine, WorkflowNotFoundError
from app.workflows.factory import build_workflow_engine
from app.workflows.models import WorkflowRun


class IncidentService:
    """基于共享 checkpointer 的事故工作流 API 编排。"""

    def __init__(
        self,
        *,
        checkpointer: Any,
        default_engine: WorkflowEngine,
    ) -> None:
        self.checkpointer = checkpointer
        self.default_engine = default_engine

    def engine_for_scenario(self, scenario: str | None) -> WorkflowEngine:
        """按 scenario 构建引擎；始终复用同一 MemorySaver。"""
        if scenario is None:
            return self.default_engine
        return build_workflow_engine(
            scenario=scenario,
            checkpointer=self.checkpointer,
            with_memory=False,
        )

    async def stream_incident(
        self,
        *,
        query: str,
        scenario: str | None = None,
        workflow_id: str | None = None,
    ) -> AsyncIterator[SseEvent]:
        """启动工作流并产出 SSE 事件，直至终态或闸门。"""
        wid = workflow_id or str(uuid.uuid4())
        engine = self.engine_for_scenario(scenario)
        try:
            async for update in engine.astream_start(
                user_query=query,
                workflow_id=wid,
            ):
                for event in map_update_to_events(update, workflow_id=wid):
                    yield event
        except Exception as exc:  # noqa: BLE001 — 转为 SSE error 帧
            yield SseEvent(
                workflow_id=wid,
                type="error",
                node="",
                message=str(exc) or exc.__class__.__name__,
                payload={"error": str(exc)},
            )

    async def get_status(self, workflow_id: str) -> WorkflowRun:
        return await self.default_engine.get_status(workflow_id)

    async def approve(
        self,
        workflow_id: str,
        *,
        approved: bool,
        comment: str | None = None,
    ) -> WorkflowRun:
        run = await self.default_engine.get_status(workflow_id)
        if run.status != "waiting_approval":
            raise PermissionError("workflow is not waiting for approval")
        return await self.default_engine.resume(
            workflow_id,
            approved=approved,
            comment=comment,
        )

    async def stream_events(self, workflow_id: str) -> AsyncIterator[SseEvent]:
        """续订：快照 + waiting_approval 或 completed。"""
        try:
            run = await self.default_engine.get_status(workflow_id)
        except WorkflowNotFoundError:
            raise
        yield SseEvent(
            workflow_id=workflow_id,
            type="snapshot",
            node="",
            message=f"status={run.status}",
            payload=run.model_dump(mode="json"),
        )
        if run.status == "waiting_approval":
            yield SseEvent(
                workflow_id=workflow_id,
                type="waiting_approval",
                node="approval_gate",
                step_id=run.current_step_id,
                agent=(run.pending_approval or {}).get("agent"),
                message="Waiting Approval...",
                payload=dict(run.pending_approval or {}),
            )
            return
        if run.status in {"completed", "completed_with_failures", "failed"}:
            yield SseEvent(
                workflow_id=workflow_id,
                type="completed",
                node="finalize",
                message=f"Workflow {run.status}",
                payload={"status": run.status},
            )
