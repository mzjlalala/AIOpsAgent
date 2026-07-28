"""Chat 请求 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """普通对话请求。"""

    message: str = Field(min_length=1, description="用户消息。")
    conversation_id: str | None = Field(
        default=None,
        description="会话 ID；缺省由服务端新建。",
    )
