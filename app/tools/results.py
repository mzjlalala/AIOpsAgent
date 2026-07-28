"""工具执行结果与元数据类型。"""

from __future__ import annotations

from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.tools.immutability import freeze_str_tags
from app.tools.types import ToolCategory, ToolOutput


class ToolMetadata(BaseModel):
    """工具结果的类型化元数据（不可变）。"""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    tool_name: str = Field(description="工具名称。")
    category: ToolCategory = Field(description="工具分类。")
    attempt: int = Field(default=1, ge=1, description="第几次尝试。")
    tags: MappingProxyType = Field(
        default_factory=freeze_str_tags,
        description="额外字符串标签。",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def _validate_tags(cls, value: object) -> MappingProxyType:
        """构造时深拷贝并冻结 tags。"""
        frozen = freeze_str_tags(value)
        assert isinstance(frozen, MappingProxyType)
        return frozen


class ToolResult(BaseModel):
    """工具调用统一结果（不可变）。"""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(description="是否成功。")
    trace_id: str = Field(description="链路 ID，与 ToolContext.trace_id 对齐。")
    data: ToolOutput = Field(default=None, description="业务输出数据。")
    error: str | None = Field(default=None, description="失败时的错误信息。")
    latency_ms: float | None = Field(default=None, description="端到端耗时（毫秒）。")
    metadata: ToolMetadata = Field(description="类型化元数据。")
