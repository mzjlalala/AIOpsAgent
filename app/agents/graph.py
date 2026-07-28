"""事故排查 Multi-Agent 图。

使用 LangGraph 1.x：``StateGraph`` + ``START``/``END`` + ``conditional_edges``。
禁止使用 LangChain ``AgentExecutor`` 或 0.x 图 API。
"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.coordinator import CoordinatorNode
from app.agents.nodes.executor import ExecutorAgentNode
from app.agents.nodes.knowledge import KnowledgeAgentNode
from app.agents.nodes.log import LogAgentNode
from app.agents.nodes.metric import MetricAgentNode
from app.agents.nodes.planner import PlannerNode
from app.agents.nodes.reporter import ReporterNode
from app.agents.runtime import AgentRuntime
from app.agents.state import AgentState

AgentName = Literal[
    "coordinator",
    "planner",
    "metric",
    "log",
    "knowledge",
    "executor",
    "reporter",
]


def _route_from_coordinator(state: AgentState) -> str:
    nxt = state.get("current_agent") or "reporter"
    allowed = {
        "planner",
        "metric",
        "log",
        "knowledge",
        "executor",
        "reporter",
    }
    return nxt if nxt in allowed else "reporter"


def build_incident_graph(
    runtime: AgentRuntime,
    *,
    checkpointer: Any | None = None,
) -> Any:
    """编译事故排查图。

    ``checkpointer`` 预留 Phase8+（Redis/Postgres）；当前默认 None。
    """
    graph = StateGraph(AgentState)

    coordinator = CoordinatorNode(runtime)
    planner = PlannerNode(runtime)
    metric = MetricAgentNode(runtime)
    log = LogAgentNode(runtime)
    knowledge = KnowledgeAgentNode(runtime)
    executor = ExecutorAgentNode(runtime)
    reporter = ReporterNode(runtime)

    graph.add_node("coordinator", coordinator)
    graph.add_node("planner", planner)
    graph.add_node("metric", metric)
    graph.add_node("log", log)
    graph.add_node("knowledge", knowledge)
    graph.add_node("executor", executor)
    graph.add_node("reporter", reporter)

    graph.add_edge(START, "coordinator")
    graph.add_conditional_edges(
        "coordinator",
        _route_from_coordinator,
        {
            "planner": "planner",
            "metric": "metric",
            "log": "log",
            "knowledge": "knowledge",
            "executor": "executor",
            "reporter": "reporter",
        },
    )
    for name in ("planner", "metric", "log", "knowledge", "executor"):
        graph.add_edge(name, "coordinator")
    graph.add_edge("reporter", END)

    return graph.compile(checkpointer=checkpointer)
