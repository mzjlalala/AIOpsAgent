"""进程内 Memory 能力实现。"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.memory.backend.base import (
    KvStore,
    ListStore,
    MemoryStoreError,
    VectorMemoryStore,
)
from app.memory.models import BaseMemoryRecord
from app.schemas.filters import MetadataFilter
from app.tools.types import JsonValue


class InMemoryListStore(ListStore):
    """进程内列表存储。"""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, list[JsonValue]]] = {}

    async def aappend(self, namespace: str, key: str, item: JsonValue) -> None:
        bucket = self._data.setdefault(namespace, {})
        bucket.setdefault(key, []).append(item)

    async def aget(
        self, namespace: str, key: str, *, limit: int | None = None
    ) -> list[JsonValue]:
        items = list(self._data.get(namespace, {}).get(key, []))
        if limit is None or limit < 0:
            return items
        if limit == 0:
            return []
        return items[-limit:]

    async def aclear(self, namespace: str, key: str) -> None:
        bucket = self._data.get(namespace)
        if bucket is not None:
            bucket.pop(key, None)


class InMemoryKvStore(KvStore):
    """进程内 KV 存储。"""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, JsonValue]] = {}

    async def aset(self, namespace: str, key: str, value: JsonValue) -> None:
        self._data.setdefault(namespace, {})[key] = value

    async def aget(self, namespace: str, key: str) -> JsonValue | None:
        return self._data.get(namespace, {}).get(key)

    async def adelete(self, namespace: str, key: str) -> None:
        bucket = self._data.get(namespace)
        if bucket is not None:
            bucket.pop(key, None)


class InMemoryVectorMemoryStore(VectorMemoryStore):
    """进程内向量记忆；余弦相似度；filter 仅 eq。"""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, BaseMemoryRecord]] = {}

    async def aupsert(
        self, namespace: str, records: Sequence[BaseMemoryRecord]
    ) -> None:
        bucket = self._data.setdefault(namespace, {})
        for record in records:
            if record.embedding is None:
                raise MemoryStoreError(f"record.embedding 为空，无法入库: {record.id}")
            bucket[record.id] = record

    async def asearch(
        self,
        namespace: str,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[BaseMemoryRecord, float]]:
        if top_k <= 0:
            return []
        scored: list[tuple[BaseMemoryRecord, float]] = []
        for record in self._data.get(namespace, {}).values():
            if record.embedding is None:
                continue
            if filters and not _match_filters(record, filters):
                continue
            score = _cosine_similarity(vector, record.embedding)
            scored.append((record, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    async def adelete(self, namespace: str, ids: Sequence[str]) -> None:
        bucket = self._data.get(namespace)
        if not bucket:
            return
        for record_id in ids:
            bucket.pop(record_id, None)


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise MemoryStoreError(f"向量维度不一致: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _match_filters(record: BaseMemoryRecord, filters: Sequence[MetadataFilter]) -> bool:
    for flt in filters:
        if flt.operator != "eq":
            raise MemoryStoreError(f"暂不支持的 filter operator: {flt.operator}")
        actual = _resolve_field(record, flt.field)
        if actual != flt.value:
            return False
    return True


def _resolve_field(record: BaseMemoryRecord, field: str) -> JsonValue:
    if field == "id":
        return record.id
    if field == "content":
        return record.content
    # Experience 等子类字段
    if hasattr(record, field):
        value: Any = getattr(record, field)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, dict):
            return value  # type: ignore[return-value]
    return record.metadata.get(field)
