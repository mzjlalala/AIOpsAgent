"""文档加载器：RawDocument → Document。"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from app.rag.models import Document, RawDocument


class DocumentLoader(ABC):
    """文档加载抽象。"""

    @abstractmethod
    async def load(self, raw: RawDocument) -> Document:
        """将原始文档转为逻辑 Document。"""


class TextDocumentLoader(DocumentLoader):
    """纯文本 / Markdown 内存加载（不解析复杂 Markdown AST）。"""

    async def load(self, raw: RawDocument) -> Document:
        title = _infer_title(raw)
        document_id = _stable_id("doc", raw.source, raw.content)
        knowledge_id = _stable_id("kn", raw.source, title)
        namespace = str(raw.metadata.get("namespace") or "default")
        return Document(
            document_id=document_id,
            knowledge_id=knowledge_id,
            title=title,
            source=raw.source,
            content=raw.content,
            namespace=namespace,
            metadata=dict(raw.metadata),
        )


def _infer_title(raw: RawDocument) -> str:
    meta_title = raw.metadata.get("title")
    if isinstance(meta_title, str) and meta_title.strip():
        return meta_title.strip()
    for line in raw.content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or Path(raw.source).stem
        if stripped:
            return stripped[:80]
    return Path(raw.source).stem or "untitled"


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"
