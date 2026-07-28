"""确定性 Mock LLM（按 scenario 返回规划/报告；支持 chat Function Calling）。"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator, Sequence

from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.types import ChatMessage, LLMCompletion, ToolCall, ToolSpec

_SCENARIO_PLANS: dict[str, list[dict[str, str]]] = {
    "cpu_high": [
        {"step_id": "1", "agent": "metric", "goal": "获取 CPU 指标"},
        {"step_id": "2", "agent": "log", "goal": "检索相关错误日志"},
        {"step_id": "3", "agent": "knowledge", "goal": "检索 CPU 排查知识库"},
    ],
    "memory_leak": [
        {"step_id": "1", "agent": "metric", "goal": "获取内存指标"},
        {"step_id": "2", "agent": "log", "goal": "检索 OOM 相关日志"},
        {"step_id": "3", "agent": "knowledge", "goal": "检索内存泄漏知识库"},
        {"step_id": "4", "agent": "executor", "goal": "演练重启（dry_run）"},
    ],
    "auto_ops": [
        {"step_id": "1", "agent": "metric", "goal": "拉取默认服务核心指标（面板）"},
        {"step_id": "2", "agent": "log", "goal": "检索近期错误与告警日志"},
        {"step_id": "3", "agent": "knowledge", "goal": "检索一键巡检与排障手册"},
        {"step_id": "4", "agent": "executor", "goal": "必要时演练重启（dry_run）"},
    ],
}

_SCENARIO_REPORTS: dict[str, str] = {
    "cpu_high": (
        "CPU 持续接近 100%，可能由于线程池耗尽或热点循环；"
        "建议结合慢查询与最近发布排查。"
    ),
    "memory_leak": (
        "内存持续上涨并出现 OOM 风险，疑似泄漏或堆配置过小；"
        "建议抓 heap dump 并评估扩容。"
    ),
    "auto_ops": (
        "## 问题判断\n"
        "默认服务巡检已完成，当前为 Mock 证据链下的示例结论。\n\n"
        "## 可能原因\n"
        "指标偏高或近期错误日志增多，需结合真实监控确认。\n\n"
        "## 解决建议\n"
        "1. 核对 CPU/内存水位与最近发布；2. 按知识库手册排查热点；"
        "3. 必要时在低峰做滚动重启演练。"
    ),
}


class MockLLMProvider(BaseLLMProvider):
    """按 scenario 返回确定性字符串；规划输出 JSON steps 数组。"""

    def __init__(
        self,
        *,
        scenario: str = "cpu_high",
        model_name: str = "mock-llm",
    ) -> None:
        self._scenario = scenario if scenario in _SCENARIO_PLANS else "cpu_high"
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def scenario(self) -> str:
        return self._scenario

    async def acomplete(self, *, system: str, prompt: str) -> str:
        _ = system
        lower = prompt.lower()
        if "plan" in lower or "规划" in prompt or "steps" in lower:
            steps = [
                {**item, "status": "pending"}
                for item in _SCENARIO_PLANS[self._scenario]
            ]
            return json.dumps(steps, ensure_ascii=False)
        return _SCENARIO_REPORTS.get(
            self._scenario,
            "【Mock 事故小结】基于 artifacts 完成汇总。",
        )

    async def astream(self, *, system: str, prompt: str) -> AsyncIterator[str]:
        """模拟流式：按小段产出，便于前端演示。"""
        text = await self.acomplete(system=system, prompt=prompt)
        size = 24
        for i in range(0, len(text), size):
            yield text[i : i + size]
            await asyncio.sleep(0.01)

    async def acomplete_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
        tool_choice: str = "auto",
    ) -> LLMCompletion:
        _ = tools, tool_choice
        if any(m.role == "tool" for m in messages):
            return LLMCompletion(content=None, tool_calls=[])
        user_text = _latest_user_text(messages)
        call = _decide_tool_call(user_text)
        if call is None:
            return LLMCompletion(content=None, tool_calls=[])
        return LLMCompletion(content=None, tool_calls=[call])

    async def astream_messages(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] | None = None,
    ) -> AsyncIterator[str]:
        _ = tools
        text = _compose_chat_answer(messages)
        size = 24
        for i in range(0, len(text), size):
            yield text[i : i + size]
            await asyncio.sleep(0.01)


def _latest_user_text(messages: Sequence[ChatMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content:
            return msg.content
    return ""


def _decide_tool_call(user_text: str) -> ToolCall | None:
    text = user_text.strip()
    if not text:
        return None
    lower = text.lower()
    needs_ops = any(
        key in text or key in lower
        for key in (
            "cpu",
            "CPU",
            "内存",
            "指标",
            "metric",
            "日志",
            "log",
            "知识",
            "手册",
            "怎么解决",
            "排查",
            "告警",
            "OOM",
            "oom",
        )
    )
    if not needs_ops:
        return None
    if any(k in text or k in lower for k in ("日志", "log", "error", "报错")) and not any(
        k in text for k in ("怎么解决", "知识", "手册")
    ):
        return ToolCall(
            id="call_mock_log",
            name="mock.log",
            arguments={"service": "api", "keyword": text[:40]},
        )
    if any(k in text or k in lower for k in ("指标", "metric")) and "怎么" not in text:
        return ToolCall(
            id="call_mock_metric",
            name="mock.metric",
            arguments={"metric": "cpu_usage", "service": "api"},
        )
    # 默认 /「怎么解决」优先知识库（验收：cpu 高怎么解决）
    return ToolCall(
        id="call_mock_knowledge",
        name="mock.knowledge",
        arguments={"query": text, "top_k": 3},
    )


def _compose_chat_answer(messages: Sequence[ChatMessage]) -> str:
    user_text = _latest_user_text(messages)
    name = _find_stated_name(messages)
    tool_bits = [
        (m.content or "")
        for m in messages
        if m.role == "tool" and m.content
    ]
    if tool_bits:
        evidence = "\n".join(tool_bits)[:800]
        return (
            "## 问题判断\n"
            f"已根据工具结果分析你的问题：{user_text}\n\n"
            "## 参考证据\n"
            f"{evidence}\n\n"
            "## 解决建议\n"
            "1. 对照知识库/指标结论定位热点；2. 观察近期发布与流量；"
            "3. 必要时在低峰做限流或滚动重启演练。"
        )
    if any(k in user_text for k in ("叫什么", "我的名字", "我刚才说")):
        if name:
            return f"你刚才说你叫 **{name}**。"
        return "我这边还没记下你的名字，可以再说一次吗？"
    if name and ("我叫" in user_text or "我是" in user_text):
        return f"你好，{name}！我是 OpsAgent，有运维问题随时问我。"
    if "我叫" in user_text or "我是" in user_text:
        m = re.search(r"我叫\s*([^\s，。！？,.!?]{1,32})", user_text)
        if m:
            return f"你好，{m.group(1)}！我是 OpsAgent，有运维问题随时问我。"
    return (
        f"收到：{user_text}\n\n"
        "我是运维助手。可以直接问故障现象，或点「一键运维巡检」。"
    )


def _find_stated_name(messages: Sequence[ChatMessage]) -> str | None:
    for msg in messages:
        if msg.role != "user" or not msg.content:
            continue
        m = re.search(r"我叫\s*([^\s，。！？,.!?]{1,32})", msg.content)
        if m:
            return m.group(1)
    return None
