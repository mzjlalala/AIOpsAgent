"""LLM 与 Embedding Provider（统一抽象）。"""

from app.providers.embedding import EmbeddingProvider, MockEmbeddingProvider

__all__ = ["EmbeddingProvider", "MockEmbeddingProvider"]
