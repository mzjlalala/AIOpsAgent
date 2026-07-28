# OpsAgent Chat Function Calling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `POST /chat` SSE：多轮对话 + OpenAI 兼容 Function Calling（knowledge/metric/log），前端普通输入走 chat，闲聊不再触发 Plan-Execute。

**Architecture:** 扩展 LLM Provider（`acomplete_messages` / `astream_messages`）；`ChatService` 内最多 3 轮 tool_calls → `ainvoke` Mock 工具 → 流式终答；`MemoryManager` 存 user/assistant 文本；复用 `SseEvent`（`workflow_id`=conversation_id）。

**Tech Stack:** FastAPI、httpx、Pydantic、现有 Mock Tools、Vue3/Vite、pytest

## Global Constraints

- Spec：`docs/superpowers/specs/2026-07-28-opsagent-chat-react-design.md`
- 工具白名单仅：`mock.knowledge`、`mock.metric`、`mock.log`（禁止 executor）
- 不做 Prompt JSON ReAct；不做流式 tool_calls 解析
- 一键运维 / `/incident` 行为不变
- 用 `uv` / 项目 `.venv`；Windows PowerShell 兼容命令

---

## 目标文件结构

```
app/providers/llm/types.py          # ChatMessage, ToolCall, ToolSpec, LLMCompletion
app/providers/llm/base.py           # + acomplete_messages / astream_messages
app/providers/llm/openai_compatible.py
app/providers/llm/mock.py
app/services/chat_tools.py          # ToolSpec 构建 + args→Pydantic + dispatch
app/schemas/chat.py                 # ChatRequest
app/schemas/sse.py                  # + session | tool_call | tool_result
app/services/chat.py                # ChatService.stream_chat
app/api/chat.py                     # POST /chat
app/main.py                         # 注入 ChatService
tests/providers/test_llm_messages.py
tests/services/test_chat_tools.py
tests/api/test_chat_sse.py
web/src/api/client.ts               # streamChat
web/src/App.vue                     # 普通发送走 /chat
web/vite.config.ts                  # proxy /chat
```

---

### Task 1: LLM 消息类型与基类方法

**Files:**
- Create: `app/providers/llm/types.py`
- Modify: `app/providers/llm/base.py`
- Test: `tests/providers/test_llm_messages.py`

**Interfaces:**
- Produces: `ChatMessage`, `ToolCall`, `ToolSpec`, `LLMCompletion`; `BaseLLMProvider.acomplete_messages` / `astream_messages`

- [ ] **Step 1: 写入类型与基类默认实现**

`app/providers/llm/types.py`:

```python
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

ChatRole = Literal["system", "user", "assistant", "tool"]

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class ChatMessage(BaseModel):
    role: ChatRole
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

class ToolFunctionSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class ToolSpec(BaseModel):
    type: Literal["function"] = "function"
    function: ToolFunctionSpec

class LLMCompletion(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
```

`base.py` 增加（默认：无 tools 时退化为 `acomplete`/`astream` 拼 system+最后一条 user；有 tools 时子类必须覆盖 `acomplete_messages`）：

```python
async def acomplete_messages(
    self,
    messages: list[ChatMessage],
    *,
    tools: list[ToolSpec] | None = None,
    tool_choice: str = "auto",
) -> LLMCompletion: ...

async def astream_messages(
    self,
    messages: list[ChatMessage],
    *,
    tools: list[ToolSpec] | None = None,
) -> AsyncIterator[str]: ...
```

基类默认：从 messages 抽出 system 与拼接的 user 文本调用现有 `acomplete`/`astream`，忽略 tools（仅作 fallback）。

- [ ] **Step 2: 单测类型序列化**

```python
def test_tool_spec_dump_openai_shape():
    spec = ToolSpec(function=ToolFunctionSpec(
        name="mock.knowledge",
        description="d",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    ))
    d = spec.model_dump()
    assert d["type"] == "function"
    assert d["function"]["name"] == "mock.knowledge"
```

- [ ] **Step 3: Run** `pytest tests/providers/test_llm_messages.py -q` → PASS

- [ ] **Step 4: Commit** `feat(llm): add chat message types for function calling`

---

### Task 2: OpenAICompatible + Mock Function Calling

**Files:**
- Modify: `app/providers/llm/openai_compatible.py`
- Modify: `app/providers/llm/mock.py`
- Test: `tests/providers/test_llm_messages.py`（追加）

**Interfaces:**
- Consumes: Task 1 types
- Produces: 真实/Mock 的 `acomplete_messages` / `astream_messages`

- [ ] **Step 1: OpenAICompatible 实现**

- `_to_api_messages(messages)`：assistant 带 `tool_calls` 时转为 OpenAI 格式（`function.name` / `function.arguments` 为 JSON 字符串）；tool 角色带 `tool_call_id`
- `acomplete_messages`：POST `stream:false`，可选 `tools=[t.model_dump()...]`、`tool_choice`
- 解析 `message.tool_calls`：`arguments` JSON 字符串 → dict（失败则 `{}` 并保留 raw 可选）
- `astream_messages`：同 astream，messages 用 `_to_api_messages`；本阶段忽略流式 tool_calls

