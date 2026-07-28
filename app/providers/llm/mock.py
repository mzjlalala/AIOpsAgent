"""确定性 Mock LLM（按 scenario 返回规划/报告）。"""

from __future__ import annotations

import json

from app.providers.llm.base import BaseLLMProvider

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
        "一键巡检完成：指标与日志已采集，知识库给出处置建议；"
        "若存在高风险变更请确认审批后再执行。"
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
