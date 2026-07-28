"""chat_tools 调度测试。"""

from __future__ import annotations

import re

import pytest

from app.providers.llm.types import ToolCall
from app.services.chat_tools import (
    CHAT_TOOL_NAMES,
    build_chat_tool_specs,
    dispatch_chat_tool,
)
from app.tools.factory import build_mock_registry


def test_build_chat_tool_specs_whitelist() -> None:
    specs = build_chat_tool_specs()
    names = {s.function.name for s in specs}
    assert names == set(CHAT_TOOL_NAMES)
    assert "mock.executor" not in names


def test_build_chat_tool_specs_use_api_safe_names() -> None:
    for spec in build_chat_tool_specs():
        assert re.fullmatch(r"[a-zA-Z0-9_-]+", spec.function.name)


@pytest.mark.asyncio
async def test_dispatch_knowledge() -> None:
    registry = build_mock_registry()
    summary, data = await dispatch_chat_tool(
        registry,
        ToolCall(
            id="c1",
            name="mock_knowledge",
            arguments={"query": "CPU", "top_k": 2},
        ),
    )
    assert summary
    assert data.get("success") is True


@pytest.mark.asyncio
async def test_dispatch_unknown_tool() -> None:
    registry = build_mock_registry()
    summary, data = await dispatch_chat_tool(
        registry,
        ToolCall(id="c2", name="mock.executor", arguments={}),
    )
    assert "未授权" in summary or "未知" in summary
    assert data == {}
