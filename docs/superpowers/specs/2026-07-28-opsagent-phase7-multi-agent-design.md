# OpsAgent 第七阶段：LangGraph Multi-Agent

Date: 2026-07-28

## 目标

落地 LangGraph 1.x 事故排查 Multi-Agent 骨架，并预留 Phase8 Workflow / Phase9 SSE 扩展点。

## 关键决策

- State：固定字段 + `artifacts` / `plan_steps`（序列化 dict）；禁止无限 `*_result`
- `AgentArtifact` / `PlanStep` Pydantic 模型（`app/agents/models.py`）
- Coordinator：`RouteStrategy` + `RuleBasedRouter`（代码路由）
- Planner：LLM `str` + `parse_json_payload` → `PlanStep[]`
- 专家节点：完整 `ToolResult` 写入 artifact.data.tool_result
- `AgentRuntime.event_bus`（默认 Noop）；`build_incident_graph(checkpointer=...)`
- `MockLLMProvider(scenario=...)`：`cpu_high` / `memory_leak`
- 依赖：`langgraph>=1.2.0,<1.3.0`；`langchain-core>=1.4.7,<2.0.0`
- API：仅 `StateGraph` / `START` / `END` / `conditional_edges`

## 明确不做

真实 LLM、Human Approval、Reflection 实现、SSE/HTTP、Checkpoint 存储实现

## 验收

- 场景参数化单测；ToolResult 链路字段齐全；max_steps 收束
- pytest / ruff / black / isort
