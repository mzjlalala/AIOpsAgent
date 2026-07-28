"""会话级键值记忆。"""

from __future__ import annotations

from collections.abc import Mapping

from app.memory.backend.base import KvStore
from app.memory.models import SessionContext
from app.tools.types import JsonValue

_NS = "session"


class SessionMemory:
    """基于 KvStore 的会话上下文。"""

    def __init__(self, kv: KvStore) -> None:
        self._kv = kv

    async def aset(self, session_id: str, data: Mapping[str, JsonValue]) -> None:
        await self._kv.aset(_NS, session_id, dict(data))

    async def aget(self, session_id: str) -> SessionContext | None:
        value = await self._kv.aget(_NS, session_id)
        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError(f"session 数据必须是 dict，got {type(value).__name__}")
        return SessionContext(session_id=session_id, data=value)  # type: ignore[arg-type]

    async def aupdate(
        self, session_id: str, patch: Mapping[str, JsonValue]
    ) -> SessionContext:
        current = await self._kv.aget(_NS, session_id)
        base: dict[str, JsonValue] = dict(current) if isinstance(current, dict) else {}
        base.update(dict(patch))
        await self._kv.aset(_NS, session_id, base)
        return SessionContext(session_id=session_id, data=base)

    async def aclear(self, session_id: str) -> None:
        await self._kv.adelete(_NS, session_id)
