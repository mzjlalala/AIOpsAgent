"""对话短期记忆。"""

from __future__ import annotations

from app.memory.backend.base import ListStore
from app.memory.models import MemoryMessage

_NS = "conversation"


class ConversationMemory:
    """基于 ListStore 的对话轮次记忆。"""

    def __init__(self, lists: ListStore) -> None:
        self._lists = lists

    async def aappend(self, conversation_id: str, message: MemoryMessage) -> None:
        await self._lists.aappend(_NS, conversation_id, message.model_dump(mode="json"))

    async def aget_recent(
        self, conversation_id: str, *, limit: int = 20
    ) -> list[MemoryMessage]:
        raw = await self._lists.aget(_NS, conversation_id, limit=limit)
        return [MemoryMessage.model_validate(item) for item in raw]

    async def aclear(self, conversation_id: str) -> None:
        await self._lists.aclear(_NS, conversation_id)
