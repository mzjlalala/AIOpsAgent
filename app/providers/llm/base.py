"""LLM Provider 抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BaseLLMProvider(ABC):
    """统一 LLM 抽象；只返回字符串，结构化解析在业务侧完成。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称标识。"""

    @abstractmethod
    async def acomplete(self, *, system: str, prompt: str) -> str:
        """完成一次补全，返回纯文本。"""

    async def astream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        """流式补全；默认实现为一次 ``acomplete`` 后整段产出。"""
        text = await self.acomplete(system=system, prompt=prompt)
        if text:
            yield text
