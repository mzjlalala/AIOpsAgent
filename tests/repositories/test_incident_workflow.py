"""事故与工作流 Repository CRUD 冒烟测试。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.trace import AgentTrace, ToolCall, ToolResult
from app.models.workflow import Approval, Workflow
from app.repositories.incident import IncidentRepository
from app.repositories.trace import (
    AgentTraceRepository,
    ToolCallRepository,
    ToolResultRepository,
)
from app.repositories.workflow import ApprovalRepository, WorkflowRepository


async def test_incident_workflow_trace_crud(db_session: AsyncSession) -> None:
    """创建 事故 → 工作流 → Trace → 工具调用/结果 → 审批。"""
    incidents = IncidentRepository(db_session)
    workflows = WorkflowRepository(db_session)
    traces = AgentTraceRepository(db_session)
    tool_calls = ToolCallRepository(db_session)
    tool_results = ToolResultRepository(db_session)
    approvals = ApprovalRepository(db_session)

    incident = await incidents.add(
        Incident(
            title="API latency high",
            severity="high",
            status="open",
            source="prometheus",
        )
    )
    workflow = await workflows.add(
        Workflow(
            incident_id=incident.id,
            plan_json=["query_metrics", "query_logs", "analyze"],
            status="running",
        )
    )
    assert (await workflows.list_by_incident(incident.id))[0].id == workflow.id

    trace = await traces.add(
        AgentTrace(
            workflow_id=workflow.id,
            node_name="metric_agent",
            agent_name="MetricAgent",
            status="completed",
            latency_ms=12.5,
            token_usage=100,
        )
    )
    call = await tool_calls.add(
        ToolCall(
            trace_id=trace.id,
            tool_name="prometheus.query",
            input_json={"query": "cpu"},
            status="success",
        )
    )
    await tool_results.add(
        ToolResult(
            tool_call_id=call.id,
            output_json={"value": 99.9},
            latency_ms=3.2,
        )
    )
    approval = await approvals.add(
        Approval(
            incident_id=incident.id,
            workflow_id=workflow.id,
            action="restart_pod",
            status="pending",
        )
    )

    pending = await approvals.list_pending_by_incident(incident.id)
    assert len(pending) == 1
    assert pending[0].id == approval.id
    assert len(await traces.list_by_workflow(workflow.id)) == 1
