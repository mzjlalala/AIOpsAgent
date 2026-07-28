"""Agent 事件总线抽象（为 SSE / 轨迹展示预留）。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentEventBus(ABC):
    """节点可向总线发布事件；Phase7 默认 Noop。"""

    @abstractmethod
    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """发布一条 Agent 事件。"""


class NoopEventBus(AgentEventBus):
    """空实现，不产生副作用。"""

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        _ = event_type, payload
