"""LLM 输出 JSON 解析层（独立于 Provider）。"""

from __future__ import annotations

import json
import re
from typing import Any


class AgentJsonParseError(ValueError):
    """无法从模型文本中解析出合法 JSON。"""


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def parse_json_payload(text: str) -> Any:
    """从模型输出中提取 JSON（支持 fenced code 或纯 JSON）。

    失败时抛出 ``AgentJsonParseError``。
    """
    stripped = text.strip()
    if not stripped:
        raise AgentJsonParseError("空文本无法解析 JSON")

    candidates = [stripped]
    match = _FENCE_RE.search(stripped)
    if match:
        candidates.insert(0, match.group(1).strip())

    # 尝试截取首个 JSON 数组/对象片段
    for opener, closer in (("[", "]"), ("{", "}")):
        start = stripped.find(opener)
        end = stripped.rfind(closer)
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])

    errors: list[str] = []
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
    raise AgentJsonParseError(f"无法解析 JSON: {errors[0] if errors else 'unknown'}")
