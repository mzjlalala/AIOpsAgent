"""PlanStep requires_approval 归一化（须在 model_validate 之前）。"""

from __future__ import annotations

from typing import Any

from app.agents.models import PlanStep


def normalize_step_approval(raw: dict[str, Any]) -> dict[str, Any]:
    """按 agent 补齐 requires_approval；显式值一律保留。

    必须在 ``PlanStep.model_validate`` 之前调用，否则无法区分
    「缺省 False」与「显式 False」。
    """
    agent = raw.get("agent", "")
    has_explicit = "requires_approval" in raw
    if agent == "executor" and not has_explicit:
        return {**raw, "requires_approval": True}
    if agent != "executor" and not has_explicit:
        return {**raw, "requires_approval": False}
    return dict(raw)


def normalize_plan(raw_steps: list[dict[str, Any]]) -> list[PlanStep]:
    """raw dicts → normalize → PlanStep.model_validate。"""
    return [
        PlanStep.model_validate(normalize_step_approval(dict(item)))
        for item in raw_steps
    ]
