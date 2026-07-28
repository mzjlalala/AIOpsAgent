"""Chat 路径工具 Schema 与调度（Function Calling）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.providers.llm.types import ToolCall, ToolFunctionSpec, ToolSpec
from app.tools.context import ToolContext
from app.tools.knowledge import KnowledgeSearchQuery
from app.tools.log import LogSearchQuery
from app.tools.metric import MetricInstantQuery
from app.tools.registry import ToolRegistry

CHAT_TOOL_NAMES: tuple[str, ...] = ("mock.knowledge", "mock.metric", "mock.log")


def build_chat_tool_specs() -> list[ToolSpec]:
    """供 LLM tools 参数使用的白名单 Schema。"""
    return [
        ToolSpec(
            function=ToolFunctionSpec(
                name="mock.knowledge",
                description="检索运维知识库与排障手册。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "检索语句"},
                        "top_k": {
                            "type": "integer",
                            "description": "返回条数",
                            "default": 3,
                        },
                    },
                    "required": ["query"],
                },
            )
        ),
        ToolSpec(
            function=ToolFunctionSpec(
                name="mock.metric",
                description="查询瞬时监控指标。",
                parameters={
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "description": "指标名"},
                        "service": {
                            "type": "string",
                            "description": "服务名，写入 labels",
                        },
                    },
                    "required": ["metric"],
                },
            )
        ),
        ToolSpec(
            function=ToolFunctionSpec(
                name="mock.log",
                description="检索服务日志。",
                parameters={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "服务名"},
                        "keyword": {
                            "type": "string",
                            "description": "关键词",
                        },
                    },
                    "required": ["service"],
                },
            )
        ),
    ]


async def dispatch_chat_tool(
    registry: ToolRegistry,
    call: ToolCall,
) -> tuple[str, dict[str, Any]]:
    """执行白名单工具，返回 (摘要, 精简 data)。"""
    if call.name not in CHAT_TOOL_NAMES:
        return f"未知或未授权工具: {call.name}", {}
    if call.name not in registry:
        return f"工具未注册: {call.name}", {}

    ctx = ToolContext(trace_id=f"chat-{call.id}")
    try:
        request = _build_request(call)
        result = await registry.get(call.name).ainvoke(request, context=ctx)
    except Exception as exc:  # noqa: BLE001 — 转为 tool observation
        return f"工具调用失败: {exc}", {"error": str(exc)}

    data = _compact_data(result.data)
    if not result.success:
        summary = result.error or f"{call.name} 失败"
        return summary, {"success": False, "error": result.error, "data": data}

    summary = _summarize(call.name, data)
    return summary, {"success": True, "data": data}


def _build_request(call: ToolCall) -> Any:
    args = call.arguments or {}
    if call.name == "mock.knowledge":
        top_k = args.get("top_k", 3)
        try:
            top_k_int = int(top_k)
        except (TypeError, ValueError):
            top_k_int = 3
        return KnowledgeSearchQuery(
            query=str(args.get("query") or ""),
            top_k=max(1, min(top_k_int, 50)),
        )
    if call.name == "mock.metric":
        service = args.get("service")
        labels = {"service": str(service)} if service else {}
        return MetricInstantQuery(
            metric=str(args.get("metric") or "cpu_usage"),
            at=datetime.now(UTC),
            labels=labels,
        )
    if call.name == "mock.log":
        now = datetime.now(UTC)
        keyword = args.get("keyword")
        return LogSearchQuery(
            service=str(args.get("service") or "api"),
            keyword=str(keyword) if keyword is not None else None,
            start=now - timedelta(hours=1),
            end=now,
            limit=50,
        )
    raise ValueError(f"unsupported tool: {call.name}")


def _compact_data(data: Any) -> dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False, default=str)
        if len(text) > 2000:
            return {"preview": text[:2000], "truncated": True}
        return data
    return {"value": str(data)[:500]}


def _summarize(tool_name: str, data: dict[str, Any]) -> str:
    if tool_name == "mock.knowledge":
        hits = data.get("hits") if isinstance(data.get("hits"), list) else []
        if hits and isinstance(hits[0], dict):
            title = hits[0].get("title") or hits[0].get("document_id") or "命中"
            return f"知识命中：{title}"
        return "知识库检索完成"
    if tool_name == "mock.metric":
        value = data.get("value")
        metric = data.get("metric") or "metric"
        return f"指标 {metric}≈{value}"
    if tool_name == "mock.log":
        events = data.get("events") if isinstance(data.get("events"), list) else []
        return f"日志命中 {len(events)} 条"
    return f"{tool_name} 完成"
