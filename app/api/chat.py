"""POST /chat — 普通对话 SSE（Function Calling）。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.chat import ChatService

router = APIRouter(tags=["chat"])


def _get_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post("/chat")
async def create_chat(
    body: ChatRequest,
    request: Request,
) -> StreamingResponse:
    """多轮对话；可选 Function Calling 查指标/日志/知识库。"""
    service = _get_service(request)

    async def event_gen() -> AsyncIterator[str]:
        async for event in service.stream_chat(
            body.message,
            conversation_id=body.conversation_id,
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
