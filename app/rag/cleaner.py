"""文本清洗。"""

from __future__ import annotations

import re

from app.rag.models import Document


class TextCleaner:
    """轻量清洗：统一换行、压缩空白、去掉控制字符。"""

    _control_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

    def clean(self, document: Document) -> Document:
        """返回清洗后的 Document 副本。"""
        text = document.content.replace("\r\n", "\n").replace("\r", "\n")
        text = self._control_re.sub("", text)
        # 压缩连续空行，保留段落结构
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 行内多空格压成单空格（保留换行）
        lines = (re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n"))
        text = "\n".join(lines)
        text = text.strip()
        return document.model_copy(update={"content": text})
