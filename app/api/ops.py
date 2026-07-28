"""一键运维 API。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.incident import OneClickOpsRequest
from app.services.incident import IncidentService

router = APIRouter(prefix="/ops", tags=["ops"])


def _get_service(request: Request) -> IncidentService:
    return request.app.state.incident_service


@router.post("/one-click")
async def one_click_ops(
    request: Request,
    body: OneClickOpsRequest | None = None,
) -> StreamingResponse:
    """一键健康巡检：Agent 自主规划，SSE 推送过程。"""
    service = _get_service(request)
    payload = body if body is not None else OneClickOpsRequest()

    async def event_gen() -> AsyncIterator[str]:
        async for event in service.stream_one_click(service=payload.service):
            yield event.to_sse()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
