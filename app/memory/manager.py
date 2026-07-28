"""MemoryManager 门面。"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from app.memory.conversation import ConversationMemory
from app.memory.experience import ExperienceMemory
from app.memory.long_term import LongMemory
from app.memory.models import (
    AgentMemoryContext,
    ExperienceRecord,
    MemoryMessage,
    SessionContext,
)
from app.memory.session import SessionMemory
from app.schemas.filters import MetadataFilter


class MemoryManager:
    """组合四类 Memory，供后续 Agent 统一调用。"""

    def __init__(
        self,
        conversation: ConversationMemory,
        session: SessionMemory,
        long_term: LongMemory,
        experience: ExperienceMemory,
    ) -> None:
        self.conversation = conversation
        self.session = session
        self.long_term = long_term
        self.experience = experience

    async def append_turn(self, conversation_id: str, message: MemoryMessage) -> None:
        await self.conversation.aappend(conversation_id, message)

    async def remember_experience(self, record: ExperienceRecord) -> ExperienceRecord:
        return await self.experience.asave(record)

    async def get_context(
        self,
        *,
        conversation_id: str,
        session_id: str,
        query: str | None = None,
        message_limit: int = 20,
        long_top_k: int = 3,
        experience_top_k: int = 3,
        experience_filters: Sequence[MetadataFilter] | None = None,
    ) -> AgentMemoryContext:
        """并发拉取对话、会话与（可选）长期/经验召回。"""
        messages_coro = self.conversation.aget_recent(
            conversation_id, limit=message_limit
        )
        session_coro = self.session.aget(session_id)

        if query:
            long_coro = self.long_term.arecall(query, top_k=long_top_k)
            exp_coro = self.experience.arecall(
                query, top_k=experience_top_k, filters=experience_filters
            )
            messages, session, long_hits, exp_hits = await asyncio.gather(
                messages_coro, session_coro, long_coro, exp_coro
            )
        else:
            messages, session = await asyncio.gather(messages_coro, session_coro)
            long_hits, exp_hits = [], []

        return AgentMemoryContext(
            messages=messages,
            session=session,
            long_hits=long_hits,
            experience_hits=exp_hits,
        )

    async def set_session(
        self, session_id: str, data: SessionContext | dict
    ) -> SessionContext:
        if isinstance(data, SessionContext):
            await self.session.aset(session_id, data.data)
            return data
        return await self.session.aupdate(session_id, data)
