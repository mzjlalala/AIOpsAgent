"""事故排查 Multi-Agent 图单测。"""

from __future__ import annotations

import pytest

from app.agents.factory import build_default_incident_app
from app.agents.json_parse import AgentJsonParseError, parse_json_payload
from app.agents.models import AgentArtifact, PlanStep
from app.agents.runtime import AgentConfig
from app.providers.llm import MockLLMProvider


def test_parse_json_payload_fence_and_raw() -> None:
    assert parse_json_payload('["a", "b"]') == ["a", "b"]
    assert parse_json_payload('```json\n["x"]\n```') == ["x"]
    with pytest.raises(AgentJsonParseError):
        parse_json_payload("not-json")


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["cpu_high", "memory_leak"])
async def test_mock_llm_scenario_plan(scenario: str) -> None:
    llm = MockLLMProvider(scenario=scenario)
    text = await llm.acomplete(
        system="sys",
        prompt="请规划 plan steps",
    )
    assert isinstance(text, str)
    steps = parse_json_payload(text)
    print(steps)
    assert isinstance(steps, list)
    validated = [PlanStep.model_validate(s) for s in steps]
    assert validated
    assert validated[0].status == "pending"


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["cpu_high", "memory_leak"])
async def test_incident_graph_scenarios(scenario: str) -> None:
    query = (
        "线上服务 CPU 突然打满 100%"
        if scenario == "cpu_high"
        else "服务内存持续上涨疑似泄漏"
    )
    _runtime, app = build_default_incident_app(
        with_memory=True,
        with_rag=False,
        scenario=scenario,
        config=AgentConfig(max_steps=12, mock_llm_scenario=scenario),
    )
    final = await app.ainvoke(
        {
            "trace_id": f"t-{scenario}",
            "user_query": query,
            "conversation_id": "c1",
            "session_id": "s1",
            "plan_steps": [],
            "visited_agents": [],
            "step_count": 0,
            "artifacts": [],
            "messages": [],
        }
    )
    assert final.get("report")
    assert "metric_result" not in final
    artifacts = [
        AgentArtifact.from_state_dict(a) for a in (final.get("artifacts") or [])
    ]
    agent_names = {a.agent_name for a in artifacts}
    assert "planner" in agent_names
    assert agent_names & {"metric", "log", "knowledge"}
    tool_arts = [a for a in artifacts if a.artifact_type == "tool_result"]
    assert tool_arts
    # 完整 ToolResult 链路
    dump = tool_arts[0].data.get("tool_result") or {}
    assert "trace_id" in dump
    assert "success" in dump
    assert "metadata" in dump
    assert dump.get("success") is True


@pytest.mark.asyncio
async def test_max_steps_forces_reporter() -> None:
    _runtime, app = build_default_incident_app(
        with_memory=False,
        scenario="cpu_high",
        config=AgentConfig(max_steps=1),
    )
    final = await app.ainvoke(
        {
            "trace_id": "t-max",
            "user_query": "CPU 打满",
            "plan_steps": [],
            "visited_agents": [],
            "step_count": 0,
            "artifacts": [],
        }
    )
    print( final)
    assert final.get("report")
    assert final.get("step_count", 0) >= 1
