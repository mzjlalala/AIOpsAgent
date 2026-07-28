"""基于 sha256 的确定性 Mock Embedding。"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

from app.providers.embedding.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """用 sha256 派生定长向量；同文同向量，便于单测与本地联调。"""

    def __init__(
        self, *, dimensions: int = 64, model_name: str = "mock-sha256"
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions 必须为正整数")
        self._dimensions = dimensions
        self._model_name = model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        """将文本 sha256 展开为归一化浮点向量。"""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw: list[float] = []
        # 循环使用 digest 字节，填满目标维度
        i = 0
        while len(raw) < self._dimensions:
            byte = digest[i % len(digest)]
            # 映射到 [-1, 1)
            raw.append((byte / 255.0) * 2.0 - 1.0)
            i += 1
            if i % len(digest) == 0:
                # 继续哈希以扩展熵，避免短周期重复
                digest = hashlib.sha256(digest).digest()

        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / norm for v in raw]
