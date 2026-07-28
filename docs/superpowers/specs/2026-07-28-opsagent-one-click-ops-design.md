# OpsAgent 一键运维（自主规划 · Mock）

Date: 2026-07-28

## 目标

前端「一键运维」触发 Agent 自主巡检（指标 → 日志 → RAG → 可选审批执行），用户无需填写事故描述。数据源本阶段仍为 Mock Tools。

## 锁定决策

- 方案 A：`POST /ops/one-click` → 复用 WorkflowEngine + SSE
- 固定 `user_query` 巡检目标；默认 scenario=`auto_ops`
- MockLLM `auto_ops`：metric → log → knowledge → executor（需审批）
- `/incident` 保留；前端主 CTA 改为一键，高级区可自定义

## 明确不做

真实 Prometheus/ES/Milvus/Redis、删除 `/incident`、Docker

## 验收

一键出 SSE；含 Planning/Metrics/Logs/Knowledge/Waiting Approval；审批通过/拒绝终态正确
