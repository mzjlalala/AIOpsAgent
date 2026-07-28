"""Mock Tool 注册工厂。"""

from __future__ import annotations

from app.tools.executor.mock import MockExecutorTool
from app.tools.knowledge.mock import MockKnowledgeTool
from app.tools.log.mock import MockLogTool
from app.tools.metric.mock import MockMetricTool
from app.tools.registry import ToolRegistry


def build_mock_registry() -> ToolRegistry:
    """创建并注册全部 Mock Tool，供测试与后续 Agent 显式使用。

    注意：不会自动挂载到 FastAPI ``create_app``。
    """
    registry = ToolRegistry()
    for tool in (
        MockMetricTool(),
        MockLogTool(),
        MockExecutorTool(),
        MockKnowledgeTool(),
    ):
        registry.register(tool)
    return registry
