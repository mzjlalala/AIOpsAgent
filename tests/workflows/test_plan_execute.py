"""Phase8 Plan-Execute 单测（默认无审批）。"""

from __future__ import annotations

import pytest

from app.workflows.factory import build_workflow_engine
from app.workflows.normalize import normalize_plan, normalize_step_approval
from app.workflows.policies import (
    AttemptFailed,
    FallbackPolicy,
    RetryPolicy,
    TimeoutPolicy,
    run_with_retry,
)


def test_normalize_default_no_approval() -> None:
    raw = {"step_id": "4", "agent": "executor", "goal": "演练重启"}
    out = normalize_step_approval(raw)
    assert out["requires_approval"] is False
    assert normalize_plan([raw])[0].requires_approval is False


def test_normalize_explicit_true_kept() -> None:
    raw = {
        "step_id": "4",
        "agent": "executor",
        "goal": "演练重启",
        "requires_approval": True,
    }
    assert normalize_step_approval(raw)["requires_approval"] is True


def test_normalize_non_executor_default_false() -> None:
    raw = {"step_id": "1", "agent": "metric", "goal": "查 CPU"}
    assert normalize_step_approval(raw)["requires_approval"] is False


@pytest.mark.asyncio
async def test_run_with_retry_recovers() -> None:
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise AttemptFailed("boom")
        return "ok"

    result = await run_with_retry(
        flaky,
        retry=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(seconds=5),
    )
    assert result == "ok"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_workflow_no_approval_completed() -> None:
    engine = build_workflow_engine(scenario="cpu_high", with_memory=False)
    run = await engine.start(user_query="CPU 打满")
    assert run.status == "completed"
    assert all(s["status"] == "success" for s in run.plan_steps)
    assert run.artifacts
    dump = run.artifacts[0]["data"]["tool_result"]
    assert "trace_id" in dump
    assert dump.get("success") is True


@pytest.mark.asyncio
async def test_memory_leak_completes_without_gate() -> None:
    engine = build_workflow_engine(scenario="memory_leak", with_memory=False)
    run = await engine.start(user_query="内存泄漏")
    assert run.status == "completed"
    assert all(s["status"] == "success" for s in run.plan_steps)
    assert any(s["agent"] == "executor" for s in run.plan_steps)


@pytest.mark.asyncio
async def test_explicit_approval_still_gates() -> None:
    plan = [
        {"step_id": "1", "agent": "metric", "goal": "指标"},
        {
            "step_id": "2",
            "agent": "executor",
            "goal": "重启",
            "requires_approval": True,
        },
    ]
    engine = build_workflow_engine(scenario="cpu_high", with_memory=False)
    run = await engine.start(user_query="显式审批", plan_steps=plan)
    assert run.status == "waiting_approval"
    done = await engine.resume(run.workflow_id, approved=True)
    assert done.status == "completed"


@pytest.mark.asyncio
async def test_executor_runs_without_explicit_false() -> None:
    plan = [
        {"step_id": "1", "agent": "metric", "goal": "指标"},
        {"step_id": "2", "agent": "executor", "goal": "重启"},
    ]
    engine = build_workflow_engine(scenario="cpu_high", with_memory=False)
    run = await engine.start(user_query="无审批执行", plan_steps=plan)
    assert run.status == "completed"
    assert all(s["status"] == "success" for s in run.plan_steps)


@pytest.mark.asyncio
async def test_retry_forced_failure_then_success() -> None:
    plan = [{"step_id": "1", "agent": "metric", "goal": "指标"}]
    engine = build_workflow_engine(
        scenario="cpu_high",
        with_memory=False,
        retry=RetryPolicy(max_attempts=2),
        forced_failures=1,
    )
    run = await engine.start(user_query="重试", plan_steps=plan)
    assert run.status == "completed"
    assert run.plan_steps[0]["status"] == "success"


@pytest.mark.asyncio
async def test_fallback_abort_fails_workflow() -> None:
    plan = [
        {"step_id": "1", "agent": "metric", "goal": "指标"},
        {"step_id": "2", "agent": "log", "goal": "日志"},
    ]
    engine = build_workflow_engine(
        scenario="cpu_high",
        with_memory=False,
        retry=RetryPolicy(max_attempts=1),
        fallback=FallbackPolicy(on_exhausted="abort"),
        forced_failures=1,
    )
    run = await engine.start(user_query="abort", plan_steps=plan)
    assert run.status == "failed"
    assert run.plan_steps[0]["status"] == "failed"
    assert run.plan_steps[1]["status"] == "pending"
