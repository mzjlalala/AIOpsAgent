# OpsAgent 普通聊天（Function Calling + 可选工具）

Date: 2026-07-28

## 目标

输入框普通消息走 **多轮对话**，由 LLM 流式回复；需要时 Agent 通过 **OpenAI 兼容 Function Calling** 调用指标 / 日志 / 知识库工具。闲聊（如「我叫 maa」）不得启动 Plan-Execute 工作流，也不应出现「制定排查思路」类进度链。

「一键运维」仍走现有 `POST /ops/one-click` Workflow。

## 锁定决策

- 方案：**原生 Function Calling**（`tools` + `tool_calls` / `role=tool` messages），**不做** Prompt-based JSON ReAct
- 循环形态仍是「观察 → 决策 → 行动」的 Agent 环，但动作边界由 API `tool_calls` 表达
- 新接口：`POST /chat` → `text/event-stream`
- 请求体：`{ "message": string, "conversation_id"?: string }`
- 多轮：服务端 `MemoryManager`（InMemory）按 `conversation_id` 存 user/assistant 轮次；缺省则新建 UUID，经 `session` 事件回传
- 工具白名单：仅 `mock.knowledge`、`mock.metric`、`mock.log`；**不含** `mock.executor`
- 循环上限：最多 **3** 轮带 `tool_calls` 的决策；超出后强制无 tools 的最终流式回答
- 决策轮：`acomplete_messages`（非流式，拿完整 `tool_calls`）；终答轮：`astream_messages`（无 tools 或 `tool_choice=none`）→ `answer_delta` + `answer`
- 前端：普通发送 → `streamChat`；一键运维不变；`tool_call`/`tool_result` 显示为轻量「查阅中」气泡

## Function Calling 协议

### LLM Provider 扩展

在现有 `acomplete` / `astream`（纯文本，供 Workflow 等沿用）之外新增：

| 类型 / 方法 | 说明 |
|-------------|------|
| `ChatMessage` | `role`: `system` \| `user` \| `assistant` \| `tool`；可选 `content`、`tool_calls`、`tool_call_id`、`name` |
| `ToolSpec` | OpenAI tools 项：`type=function` + `function.{name,description,parameters}` |
| `LLMCompletion` | `content: str \| None` + `tool_calls: list[ToolCall]` |
| `ToolCall` | `id`, `name`, `arguments`（JSON object 或已解析 dict） |
| `acomplete_messages(messages, tools=None, tool_choice="auto")` | 非流式多轮补全 |
| `astream_messages(messages, tools=None)` | 流式文本（本阶段终答可不解析流式 tool_calls） |

`OpenAICompatibleLLMProvider`：请求体带 `messages` + 可选 `tools`；解析 `choices[0].message.tool_calls`。

`MockLLMProvider`：按最近 user 文本启发式返回：
- 闲聊 → 无 `tool_calls`，`content` 可空（由终答轮再生成）或直接短回复策略见下
- 含 CPU/指标/日志/知识等关键词 → 返回对应 `tool_calls`（固定 id/args）
- 已有 `role=tool` 观察后 → 无 `tool_calls`，进入终答

### 工具 Schema（挂到 `tools`）

函数名与注册表一致：

| name | parameters（JSON Schema 要点） | 映射到 |
|------|-------------------------------|--------|
| `mock.knowledge` | `query` (string, required), `top_k` (int, optional) | `KnowledgeSearchQuery` |
| `mock.metric` | `metric` (string, required), `service` (string, optional → labels) | `MetricInstantQuery`（`at` 默认 now） |
| `mock.log` | `service` (string, required), `keyword` (string, optional) | `LogSearchQuery`（`start`/`end` 默认近 1h） |

由 `ToolRegistry` + Pydantic model 生成 `ToolSpec`（可放 `app/services/chat_tools.py` 或 `app/providers/llm/tools.py`）。

### 一轮决策语义

