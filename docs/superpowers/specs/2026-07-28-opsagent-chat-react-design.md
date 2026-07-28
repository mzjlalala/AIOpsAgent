# OpsAgent 普通聊天（ReAct + 可选工具）

Date: 2026-07-28

## 目标

输入框普通消息走 **多轮对话**，由 LLM 流式回复；需要时 Agent 以 **ReAct** 调用指标 / 日志 / 知识库工具。闲聊（如「我叫 maa」）不得启动 Plan-Execute 工作流，也不应出现「制定排查思路」类进度链。

「一键运维」仍走现有 `POST /ops/one-click` Workflow。

## 锁定决策

- 方案：**Prompt-based ReAct**（LLM 输出 JSON 动作；服务端解析并 `ainvoke` Mock 工具），不引入 OpenAI 原生 `tool_calls` API（本阶段）
- 新接口：`POST /chat` → `text/event-stream`
- 请求体：`{ "message": string, "conversation_id"?: string }`
- 多轮：服务端 `MemoryManager`（InMemory）按 `conversation_id` 存 user/assistant 轮次；缺省则新建 UUID 并在首帧/首事件中回传
- 工具白名单：仅 `mock.knowledge`、`mock.metric`、`mock.log`；**不含** `mock.executor`
- 循环上限：最多 **3** 轮工具调用；超出后强制进入最终回答
- 决策轮用 `acomplete`（解析 JSON）；最终回答用 `astream` → `answer_delta` + `answer`
- 前端：普通发送 → `streamChat`；一键运维不变；`tool_call`/`tool_result` 显示为轻量「查阅中」气泡（非工作流步骤文案）

## ReAct 协议（LLM 输出）

系统提示声明可用工具与输出格式。每轮模型只能输出下列之一（纯 JSON，不要 Markdown 包裹）：

```json
{"action":"tool","tool":"mock.knowledge","args":{"query":"...","top_k":3}}
```

```json
{"action":"final","content":"（可省略；若走流式最终答则本轮可不返回 content）"}
```

当 `action` 为 `final`（或非 JSON / 无法解析为 tool）时，进入最终回答阶段：用对话历史 + 工具观察再 `astream` 生成面向用户的 Markdown 回复。

### 工具 args 约定

| tool | args（最小集） | 映射 |
|------|----------------|------|
| `mock.knowledge` | `query`, `top_k?` | `KnowledgeSearchQuery` |
| `mock.metric` | `query`（或 `service`/`metric_name` 文本） | `MetricInstantQuery`（缺省合理默认） |
| `mock.log` | `query`, `service?` | `LogSearchQuery` |

未知 tool 名 → SSE `error` 或跳过并写入 observation「未知工具」，计入一轮。

## SSE 事件

复用 `SseEvent` 信封；`workflow_id` 字段本接口填 `conversation_id`（避免新 envelope）。

| type | 含义 |
|------|------|
| `session` | 新建/确认会话：`message` 可空，`payload.conversation_id` |
| `tool_call` | 即将调用工具：`message` 简述，`payload.tool` / `args` |
| `tool_result` | 工具结果摘要：`message` 一行摘要，`payload` 含精简 data |
| `answer_delta` | 最终回答增量 |
| `answer` | 最终回答全文 |
| `error` | 失败 |

不推送 `step_started` / Plan-Execute 相关事件。

## 组件

| 组件 | 职责 |
|------|------|
| `app/schemas/chat.py` | `ChatRequest` |
| `app/services/chat.py` | `ChatService.stream_chat`：记忆 → ReAct 循环 → 流式终答 |
| `app/api/chat.py` | `POST /chat` StreamingResponse |
| `app/main.py` | 注入 `ChatService`（LLM + ToolRegistry + MemoryManager） |
| `web` | `streamChat`、proxy `/chat`、App 普通发送改走 chat |

LLM / Tool 接口不强制改原生 tools API；可在 `ChatService` 内用现有 `acomplete`/`astream` + `ToolRegistry.get(...).ainvoke`。

## 数据流

```
用户 message
  → Memory.append(user)
  → loop ≤3:
       LLM.acomplete(system+history+observations)
       → tool? → SSE tool_call → ainvoke → SSE tool_result → append observation
       → final? → break
  → LLM.astream(… + observations) → answer_delta* → answer
  → Memory.append(assistant)
```

## 错误处理

- LLM / 工具异常：SSE `error`，不中断已推送的 delta（若已有）
- 客户端 Abort：与现有 SSE 一致，生成器停止即可
- 空 `message`：HTTP 422

## 明确不做

- 原生 OpenAI `tools` / `tool_calls` API
- 聊天路径调用 `mock.executor` 或任意变更执行
- 把普通聊天路由到 `POST /incident` / Workflow
- 持久化 DB history、鉴权、多用户隔离
- 修改一键运维 / Plan-Execute 主路径行为（除文档说明分流）

## 验收

1. 「我叫 maa」→ 仅有流式 `answer*`（可有 `session`），**无** tool / 排查步骤文案  
2. 「cpu 高怎么解决」→ 可出现 `tool_call`（至少 knowledge）+ 流式 Markdown 结论  
3. 同一 `conversation_id` 第二轮能引用上文（如「我刚才说我叫什么」）  
4. 前端普通输入走 `/chat`；一键运维仍走 `/ops/one-click`  
5. `pytest` 覆盖 chat SSE（MockLLM 可按 prompt 返回固定 tool/final JSON）
