"""PlanStep requires_approval 归一化（须在 model_validate 之前）。"""

from __future__ import annotations

from typing import Any

from app.agents.models import PlanStep


def normalize_step_approval(raw: dict[str, Any]) -> dict[str, Any]:
    """补齐 requires_approval；当前产品默认全查询、无需审批。

    缺省 → False；仅显式 ``requires_approval=True`` 才进闸门（预留）。
    必须在 ``PlanStep.model_validate`` 之前调用。
    """
    if "requires_approval" not in raw:
        return {**raw, "requires_approval": False}
    return dict(raw)


def normalize_plan(raw_steps: list[dict[str, Any]]) -> list[PlanStep]:
    """raw dicts → normalize → PlanStep.model_validate。"""
    return [
        PlanStep.model_validate(normalize_step_approval(dict(item)))
        for item in raw_steps
    ]
