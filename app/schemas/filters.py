"""共享过滤条件模型（RAG / Memory 统一使用）。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.types import JsonValue


class MetadataFilter(BaseModel):
    """元数据过滤条件；本阶段实现仅支持 operator=eq。"""

    field: str = Field(description="字段名（顶层属性或 metadata 键）。")
    operator: str = Field(
        default="eq",
        description="比较运算符，预留 contains/in/range。",
    )
    value: JsonValue = Field(description="期望值。")
