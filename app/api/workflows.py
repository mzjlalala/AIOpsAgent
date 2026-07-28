"""Workflow 状态 / 审批 / 事件续订。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.incident import ApproveRequest, WorkflowRunResponse
from app.services.incident import IncidentService
from app.workflows.engine import WorkflowNotFoundError

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _get_service(request: Request) -> IncidentService:
    return request.app.state.incident_service


@router.get("/{workflow_id}", response_model=WorkflowRunResponse)
async def get_workflow(workflow_id: str, request: Request) -> WorkflowRunResponse:
    """查询工作流状态。"""
    service = _get_service(request)
    try:
        run = await service.get_status(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    return WorkflowRunResponse.from_run(run)


@router.post("/{workflow_id}/approve", response_model=WorkflowRunResponse)
async def approve_workflow(
    workflow_id: str,
    body: ApproveRequest,
    request: Request,
) -> WorkflowRunResponse:
    """人工审批；必须处于 waiting_approval。"""
    service = _get_service(request)
    try:
        run = await service.approve(
            workflow_id,
            approved=body.approved,
            comment=body.comment,
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail="workflow is not waiting for approval",
        ) from exc
    return WorkflowRunResponse.from_run(run)


@router.get("/{workflow_id}/events")
async def workflow_events(workflow_id: str, request: Request) -> StreamingResponse:
    """续订 SSE：快照 + waiting_approval 或 completed。"""
    service = _get_service(request)

    async def event_gen() -> AsyncIterator[str]:
        try:
            async for event in service.stream_events(workflow_id):
                yield event.to_sse()
        except WorkflowNotFoundError:
            from app.schemas.sse import SseEvent

            yield SseEvent(
                workflow_id=workflow_id,
                type="error",
                message="workflow not found",
                payload={"status_code": 404},
            ).to_sse()

    # 预先校验存在性，便于返回真 404
    try:
        await service.get_status(workflow_id)
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
