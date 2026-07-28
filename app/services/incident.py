"""Incident 编排服务：Workflow astream → 问答式 SSE。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.config.settings import Settings
from app.schemas.sse import SseEvent
from app.services.sse_map import map_update_to_events
from app.workflows.engine import WorkflowEngine, WorkflowNotFoundError
from app.workflows.factory import build_workflow_engine
from app.workflows.models import WorkflowRun

_TERMINAL = {"completed", "completed_with_failures", "failed"}


class IncidentService:
    """基于共享 checkpointer 的事故工作流 API 编排。"""

    def __init__(
        self,
        *,
        checkpointer: Any,
        default_engine: WorkflowEngine,
        settings: Settings | None = None,
    ) -> None:
        self.checkpointer = checkpointer
        self.default_engine = default_engine
        self.settings = settings

    def engine_for_scenario(self, scenario: str | None) -> WorkflowEngine:
        """按 scenario 构建引擎；始终复用同一 MemorySaver。"""
        if scenario is None:
            return self.default_engine
        return build_workflow_engine(
            scenario=scenario,
            checkpointer=self.checkpointer,
            with_memory=False,
            settings=self.settings,
        )

    async def stream_incident(
        self,
        *,
        query: str,
        scenario: str | None = None,
        workflow_id: str | None = None,
    ) -> AsyncIterator[SseEvent]:
        """启动排查并推送进度；结束后追加问答结论 ``answer``。"""
        wid = workflow_id or str(uuid.uuid4())
        engine = self.engine_for_scenario(scenario)
        try:
            async for update in engine.astream_start(
                user_query=query,
                workflow_id=wid,
            ):
                for event in map_update_to_events(update, workflow_id=wid):
                    yield event
            run = await self.default_engine.get_status(wid)
            if run.status in _TERMINAL:
                pieces: list[str] = []
                async for delta in self._stream_answer(engine, run):
                    if not delta:
                        continue
                    pieces.append(delta)
                    yield SseEvent(
                        workflow_id=wid,
                        type="answer_delta",
                        node="qa",
                        message=delta,
                        payload={"status": run.status},
                    )
                yield SseEvent(
                    workflow_id=wid,
                    type="answer",
                    node="qa",
                    message="".join(pieces),
                    payload={"status": run.status},
                )
        except Exception as exc:  # noqa: BLE001 — 转为 SSE error 帧
            yield SseEvent(
                workflow_id=wid,
                type="error",
                node="",
                message=str(exc) or exc.__class__.__name__,
                payload={"error": str(exc)},
            )

    async def stream_one_click(
        self,
        *,
        service: str | None = None,
        workflow_id: str | None = None,
    ) -> AsyncIterator[SseEvent]:
        """一键运维：固定巡检目标 + auto_ops / 真实 LLM 规划。"""
        svc = (service or "api").strip() or "api"
        query = (
            f"对服务 {svc} 执行一键健康巡检：查看指标与日志，"
            "检索知识库，并给出问题判断与解决建议。"
        )
        async for event in self.stream_incident(
            query=query,
            scenario="auto_ops",
            workflow_id=workflow_id,
        ):
            yield event

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
                message="需要人工确认后继续",
                payload=dict(run.pending_approval or {}),
            )
            return
        if run.status in _TERMINAL:
            yield SseEvent(
                workflow_id=workflow_id,
                type="completed",
                node="finalize",
                message="排查过程结束",
                payload={"status": run.status},
            )

    async def _stream_answer(
        self,
        engine: WorkflowEngine,
        run: WorkflowRun,
    ) -> AsyncIterator[str]:
        """流式产出问答结论。"""
        evidence = _compact_evidence(run.artifacts)
        system = (
            "你是资深运维问答助手。根据排查证据用中文回答用户，"
            "结构固定为：\n"
            "## 问题判断\n"
            "## 可能原因\n"
            "## 解决建议\n"
            "使用 Markdown。不要输出 JSON，不要提工作流、step、agent、SSE。"
        )
        prompt = (
            f"用户问题/目标：{run.user_query}\n\n"
            f"排查证据（摘要）：\n{evidence}\n\n"
            "请给出结论与可执行建议。"
        )
        async for delta in engine.runtime.llm.astream(system=system, prompt=prompt):
            yield delta

    async def _compose_answer(self, engine: WorkflowEngine, run: WorkflowRun) -> str:
        """兼容非流式调用。"""
        parts: list[str] = []
        async for delta in self._stream_answer(engine, run):
            parts.append(delta)
        return "".join(parts)


def _compact_evidence(artifacts: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for raw in artifacts[-8:]:
        agent = raw.get("agent_name") or "?"
        data = raw.get("data") or {}
        tool = data.get("tool_result") or {}
        success = tool.get("success", raw.get("success"))
        body = tool.get("data")
        try:
            body_s = json.dumps(body, ensure_ascii=False)[:500]
        except TypeError:
            body_s = str(body)[:500]
        lines.append(f"- [{agent}] success={success} data={body_s}")
    return "\n".join(lines) if lines else "（暂无工具证据）"
