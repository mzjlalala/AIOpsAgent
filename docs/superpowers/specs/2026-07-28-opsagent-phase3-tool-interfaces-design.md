# OpsAgent 第三阶段：Tool 接口设计

Date: 2026-07-28

## 目标

落地异步优先的 Tool 抽象层：统一公开入口 `ainvoke`，子类实现 `_execute`（同步/异步双兼容），并预留可观测 Hook。

## 关键决策

- 公开入口：`await tool.ainvoke(request, context=None, runtime=None)`
- `_execute` 不定为 async；返回 `ToolOutput`
- `ToolContext` / `ToolResult` / `ToolMetadata` 不可变（frozen）
- 运行时依赖走 `RuntimeDependencies`，不进 Context
- Hooks：`before` / `on_error` / `on_result` / `after`
- 四类领域抽象 + ToolRegistry + MCPToolAdapter 接口
- 中文注释；无 Mock/生产实现

## 类型

- `JsonValue` / `ToolOutput`
- `ToolContext(frozen)`：`trace_id`、业务 ID、`tags`
- `RuntimeDependencies`：dataclass + `extensions`
- `ToolResult`：含 `trace_id` + 类型化 `metadata`

## 扩展点

- 第四阶段实现 Mock/生产 Tool
- Hook 中接入 Agent Trace / OpenTelemetry / 审计
- RuntimeDependencies 扩展 db_session、http_client 等

## 验收

- 同步/异步 `_execute` 均可被 ainvoke 调度
- Context 不可变；Result Hook 有单测
- Registry / Schema / 抽象约束测试通过
