"""Embedding Provider 抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingProvider(ABC):
    """统一 Embedding 抽象；业务禁止直接调用厂商 SDK。"""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """向量维度。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称标识。"""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """将查询文本编码为向量。"""

    @abstractmethod
    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """批量将文档文本编码为向量。"""
