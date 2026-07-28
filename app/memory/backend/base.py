"""Memory 存储能力抽象（组合模式，非万能接口）。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.memory.models import BaseMemoryRecord
from app.schemas.filters import MetadataFilter
from app.tools.types import JsonValue


class ListStore(ABC):
    """列表型存储能力（对话轮次等）。"""

    @abstractmethod
    async def aappend(self, namespace: str, key: str, item: JsonValue) -> None:
        """追加一条记录。"""

    @abstractmethod
    async def aget(
        self, namespace: str, key: str, *, limit: int | None = None
    ) -> list[JsonValue]:
        """读取列表；limit 为最近 N 条（从尾部截取）。"""

    @abstractmethod
    async def aclear(self, namespace: str, key: str) -> None:
        """清空指定 key 的列表。"""


class KvStore(ABC):
    """键值存储能力（会话上下文等）。"""

    @abstractmethod
    async def aset(self, namespace: str, key: str, value: JsonValue) -> None:
        """写入键值。"""

    @abstractmethod
    async def aget(self, namespace: str, key: str) -> JsonValue | None:
        """读取键值。"""

    @abstractmethod
    async def adelete(self, namespace: str, key: str) -> None:
        """删除键。"""


class VectorMemoryStore(ABC):
    """向量记忆能力；只存已带 embedding 的记录（命名避开 RAG VectorStore）。"""

    @abstractmethod
    async def aupsert(
        self, namespace: str, records: Sequence[BaseMemoryRecord]
    ) -> None:
        """按 id upsert；要求 embedding 非空。"""

    @abstractmethod
    async def asearch(
        self,
        namespace: str,
        *,
        vector: Sequence[float],
        top_k: int = 5,
        filters: Sequence[MetadataFilter] | None = None,
    ) -> list[tuple[BaseMemoryRecord, float]]:
        """相似度检索。"""

    @abstractmethod
    async def adelete(self, namespace: str, ids: Sequence[str]) -> None:
        """按 id 删除。"""


class MemoryBackend:
    """能力组合容器，不是上帝接口。"""

    def __init__(
        self,
        lists: ListStore,
        kv: KvStore,
        vectors: VectorMemoryStore,
    ) -> None:
        self.lists = lists
        self.kv = kv
        self.vectors = vectors


class MemoryStoreError(Exception):
    """Memory 存储相关错误。"""