1. 组装 `messages` = system + 历史（user/assistant）+ 本轮 user + 本轮已产生的 assistant(`tool_calls`)/`tool` 消息  
2. `acomplete_messages(..., tools=whitelist, tool_choice="auto")`  
3. 若 `tool_calls` 非空：对每个 call → SSE `tool_call` → `ainvoke` → SSE `tool_result` → append `role=tool`（`tool_call_id` 对齐）→ 计入一轮，回到 2  
4. 若无 `tool_calls`：进入终答 — `astream_messages`（不传 tools 或 `tool_choice=none`），只流式 `content`  
5. 达到 3 轮仍有 `tool_calls`：丢弃本轮 calls，强制终答并在 system/user 附加「请基于已有工具结果直接回答」

未知 / 非白名单函数名：写入 `role=tool` 内容为错误说明，不发 SSE `error`，计入一轮。

## SSE 事件

复用 `SseEvent`；`workflow_id` 字段填 `conversation_id`。

| type | 含义 |
|------|------|
| `session` | `payload.conversation_id` |
| `tool_call` | `payload`: `id`, `tool`, `args`；`message` 简述 |
| `tool_result` | `payload`: `id`, `tool`, 精简 `data`；`message` 一行摘要 |
| `answer_delta` | 最终回答增量 |
| `answer` | 最终回答全文 |
| `error` | 失败 |

不推送 `step_started` / Plan-Execute 相关事件。

## 组件

| 组件 | 职责 |
|------|------|
| `app/schemas/chat.py` | `ChatRequest` |
| `app/providers/llm/types.py`（或等同） | `ChatMessage` / `ToolCall` / `LLMCompletion` / `ToolSpec` |
| `app/providers/llm/base.py` + `openai_compatible.py` + `mock.py` | Function Calling 能力 |
| `app/services/chat.py` | `ChatService.stream_chat`：记忆 → FC 循环 → 流式终答 |
| `app/api/chat.py` | `POST /chat` StreamingResponse |
| `app/main.py` | 注入 `ChatService`（LLM + ToolRegistry + MemoryManager） |
| `web` | `streamChat`、proxy `/chat`、App 普通发送改走 chat |

## 数据流

```
用户 message
  → Memory.append(user)
  → messages = system + history + user
  → loop ≤3:
       completion = acomplete_messages(messages, tools=whitelist)
       → tool_calls?
            for each: SSE tool_call → ainvoke → SSE tool_result
                      messages += assistant(tool_calls) + tool results
       → else: break
  → astream_messages(messages, no tools) → answer_delta* → answer
  → Memory.append(assistant 终答文本)
```

持久化到 Memory 的 assistant 内容为**面向用户的最终 Markdown**；本阶段可不把中间 `tool_calls` 写入 ConversationMemory（仅写在当次请求的 `messages` 工作区），以降低 Memory 模型改动。若第二轮需要工具上下文，依赖模型根据历史问答文本推断即可（验收第 3 条以用户可见对话为准）。

## 错误处理

- LLM / 工具异常：SSE `error`
- 客户端 Abort：停止生成器
- 空 `message`：HTTP 422
- `arguments` JSON 非法：`role=tool` 返回解析错误，继续循环

## 明确不做

- Prompt-based JSON ReAct（模型手写 `{"action":"tool"}`）
- 本阶段解析**流式** `tool_calls` 增量（决策轮非流式即可）
- 聊天路径调用 `mock.executor` 或任意变更执行
- 普通聊天路由到 `POST /incident` / Workflow
- 持久化 DB history、鉴权、多用户隔离
- 修改一键运维 / Plan-Execute 主路径行为

## 验收

1. 「我叫 maa」→ 仅有流式 `answer*`（可有 `session`），**无** `tool_call`  
2. 「cpu 高怎么解决」→ 至少一次 `tool_call`（优先 `mock.knowledge`）+ 流式 Markdown 结论  
3. 同一 `conversation_id` 第二轮能引用上文（如「我刚才说我叫什么」）  
4. 前端普通输入走 `/chat`；一键运维仍走 `/ops/one-click`  
5. `pytest`：OpenAI compatible 请求含 `tools`；Mock 路径覆盖有/无 `tool_calls` 的 chat SSE
