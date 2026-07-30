# 聊天滚动条样式优化设计

日期：2026-07-30  
范围：前端 Web Console 滚动条视觉优化

## 目标

将聊天消息区与侧边栏会话列表的系统默认滚动条，改为细条、半透明、悬停更明显的样式，贴近 ChatGPT 类深色对话界面，降低视觉干扰。

## 非目标

- 不引入第三方滚动条库或自定义 DOM 滚动条组件
- 不改滚动行为（自动滚到底、触控、键盘滚动等）
- 不改代码块区域（`.md-body pre`）的横向滚动条为全局统一（可自然继承或保持默认，本需求不强制）
- 不做「完全隐藏、仅滚动时闪现」的 JS 交互

## 方案

在 `web/src/styles.css` 增加可复用滚动条样式，并挂到：

- `.main__body`（聊天上下滚动）
- `.sidebar__list`（侧边栏会话列表）

### 视觉规范

| 项 | 规范 |
|---|---|
| 宽度 / 高度 | 6px（细条） |
| 轨道 | 透明 |
| 滑块默认 | `rgba(255, 255, 255, 0.2)`，圆角满圆 |
| 滑块悬停 / 拖拽 | `rgba(255, 255, 255, 0.4)` |
| 边框 | 无（或 透明边框避免方块感） |

### 兼容实现

1. **Chromium / Safari**：`::-webkit-scrollbar`、`::-webkit-scrollbar-track`、`::-webkit-scrollbar-thumb`（及 `:hover`）
2. **Firefox**：`scrollbar-width: thin` + `scrollbar-color: <thumb> transparent`

可用 CSS 变量集中颜色（例如 `--scrollbar-thumb` / `--scrollbar-thumb-hover`），便于与现有 `--bg` / `--line` 体系共存。

### 结构建议

```css
:root {
  --scrollbar-size: 6px;
  --scrollbar-thumb: rgba(255, 255, 255, 0.2);
  --scrollbar-thumb-hover: rgba(255, 255, 255, 0.4);
}

.scrollable {
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) transparent;
}

.scrollable::-webkit-scrollbar { width: var(--scrollbar-size); height: var(--scrollbar-size); }
.scrollable::-webkit-scrollbar-track { background: transparent; }
.scrollable::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 999px;
}
.scrollable::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}

.main__body,
.sidebar__list {
  /* 应用 .scrollable 规则：直接复用选择器或并列挂载 */
}
```

实现时可直接写 `.main__body, .sidebar__list` 选择器，或抽 `.scrollable` 再给两处加 class；优先改 CSS 选择器、少动 Vue 模板。

## 验收

1. 聊天消息超出视口时，右侧出现细半透明滑块，轨道不明显
2. 鼠标悬停滑块时对比度提高
3. 侧边栏会话列表过长时样式一致
4. Firefox 与 Chromium 均可用（Firefox 为 thin + 双色近似效果，不必像素级一致）
5. 现有深色主题与布局无回归

## 风险与约束

- Firefox 不支持 WebKit 伪元素，只能近似「细 + 半透明」
- Windows 高对比度 / 强制颜色模式下浏览器可能覆盖自定义滚动条，可接受
