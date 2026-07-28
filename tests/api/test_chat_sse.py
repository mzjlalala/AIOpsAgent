"""POST /chat SSE 测试。"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    blocks = body.strip().split("\n\n")
    for block in blocks:
        if not block.strip():
            continue
        event_type = None
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
        if not data_lines:
            continue
        payload = json.loads("\n".join(data_lines))
        if event_type and payload.get("type") != event_type:
            payload["type"] = event_type
        events.append(payload)
    return events


def test_chat_idle_no_tools(client: TestClient) -> None:
    response = client.post("/chat", json={"message": "我叫 maa"})
    assert response.status_code == 200
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "session" in types
    assert "answer" in types
    assert "tool_call" not in types
    assert "step_started" not in types


def test_chat_cpu_uses_knowledge(client: TestClient) -> None:
    response = client.post("/chat", json={"message": "cpu 高怎么解决"})
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert any(
        e.get("payload", {}).get("tool") == "mock.knowledge"
        for e in events
        if e["type"] == "tool_call"
    )
    assert types[-1] == "answer"
    assert events[-1]["message"]


def test_chat_multi_turn_memory(client: TestClient) -> None:
    first = client.post("/chat", json={"message": "我叫 maa"})
    cid = next(
        e["payload"]["conversation_id"]
        for e in _parse_sse(first.text)
        if e["type"] == "session"
    )
    second = client.post(
        "/chat",
        json={"message": "我刚才说我叫什么", "conversation_id": cid},
    )
    answer = next(e["message"] for e in _parse_sse(second.text) if e["type"] == "answer")
    assert "maa" in answer.lower()


def test_chat_validation_empty(client: TestClient) -> None:
    assert client.post("/chat", json={"message": ""}).status_code == 422