- [ ] **Step 2: Mock 实现启发式**

```python
async def acomplete_messages(...):
    # 若 messages 已有 role=tool → 返回 LLMCompletion(content=None, tool_calls=[])
    # 取最近 user content：
    #   含 cpu/CPU/指标/metric → tool mock.metric 或优先 knowledge（含「怎么解决」「知识」→ knowledge）
    #   含 日志/log/error → mock.log
    #   含 知识/手册/怎么解决/排查 → mock.knowledge
    #   否则 tool_calls=[]
    # knowledge 优先于 metric（验收：cpu 高怎么解决 → knowledge）

async def astream_messages(...):
    # 综合最近 user + tool 观察，产出中文 Markdown 短答（分块 yield）
    # 若有 tool 结果：提及知识/指标摘要；闲聊：礼貌回应并记住名字类内容
```

- [ ] **Step 3: 单测**

```python
@pytest.mark.asyncio
async def test_mock_chat_idle_no_tools():
    llm = MockLLMProvider()
    c = await llm.acomplete_messages([
        ChatMessage(role="system", content="s"),
        ChatMessage(role="user", content="我叫 maa"),
    ], tools=[])
    assert c.tool_calls == []

@pytest.mark.asyncio
async def test_mock_chat_cpu_calls_knowledge():
    llm = MockLLMProvider()
    c = await llm.acomplete_messages([
        ChatMessage(role="user", content="cpu 高怎么解决"),
    ], tools=[])
    assert any(t.name == "mock.knowledge" for t in c.tool_calls)

@pytest.mark.asyncio
async def test_openai_messages_sends_tools(monkeypatch):
    # patch httpx，断言 post json 含 tools[0].function.name == mock.knowledge
    # 返回带 tool_calls 的假响应，断言 LLMCompletion.tool_calls[0].name
```

- [ ] **Step 4: Run** `pytest tests/providers/test_llm_messages.py -q` → PASS

- [ ] **Step 5: Commit** `feat(llm): implement function calling for openai-compatible and mock`

---

### Task 3: chat_tools 调度

**Files:**
- Create: `app/services/chat_tools.py`
- Test: `tests/services/test_chat_tools.py`

**Interfaces:**
- Consumes: `ToolRegistry`, ToolCall
- Produces: `CHAT_TOOL_NAMES`, `build_chat_tool_specs()`, `dispatch_chat_tool(registry, call) -> tuple[str, dict]`

- [ ] **Step 1: 实现**

```python
CHAT_TOOL_NAMES = ("mock.knowledge", "mock.metric", "mock.log")

def build_chat_tool_specs() -> list[ToolSpec]:
    # 手写三个 ToolSpec（parameters 对齐 spec 表）

async def dispatch_chat_tool(registry: ToolRegistry, call: ToolCall) -> tuple[str, dict]:
    # 不在白名单 → return ("未知或未授权工具: ...", {})
    # knowledge: KnowledgeSearchQuery(query=..., top_k=...)
    # metric: MetricInstantQuery(metric=..., labels={service: ...} if service)
    # log: LogSearchQuery(service=..., keyword=..., start=now-1h, end=now)
    # result = await tool.ainvoke(req)
    # summary = 一行中文；data = 精简 dict（成功时 result.data 截断）
```

- [ ] **Step 2: 测试** 用 `build_mock_registry()` 调 knowledge，断言 summary 非空且 success 路径

- [ ] **Step 3: Commit** `feat(chat): add tool specs and dispatch for chat FC`

---

### Task 4: ChatService + SSE 类型 + API

**Files:**
- Create: `app/schemas/chat.py`
- Create: `app/services/chat.py`
- Create: `app/api/chat.py`
- Modify: `app/schemas/sse.py`（增加 `session`, `tool_call`, `tool_result`）
- Modify: `app/main.py`
- Test: `tests/api/test_chat_sse.py`

**Interfaces:**
- Consumes: LLM FC、chat_tools、MemoryManager、`build_mock_registry`
- Produces: `ChatService.stream_chat(message, conversation_id=None) -> AsyncIterator[SseEvent]`

- [ ] **Step 1: ChatRequest**

```python
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
```

- [ ] **Step 2: ChatService.stream_chat**

逻辑按 spec 数据流：
1. `cid = conversation_id or uuid4()`
2. yield `session`（payload.conversation_id）
3. `append_turn` user；`get_context(conversation_id=cid, session_id=cid, message_limit=20)`
4. 组装 messages：system（运维助手，可用 FC 工具，闲聊勿乱调工具）+ history MemoryMessage → ChatMessage + 本轮 user
5. `specs = build_chat_tool_specs()`；loop `for _ in range(3)`:
   - `comp = await llm.acomplete_messages(messages, tools=specs)`
   - if not comp.tool_calls: break
   - append assistant message with tool_calls
   - for each call: yield tool_call；`summary, data = await dispatch...`；yield tool_result；append tool message（content=json summary+data）
