"""Mock Embedding Provider 单测。"""

from __future__ import annotations

import pytest

from app.providers.embedding import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_mock_embedding_deterministic_and_normalized() -> None:
    provider = MockEmbeddingProvider(dimensions=64)
    assert provider.dimensions == 64
    assert provider.model_name == "mock-sha256"

    v1 = await provider.embed_query("CPU 打满")
    v2 = await provider.embed_query("CPU 打满")
    v3 = await provider.embed_query("OOM")
    assert v1 == v2
    assert v1 != v3
    assert len(v1) == 64
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-6

    docs = await provider.embed_documents(["a", "b"])
    assert len(docs) == 2
    assert docs[0] == await provider.embed_query("a")


def test_mock_embedding_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError):
        MockEmbeddingProvider(dimensions=0)
