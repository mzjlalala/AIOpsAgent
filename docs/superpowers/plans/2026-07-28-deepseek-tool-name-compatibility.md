# DeepSeek Tool Name Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/chat` Function Calling compatible with DeepSeek and use `deepseek-v4-pro` as the documented default model.

**Architecture:** Keep the existing internal ToolRegistry names (`mock.*`) unchanged. Expose API-safe function names to the LLM and translate them back to registry names at the chat-tool boundary.

**Tech Stack:** Python 3.13, Pydantic v2, httpx, pytest, FastAPI

---

### Task 1: Lock the DeepSeek-compatible tool-name contract

**Files:**
- Modify: `tests/services/test_chat_tools.py`

- [x] **Step 1: Write the failing test**

Add a test which asserts every name returned by `build_chat_tool_specs()` matches `^[a-zA-Z0-9_-]+$`, and a dispatch test which invokes `mock_knowledge` while resolving the existing `mock.knowledge` registry entry.

- [x] **Step 2: Run the focused tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_chat_tools.py -q`

Expected: FAIL because the current public names contain dots and are also used directly as registry keys.

### Task 2: Add the protocol-to-registry name mapping

**Files:**
- Modify: `app/services/chat_tools.py`
- Modify: `app/providers/llm/mock.py`

- [x] **Step 1: Define API-safe public names**

Expose `mock_knowledge`, `mock_metric`, and `mock_log`, backed by a mapping to `mock.knowledge`, `mock.metric`, and `mock.log`.

- [x] **Step 2: Use mapped registry names for dispatch**

Validate the public name against the mapping, fetch the mapped internal tool, and retain the existing request builders and summaries.

- [x] **Step 3: Update MockLLM tool calls**

Return the same API-safe names as the real provider so both providers exercise the same chat boundary.

- [x] **Step 4: Verify focused tests pass**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_chat_tools.py tests/providers/test_llm_messages.py tests/api/test_chat_sse.py -q`

Expected: PASS.

### Task 3: Update the default DeepSeek model

**Files:**
- Modify: `app/config/settings.py`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `tests/providers/test_openai_compatible_llm.py`
- Modify: `tests/providers/test_llm_messages.py`

- [x] **Step 1: Add a default-setting assertion**

Assert that a `Settings` instance without `LLM_MODEL` override defaults to `deepseek-v4-pro`.

- [x] **Step 2: Verify the assertion fails**

Run: `.venv/Scripts/python.exe -m pytest tests/providers/test_openai_compatible_llm.py -q`

Expected: FAIL with `deepseek-chat != deepseek-v4-pro`.

- [x] **Step 3: Update defaults and examples**

Replace the remaining `deepseek-chat` default/example references with `deepseek-v4-pro` while leaving the user's local `.env` secret untouched.

- [x] **Step 4: Run complete verification**

Run: `.venv/Scripts/python.exe -m pytest`

Run: `.venv/Scripts/ruff.exe check app tests`

Run: `.venv/Scripts/black.exe --check app tests`

Expected: tests pass; quality-check output is reported exactly, including unrelated pre-existing findings.

- [x] **Step 5: Exercise the real DeepSeek chat request**

Send `hi` through the configured provider with `build_chat_tool_specs()` and confirm HTTP 200 without printing the API key.
