"""Agent 运行时与图工厂。"""

from __future__ import annotations

from typing import Any

from app.agents.events import AgentEventBus, NoopEventBus
from app.agents.graph import build_incident_graph
from app.agents.runtime import AgentConfig, AgentRuntime
from app.config.settings import Settings
from app.memory.factory import build_memory_manager
from app.providers.llm.factory import build_llm_provider
from app.rag.factory import build_rag_bundle
from app.tools.factory import build_mock_registry


def build_agent_runtime(
    *,
    with_memory: bool = True,
    with_rag: bool = False,
    config: AgentConfig | None = None,
    scenario: str | None = None,
    event_bus: AgentEventBus | None = None,
    settings: Settings | None = None,
) -> AgentRuntime:
    """按 Settings 注入 LLM（默认 Mock）+ Mock Tools；可选 Memory / RAG / EventBus。"""
    cfg = config or AgentConfig()
    if scenario is not None:
        cfg = AgentConfig(
            max_steps=cfg.max_steps,
            message_limit=cfg.message_limit,
            default_service=cfg.default_service,
            mock_llm_scenario=scenario,
        )
    rag = None
    if with_rag:
        rag = build_rag_bundle().retrieve
    return AgentRuntime(
        llm=build_llm_provider(
            settings=settings,
            scenario=cfg.mock_llm_scenario,
        ),
        tools=build_mock_registry(),
        config=cfg,
        memory=build_memory_manager() if with_memory else None,
        rag=rag,
        event_bus=event_bus or NoopEventBus(),
    )


def build_default_incident_app(
    *,
    with_memory: bool = True,
    with_rag: bool = False,
    config: AgentConfig | None = None,
    scenario: str | None = None,
    checkpointer: Any | None = None,
    event_bus: AgentEventBus | None = None,
) -> tuple[AgentRuntime, Any]:
    """返回 (runtime, compiled_graph)。不注入 FastAPI。"""
    runtime = build_agent_runtime(
        with_memory=with_memory,
        with_rag=with_rag,
        config=config,
        scenario=scenario,
        event_bus=event_bus,
    )
    return runtime, build_incident_graph(runtime, checkpointer=checkpointer)
