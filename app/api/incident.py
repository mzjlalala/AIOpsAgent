"""POST /incident — 启动即 SSE。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.incident import IncidentCreate
from app.services.incident import IncidentService

router = APIRouter(tags=["incident"])


def _get_service(request: Request) -> IncidentService:
    return request.app.state.incident_service


@router.post("/incident")
async def create_incident(
    body: IncidentCreate,
    request: Request,
) -> StreamingResponse:
    """启动 Plan-Execute 工作流，以 SSE 推送执行过程。"""
    service = _get_service(request)

    async def event_gen() -> AsyncIterator[str]:
        async for event in service.stream_incident(
            query=body.query,
            scenario=body.scenario,
        ):
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
