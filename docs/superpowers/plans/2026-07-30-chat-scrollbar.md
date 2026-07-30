# Chat Scrollbar Styling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为聊天消息区与侧边栏会话列表添加细条半透明、悬停更明显的自定义滚动条样式。

**Architecture:** 仅改 `web/src/styles.css`：在 `:root` 增加滚动条变量，用并列选择器 `.main__body, .sidebar__list` 挂载 WebKit 伪元素 + Firefox `scrollbar-*`，不改 Vue 模板。

**Tech Stack:** CSS（WebKit scrollbar 伪元素、Firefox scrollbar-width/color）、Vue Web Console 现有深色主题变量。

## Global Constraints

- 宽度 6px；轨道透明；滑块默认 `rgba(255,255,255,0.2)`；悬停 `rgba(255,255,255,0.4)`
- 作用域仅 `.main__body` 与 `.sidebar__list`
- 不引入第三方库；不改滚动行为；不强制改代码块横向滚动条
- 优先 CSS 选择器，少动 Vue 模板

---

### Task 1: 添加滚动条 CSS 与回归断言

**Files:**
- Modify: `web/src/styles.css`
- Create: `web/tests/scrollbar-style.test.ts`

**Interfaces:**
- Consumes: 现有 `.main__body`、`.sidebar__list` 选择器
- Produces: `:root` 变量 `--scrollbar-size` / `--scrollbar-thumb` / `--scrollbar-thumb-hover`；两处滚动容器的自定义滚动条规则

- [x] **Step 1: Write the failing test**

在 `web/tests/scrollbar-style.test.ts` 写入：

```typescript
import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../src/styles.css"),
  "utf8",
);

test("styles.css defines scrollbar CSS variables", () => {
  assert.match(css, /--scrollbar-size:\s*6px/);
  assert.match(css, /--scrollbar-thumb:\s*rgba\(255,\s*255,\s*255,\s*0\.2\)/);
  assert.match(css, /--scrollbar-thumb-hover:\s*rgba\(255,\s*255,\s*255,\s*0\.4\)/);
});

test("styles.css styles main__body and sidebar__list scrollbars", () => {
  assert.match(css, /\.main__body\s*,\s*\.sidebar__list/);
  assert.match(css, /scrollbar-width:\s*thin/);
  assert.match(css, /scrollbar-color:\s*var\(--scrollbar-thumb\)\s+transparent/);
  assert.match(css, /::-webkit-scrollbar/);
  assert.match(css, /::-webkit-scrollbar-track/);
  assert.match(css, /::-webkit-scrollbar-thumb/);
  assert.match(css, /::-webkit-scrollbar-thumb:hover/);
});
```

- [x] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test tests/scrollbar-style.test.ts`  
Working directory: `web/`  
Expected: FAIL（变量或选择器尚未存在）

- [x] **Step 3: Write minimal implementation**

在 `web/src/styles.css` 的 `:root` 中追加：

```css
--scrollbar-size: 6px;
--scrollbar-thumb: rgba(255, 255, 255, 0.2);
--scrollbar-thumb-hover: rgba(255, 255, 255, 0.4);
```

在全局 `box-sizing` 规则之后（或 `.main__body` 定义附近）增加：

```css
.main__body,
.sidebar__list {
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) transparent;
}

.main__body::-webkit-scrollbar,
.sidebar__list::-webkit-scrollbar {
  width: var(--scrollbar-size);
  height: var(--scrollbar-size);
}

.main__body::-webkit-scrollbar-track,
.sidebar__list::-webkit-scrollbar-track {
  background: transparent;
}

.main__body::-webkit-scrollbar-thumb,
.sidebar__list::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 999px;
}

.main__body::-webkit-scrollbar-thumb:hover,
.sidebar__list::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test tests/scrollbar-style.test.ts`  
Expected: PASS（2/2）

另跑：`npm run build`（working directory `web/`）Expected: exit 0

- [x] **Step 5: Commit**

```bash
git add web/src/styles.css web/tests/scrollbar-style.test.ts
git commit -m "style(web): thin translucent scrollbars for chat and sidebar"
```
