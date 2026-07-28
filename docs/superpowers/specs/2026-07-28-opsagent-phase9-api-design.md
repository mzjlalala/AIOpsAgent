# OpsAgent 第九阶段：API（Incident / Approval / SSE）

Date: 2026-07-28

## 目标

落地 HTTP 骨架：`POST /incident` 启动即 SSE，审批 `Command(resume)`，状态查询与事件续订；主路径仅 Phase8 Workflow。

## 关键决策

- 骨架优先；挂载进程内 `WorkflowEngine` + 共享 `MemorySaver`
- `POST /incident` 返回 `text/event-stream`（`astream` / `stream_mode=updates`）
- 审批：`POST /workflows/{id}/approve` → JSON `WorkflowRun`
- `GET /workflows/{id}/events`：状态快照；仍 interrupted 则 `waiting_approval`；终态则 `completed`
- 不同 `scenario` 请求可重建 engine，但必须共享同一 checkpointer
- 不做：`/chat`、history、tools、RAG、metrics、replay、鉴权、MySQL/Redis、Phase7 HTTP、ApprovalIndex

## 端点

| 方法 | 路径 | 行为 |
|------|------|------|
| POST | `/incident` | `{query, scenario?}` → SSE |
| POST | `/workflows/{id}/approve` | `{approved, comment?}` → JSON |
| GET | `/workflows/{id}` | 状态 JSON |
| GET | `/workflows/{id}/events` | 续订 / 快照 SSE |
| GET | `/health` | 不变 |

## SSE 信封

`{workflow_id, type, node, step_id?, agent?, message, payload}`

类型：`step_started` / `step_succeeded` / `step_failed` / `waiting_approval` / `completed` / `error` / `snapshot`

## 错误

- 未知 id → 404（含进程重启后 MemorySaver 丢失）
- 非 waiting_approval 时 approve → 409
- 校验失败 → 422
- 执行异常：SSE `error`；JSON `500`

## 验收

- cpu_high SSE → completed（含 Planning / Metrics）
- memory_leak → waiting_approval → approve/reject
- 404 / 409；pytest / ruff / black / isort
