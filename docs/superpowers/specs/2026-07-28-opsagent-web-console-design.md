# OpsAgent 演示前端（Vue3 单页控制台）

Date: 2026-07-28

## 目标

独立 `web/`（Vite + Vue 3 + TS）最小演示页：发起 `/incident` SSE、展示事件流、在闸门处审批。

## 锁定决策

- Vue 3 + Vite + TypeScript；仓库根目录 `web/`
- 单页控制台（无路由、无登录）
- 开发期 Vite proxy → `http://127.0.0.1:8000`（`/incident`、`/workflows`、`/health`）
- 不挂载 FastAPI 静态资源（Docker 阶段再考虑）

## 一屏结构

1. 品牌条：OpsAgent + 副标
2. 发起区：query、scenario（cpu_high / memory_leak）、开始排查
3. 状态条：workflow_id、status
4. 事件流：SSE 时间线
5. 审批条：仅 `waiting_approval` 时显示（通过/拒绝 + 备注）

## 视觉

- 冷灰蓝浅色底 + 淡网格；强调色青绿 / 琥珀
- 字体：IBM Plex Sans + Noto Sans SC
- 事件淡入；待审批轻微脉冲；避免紫/奶油陶土/霓虹 glow

## 明确不做

登录、多页路由、历史列表、暗色切换、图表大屏、移动端专项

## 验收

- `npm install && npm run dev` 可开
- cpu_high 跑完；memory_leak 可审批
- 根 README 补充前端启动说明
