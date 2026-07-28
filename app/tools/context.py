"""不可变的工具调用上下文。"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field


def _empty_tags() -> Mapping[str, str]:
    """默认空标签（不可变视图）。"""
    return MappingProxyType({})


class ToolContext(BaseModel):
    """工具一次调用的不可变上下文。

    仅承载可序列化的追踪/业务标识，禁止放入 Session/Client 等运行时依赖。
    需要变更时使用 ``model_copy(update=...)`` 生成新实例。
    """

    model_config = ConfigDict(frozen=True)

    trace_id: str = Field(description="本次调用链路 ID。")
    request_id: str | None = Field(default=None, description="上游请求 ID。")
    incident_id: int | None = Field(default=None, description="关联事故 ID。")
    workflow_id: int | None = Field(default=None, description="关联工作流 ID。")
    user_id: int | None = Field(default=None, description="发起用户 ID。")
    tags: Mapping[str, str] = Field(
        default_factory=_empty_tags,
        description="仅允许字符串标签，禁止塞入可变依赖对象。",
    )
