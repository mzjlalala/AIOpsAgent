"""Agent 运行时依赖容器。"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.events import AgentEventBus, NoopEventBus
from app.memory.manager import MemoryManager
from app.providers.llm.base import BaseLLMProvider
from app.rag.retrieve import RetrievePipeline
from app.tools.registry import ToolRegistry


@dataclass
class AgentConfig:
    """Agent 图运行配置。"""

    max_steps: int = 8
    message_limit: int = 20
    default_service: str = "api"
    mock_llm_scenario: str = "cpu_high"


@dataclass
class AgentRuntime:
    """节点共享依赖：llm / tools / config / memory / rag / event_bus。"""

    llm: BaseLLMProvider
    tools: ToolRegistry
    config: AgentConfig = field(default_factory=AgentConfig)
    memory: MemoryManager | None = None
    rag: RetrievePipeline | None = None
    event_bus: AgentEventBus | None = None

    def __post_init__(self) -> None:
        if self.event_bus is None:
            self.event_bus = NoopEventBus()
