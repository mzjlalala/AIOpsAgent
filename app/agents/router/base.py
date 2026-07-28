"""路由决策模型与策略抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.agents.state import AgentState


class RouteDecision(BaseModel):
    """路由结果。"""

    next_agent: str = Field(description="下一跳节点名。")
    reason: str = ""


class RouteStrategy(ABC):
    """可插拔路由策略；Phase7 使用规则路由，未来可换 LLMRouter。"""

    @abstractmethod
    async def route(self, state: AgentState) -> RouteDecision:
        """根据 State 决定下一 Agent。"""
