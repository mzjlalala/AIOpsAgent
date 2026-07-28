"""SSE 事件信封。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SseEventType = Literal[
    "step_started",
    "step_succeeded",
    "step_failed",
    "waiting_approval",
    "completed",
    "error",
    "snapshot",
]


class SseEvent(BaseModel):
    """对外推送的统一 SSE 载荷。"""

    workflow_id: str
    type: SseEventType
    node: str = ""
    step_id: str | None = None
    agent: str | None = None
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        """编码为 SSE 文本帧。"""
        data = self.model_dump_json()
        return f"event: {self.type}\ndata: {data}\n\n"
