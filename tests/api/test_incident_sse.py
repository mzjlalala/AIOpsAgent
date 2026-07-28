"""Phase9 Incident / Approval / SSE API 测试。"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.services.sse_map import map_update_to_events


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


def test_map_update_planning() -> None:
    events = map_update_to_events(
        {"load_or_init_plan": {"plan_steps": [{}, {}], "status": "running"}},
        workflow_id="w1",
    )
    assert len(events) == 1
    assert events[0].type == "step_started"
    assert events[0].message == "Planning..."


def test_map_update_interrupt() -> None:
    class _I:
        value = {"step_id": "4", "agent": "executor", "action": "approve_step"}

    events = map_update_to_events(
        {"__interrupt__": (_I(),)},
        workflow_id="w1",
    )
    assert events[0].type == "waiting_approval"
    assert events[0].agent == "executor"


def test_incident_cpu_high_sse_completed(client: TestClient) -> None:
    response = client.post(
        "/incident",
        json={"query": "CPU 打满", "scenario": "cpu_high"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    messages = [e.get("message", "") for e in events]
    assert "step_started" in types
    assert any("Planning" in m for m in messages)
    assert any("Query Metrics" in m for m in messages)
    assert "waiting_approval" not in types
    assert types[-1] == "completed"
    assert events[-1]["payload"].get("status") == "completed"
    wid = events[0]["workflow_id"]
    status = client.get(f"/workflows/{wid}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"


def test_incident_memory_leak_completes(client: TestClient) -> None:
    response = client.post(
        "/incident",
        json={"query": "内存泄漏", "scenario": "memory_leak"},
    )
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "waiting_approval" not in types
    assert types[-1] == "completed"
    wid = events[0]["workflow_id"]
    status = client.get(f"/workflows/{wid}")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    ev = client.get(f"/workflows/{wid}/events")
    assert ev.status_code == 200
    assert any(e["type"] == "completed" for e in _parse_sse(ev.text))


def test_workflow_not_found(client: TestClient) -> None:
    assert client.get("/workflows/missing-id").status_code == 404
    assert client.get("/workflows/missing-id/events").status_code == 404
    assert (
        client.post(
            "/workflows/missing-id/approve",
            json={"approved": True},
        ).status_code
        == 404
    )


def test_approve_conflict_when_not_waiting(client: TestClient) -> None:
    response = client.post(
        "/incident",
        json={"query": "CPU", "scenario": "cpu_high"},
    )
    wid = _parse_sse(response.text)[0]["workflow_id"]
    conflict = client.post(
        f"/workflows/{wid}/approve",
        json={"approved": True},
    )
    assert conflict.status_code == 409


def test_incident_validation_error(client: TestClient) -> None:
    response = client.post("/incident", json={"query": ""})
    assert response.status_code == 422


def test_one_click_ops_completes(client: TestClient) -> None:
    response = client.post("/ops/one-click", json={})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    messages = [e.get("message", "") for e in events]
    assert any("Planning" in m for m in messages)
    assert any("Query Metrics" in m for m in messages)
    assert any("Searching Logs" in m for m in messages)
    assert any("Searching Knowledge" in m for m in messages)
    assert "waiting_approval" not in types
    assert types[-1] == "completed"
    assert events[-1]["payload"].get("status") == "completed"