6. 若仍想调工具（第 3 轮后还有）：messages 追加 user「请基于已有工具结果直接回答用户，不要再调用工具」
7. `async for delta in llm.astream_messages(messages, tools=None): yield answer_delta`
8. yield answer；`append_turn` assistant
9. except → yield error

- [ ] **Step 3: API + main**

```python
# api/chat.py — 同 incident StreamingResponse 头
# main: memory = build_memory_manager(); tools = build_mock_registry()
# app.state.chat_service = ChatService(llm=engine.runtime.llm 或 build_llm_provider, tools, memory)
```

注意：TEST 环境 `build_llm_provider` 已强制 Mock——chat 与 incident 共用 settings。

- [ ] **Step 4: 测试 `tests/api/test_chat_sse.py`**

复用 `_parse_sse`（可从 test_incident_sse 抽到 conftest，或复制）：

```python
def test_chat_idle_no_tools(client):
    r = client.post("/chat", json={"message": "我叫 maa"})
    types = [e["type"] for e in _parse_sse(r.text)]
    assert "session" in types
    assert "answer" in types
    assert "tool_call" not in types
    assert "step_started" not in types

def test_chat_cpu_uses_knowledge(client):
    r = client.post("/chat", json={"message": "cpu 高怎么解决"})
    types = [e["type"] for e in _parse_sse(r.text)]
    assert "tool_call" in types
    assert any(e.get("payload", {}).get("tool") == "mock.knowledge" for e in _parse_sse(r.text) if e["type"]=="tool_call")
    assert types[-1] == "answer"

def test_chat_multi_turn_memory(client):
    r1 = client.post("/chat", json={"message": "我叫 maa"})
    cid = next(e["payload"]["conversation_id"] for e in _parse_sse(r1.text) if e["type"]=="session")
    r2 = client.post("/chat", json={"message": "我刚才说我叫什么", "conversation_id": cid})
    answer = next(e["message"] for e in _parse_sse(r2.text) if e["type"]=="answer")
    assert "maa" in answer.lower() or "maa" in answer
```

Mock `astream_messages` 闲聊/追问需能从 history 回显名字（实现时在 mock 里扫描 history user「我叫 X」）。

- [ ] **Step 5: Run** `pytest tests/api/test_chat_sse.py tests/services/test_chat_tools.py -q` → PASS

- [ ] **Step 6: Commit** `feat(chat): add POST /chat SSE with function calling loop`

---

### Task 5: 前端对接 `/chat`

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/App.vue`
- Modify: `web/vite.config.ts`
- Modify: `web/src/components/ChatMain.vue`（tool_call/tool_result → progress 文案）

**Interfaces:**
- Consumes: 后端 SSE 新类型
- Produces: 普通发送走 `streamChat`

- [ ] **Step 1: client**

```typescript
export async function streamChat(
  message: string,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
  conversationId?: string | null,
): Promise<void> {
  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ message, conversation_id: conversationId || null }),
    signal,
  });
  // 同 readSseStream
}
```

扩展 `SseEventType`：`session` | `tool_call` | `tool_result`

- [ ] **Step 2: App.vue**

- `SessionState` 增加 `conversationId: string | null`
- `handleEvent`：`session` → 写入 `session.conversationId`；`tool_call`/`tool_result` → `progress` 气泡；其余同前
- `runAsk` chat 模式：`streamChat(content, ..., session.conversationId)` 不再 `streamIncident`

- [ ] **Step 3: vite proxy `/chat`**（与 `/incident` 相同 SSE 头处理）

- [ ] **Step 4: `npm run build`** → PASS

- [ ] **Step 5: Commit** `feat(web): route normal chat to /chat SSE`

---

### Task 6: 全量验证

- [ ] **Step 1:** `pytest tests/api/test_chat_sse.py tests/providers/test_llm_messages.py tests/services/test_chat_tools.py -q`
- [ ] **Step 2:** `npm run build`（`web/`）
- [ ] **Step 3:** 手动核对验收清单（spec §验收 1–4）
- [ ] **Step 4:** 若有文档缺口，更新 `README.md` API 列表一行 `POST /chat`

---

## Spec 覆盖自检

| Spec 项 | Task |
|---------|------|
| POST /chat SSE | 4 |
| Function Calling（非 Prompt ReAct） | 1–2 |
| Memory 多轮 | 4 |
| 白名单三工具 | 3 |
| 最多 3 轮 | 4 |
| session/tool_*/answer_* | 4–5 |
| 前端分流 | 5 |
| 不做 executor / incident 改道 | Global + 4 |
| pytest 有/无 tools | 2、4 |
