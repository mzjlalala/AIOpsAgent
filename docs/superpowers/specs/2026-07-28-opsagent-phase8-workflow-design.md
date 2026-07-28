# OpsAgent 第八阶段：Workflow（Plan-Execute / Approval）

Date: 2026-07-28

## 目标

落地外层 Plan-Execute 工作流骨架：`MemorySaver` 必选、人工审批闸门（`interrupt` + `Command(resume)`）、主路径仅经 `AgentRuntime.tools`。

## 关键决策

- 真相源：**仅 Checkpointer + WorkflowState**；本阶段无 ApprovalIndex
- `requires_approval`：**raw dict → normalize → PlanStep.model_validate**（消除显式 False vs 默认 False）
- executor 缺省字段 → `requires_approval=True`；显式 False 保留（可测跳过闸门）
- ApprovalGate：`interrupt()` **之前禁止副作用**；恢复后从节点开头重跑
- Engine.resume：**必须** `Command(resume={approved, comment})` + 同一 `thread_id`
- `get_status`：`graph.aget_state(thread_id)`；有 pending interrupt → `waiting_approval`
- Retry / Timeout / Fallback 包在 ExecuteStep 内；`StepResult.abort` 预留 Finalize 边
- 终态：`completed` / `completed_with_failures` / `failed` / `waiting_approval`
- Artifacts：现有 `AgentArtifact`（`agent_name` / `artifact_type`）+ `data.tool_result`

## interrupt 契约

```
start:
  graph.compile(checkpointer=MemorySaver())
  await graph.ainvoke(input, config={"configurable": {"thread_id": workflow_id}})

resume:
  await graph.ainvoke(
      Command(resume={"approved": bool, "comment": str|None}),
      config={"configurable": {"thread_id": workflow_id}},
  )
```

## 归一化顺序

`LoadOrInitPlan` 与 `engine.start()` 均：raw dicts → `normalize_step_approval` → `PlanStep.model_validate`。

## 明确不做

ApprovalIndex、Redis/Postgres Checkpointer、MySQL 审批落库、HTTP/SSE、嵌套 Phase7 全图

## 验收

- cpu_high → `completed`；memory_leak → 闸门 → approve/`completed` 或 reject/`completed_with_failures`
- 显式 `requires_approval=False` 的 executor 不进闸门
- Retry 一次后成功；abort Fallback → `failed`
- pytest / ruff / black / isort
