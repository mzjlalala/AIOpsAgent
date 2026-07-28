"""普通聊天服务：Function Calling 循环 + 流式终答。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Sequence

from app.memory.manager import MemoryManager
from app.memory.models import MemoryMessage
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.types import ChatMessage, ToolCall
from app.schemas.sse import SseEvent
from app.services.chat_tools import build_chat_tool_specs, dispatch_chat_tool
from app.tools.registry import ToolRegistry

_SYSTEM = (
    "你是资深运维助手 OpsAgent。用中文回答，可用 Function Calling 调用工具。"
    "闲聊、自我介绍、与运维无关的问题不要调用工具。"
    "涉及 CPU/内存/日志/排障手册时再使用工具。"
    "最终回答使用清晰 Markdown。"
)


class ChatService:
    """多轮对话 + 可选工具。"""

    def __init__(
        self,
        *,
        llm: BaseLLMProvider,
        tools: ToolRegistry,
        memory: MemoryManager,
        max_tool_rounds: int = 3,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._memory = memory
        self._max_tool_rounds = max_tool_rounds

    async def stream_chat(
        self,
        message: str,
        *,
        conversation_id: str | None = None,
    ) -> AsyncIterator[SseEvent]:
        cid = (conversation_id or "").strip() or str(uuid.uuid4())
        try:
            yield SseEvent(
                workflow_id=cid,
                type="session",
                node="chat",
                message="",
                payload={"conversation_id": cid},
            )
            await self._memory.append_turn(
                cid,
                MemoryMessage(role="user", content=message),
            )
            ctx = await self._memory.get_context(
                conversation_id=cid,
                session_id=cid,
                message_limit=20,
            )
            messages: list[ChatMessage] = [
                ChatMessage(role="system", content=_SYSTEM),
                *_history_to_messages(ctx.messages),
            ]
            # get_context 已含刚写入的 user；避免重复时检查末条
            if not messages or messages[-1].role != "user":
                messages.append(ChatMessage(role="user", content=message))

            specs = build_chat_tool_specs()
            for round_i in range(self._max_tool_rounds):
                completion = await self._llm.acomplete_messages(
                    messages,
                    tools=specs,
                    tool_choice="auto",
                )
                if not completion.tool_calls:
                    break

                messages.append(
                    ChatMessage(
                        role="assistant",
                        content=completion.content,
                        tool_calls=completion.tool_calls,
                    )
                )
                async for event in self._run_tool_calls(
                    cid, completion.tool_calls, messages
                ):
                    yield event
            else:
                messages.append(
                    ChatMessage(
                        role="user",
                        content="请基于已有工具结果直接回答用户，不要再调用工具。",
                    )
                )

            pieces: list[str] = []
            async for delta in self._llm.astream_messages(messages, tools=None):
                if not delta:
                    continue
                pieces.append(delta)
                yield SseEvent(
                    workflow_id=cid,
                    type="answer_delta",
                    node="chat",
                    message=delta,
                    payload={},
                )
            answer = "".join(pieces).strip() or "（无回复）"
            await self._memory.append_turn(
                cid,
                MemoryMessage(role="assistant", content=answer),
            )
            yield SseEvent(
                workflow_id=cid,
                type="answer",
                node="chat",
                message=answer,
                payload={},
            )
        except Exception as exc:  # noqa: BLE001
            yield SseEvent(
                workflow_id=cid,
                type="error",
                node="chat",
                message=str(exc) or exc.__class__.__name__,
                payload={"error": str(exc)},
            )

    async def _run_tool_calls(
        self,
        cid: str,
        calls: Sequence[ToolCall],
        messages: list[ChatMessage],
    ) -> AsyncIterator[SseEvent]:
        for call in calls:
            yield SseEvent(
                workflow_id=cid,
                type="tool_call",
                node="chat",
                message=f"正在调用 {call.name}…",
                payload={
                    "id": call.id,
                    "tool": call.name,
                    "args": call.arguments,
                },
            )
            summary, data = await dispatch_chat_tool(self._tools, call)
            yield SseEvent(
                workflow_id=cid,
                type="tool_result",
                node="chat",
                message=summary,
                payload={
                    "id": call.id,
                    "tool": call.name,
                    "data": data,
                },
            )
            messages.append(
                ChatMessage(
                    role="tool",
                    name=call.name,
                    tool_call_id=call.id,
                    content=json.dumps(
                        {"summary": summary, "data": data},
                        ensure_ascii=False,
                        default=str,
                    ),
                )
            )


def _history_to_messages(history: Sequence[MemoryMessage]) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for item in history:
        role = item.role if item.role in {"user", "assistant", "system"} else "user"
        out.append(ChatMessage(role=role, content=item.content))  # type: ignore[arg-type]
    return out
