"""ToolRegistry 单测。"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.tools.base import BaseTool
from app.tools.context import ToolContext
from app.tools.exceptions import ToolAlreadyRegisteredError, ToolNotFoundError
from app.tools.registry import ToolRegistry
from app.tools.runtime import RuntimeDependencies
from app.tools.types import ToolCategory, ToolOutput


class _DummyRequest(BaseModel):
    pass


class _DummyTool(BaseTool):
    name = "dummy"
    description = "dummy tool"
    category = ToolCategory.METRIC

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        return {"ok": True}


def test_registry_register_get_list_unregister() -> None:
    registry = ToolRegistry()
    tool = _DummyTool()
    registry.register(tool)

    assert "dummy" in registry
    assert len(registry) == 1
    assert registry.get("dummy") is tool
    assert registry.list(category=ToolCategory.METRIC) == [tool]
    assert registry.list(category=ToolCategory.LOG) == []

    registry.unregister("dummy")
    assert len(registry) == 0


def test_registry_duplicate_and_missing() -> None:
    registry = ToolRegistry()
    registry.register(_DummyTool())
    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register(_DummyTool())
    with pytest.raises(ToolNotFoundError):
        registry.get("missing")
