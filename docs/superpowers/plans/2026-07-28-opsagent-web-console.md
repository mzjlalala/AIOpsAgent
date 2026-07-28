# OpsAgent 演示前端（Vue3 单页）Implementation Plan

> **For agentic workers:** 按任务顺序实现；每步可独立验收。

**Goal:** 独立 `web/` 演示控制台：Incident SSE + 审批，Vite proxy 联调后端。

**Architecture:** Vue 3 + Vite + TS 单页；fetch 解析 SSE；不挂 FastAPI 静态。

**Tech Stack:** Vue 3、Vite、TypeScript、原生 fetch

## Global Constraints

- 目录：`web/`（仓库根下）
- Proxy：`/incident`、`/workflows`、`/health` → `http://127.0.0.1:8000`
- 无登录、无路由、无暗色切换
- 视觉：冷灰蓝 + 青绿/琥珀；IBM Plex Sans + Noto Sans SC
- 设计文档：`docs/superpowers/specs/2026-07-28-opsagent-web-console-design.md`

---

## 目标结构

```
web/
  package.json
  vite.config.ts
  index.html
  src/main.ts
  src/App.vue
  src/styles.css
  src/api/client.ts
  src/components/BrandHeader.vue
  src/components/IncidentForm.vue
  src/components/StatusBar.vue
  src/components/EventTimeline.vue
  src/components/ApprovalPanel.vue
```

## Task 1：Scaffold + proxy

- [ ] `npm create vite@latest web -- --template vue-ts`（或等价手写）
- [ ] `vite.config.ts` 配置 server.proxy
- [ ] 确认 `npm install && npm run dev` 能开空白页

## Task 2：API client

- [ ] `streamIncident(query, scenario)` 解析 SSE → 回调事件
- [ ] `getWorkflow(id)` / `approveWorkflow(id, {approved, comment})`
- [ ] 类型与后端 `SseEvent` / `WorkflowRunResponse` 对齐

## Task 3：UI 组件 + App

- [ ] 五块组件 + App 状态机（idle → running → waiting_approval → terminal）
- [ ] `styles.css` 设计 token / 网格 / 动效
- [ ] cpu_high / memory_leak 手动联调通过

## Task 4：README

- [ ] 根 README 增加前端两终端启动说明
- [ ] 冒烟：health + 一页可点

## 验收

- cpu_high 跑完无闸门；memory_leak 可审批
- 不改后端业务（仅文档）
