"""文本切分策略。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.rag.models import Document, DocumentChunk


class TextSplitter(ABC):
    """切分策略抽象；便于后续 Markdown/Code/Recursive 扩展。"""

    @abstractmethod
    async def split(self, document: Document) -> list[DocumentChunk]:
        """将 Document 切为 DocumentChunk 列表（尚不含 embedding）。"""


class SimpleTextSplitter(TextSplitter):
    """按字符窗口切分，支持 overlap。"""

    def __init__(self, *, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须为正整数")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 须满足 0 <= overlap < chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def split(self, document: Document) -> list[DocumentChunk]:
        content = document.content
        if not content:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        ordinal = 0
        step = self._chunk_size - self._chunk_overlap
        while start < len(content):
            end = min(start + self._chunk_size, len(content))
            piece = content[start:end]
            chunk_id = f"chk-{document.document_id}-{ordinal}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    knowledge_id=document.knowledge_id,
                    title=document.title,
                    content=piece,
                    source=document.source,
                    namespace=document.namespace,
                    ordinal=ordinal,
                    metadata=dict(document.metadata),
                    embedding=None,
                )
            )
            ordinal += 1
            if end >= len(content):
                break
            start += step
        return chunks
