"""LLM Function Calling 消息类型与 Mock/OpenAI 行为测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLMProvider
from app.providers.llm.types import (
    ChatMessage,
    ToolFunctionSpec,
    ToolSpec,
)


def test_tool_spec_dump_openai_shape() -> None:
    spec = ToolSpec(
        function=ToolFunctionSpec(
            name="mock_knowledge",
            description="d",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    )
    dumped = spec.model_dump()
    assert dumped["type"] == "function"
    assert dumped["function"]["name"] == "mock_knowledge"


@pytest.mark.asyncio
async def test_mock_chat_idle_no_tools() -> None:
    llm = MockLLMProvider()
    completion = await llm.acomplete_messages(
        [
            ChatMessage(role="system", content="s"),
            ChatMessage(role="user", content="我叫 maa"),
        ],
        tools=[],
    )
    assert completion.tool_calls == []


@pytest.mark.asyncio
async def test_mock_chat_cpu_calls_knowledge() -> None:
    llm = MockLLMProvider()
    completion = await llm.acomplete_messages(
        [ChatMessage(role="user", content="cpu 高怎么解决")],
        tools=[],
    )
    assert any(t.name == "mock_knowledge" for t in completion.tool_calls)


@pytest.mark.asyncio
async def test_mock_after_tool_no_more_calls() -> None:
    llm = MockLLMProvider()
    completion = await llm.acomplete_messages(
        [
            ChatMessage(role="user", content="cpu 高怎么解决"),
            ChatMessage(
                role="assistant",
                tool_calls=[],
                content=None,
            ),
            ChatMessage(
                role="tool",
                tool_call_id="call_1",
                name="mock_knowledge",
                content='{"summary":"ok"}',
            ),
        ],
        tools=[],
    )
    assert completion.tool_calls == []


@pytest.mark.asyncio
async def test_openai_messages_sends_tools() -> None:
    provider = OpenAICompatibleLLMProvider(
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        model_name="deepseek-v4-pro",
    )
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "mock_knowledge",
                                "arguments": '{"query":"cpu","top_k":3}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=fake_response)

    tools = [
        ToolSpec(
            function=ToolFunctionSpec(
                name="mock_knowledge",
                description="kb",
                parameters={"type": "object", "properties": {}},
            )
        )
    ]
    target = "app.providers.llm.openai_compatible.httpx.AsyncClient"
    with patch(target, return_value=mock_client):
        completion = await provider.acomplete_messages(
            [ChatMessage(role="user", content="cpu")],
            tools=tools,
        )
    assert completion.tool_calls[0].name == "mock_knowledge"
    assert completion.tool_calls[0].arguments["query"] == "cpu"
    payload = mock_client.post.await_args.kwargs["json"]
    assert payload["tools"][0]["function"]["name"] == "mock_knowledge"
