"""Memory 领域模型。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.tools.types import JsonValue


class BaseMemoryRecord(BaseModel):
    """记忆记录基类；向量侧只读取已填好的 embedding。"""

    id: str
    content: str = Field(description="展示 / 参与 embed 的主文本。")
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime | None = Field(default=None)


class MemoryMessage(BaseModel):
    """对话轮次消息。"""

    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class SessionContext(BaseModel):
    """会话级键值上下文。"""

    session_id: str
    data: dict[str, JsonValue] = Field(default_factory=dict)


class LongMemoryItem(BaseMemoryRecord):
    """长期记忆条目。"""

    tags: list[str] = Field(default_factory=list)


class ExperienceRecord(BaseMemoryRecord):
    """经验记忆：成功/失败案例的结构化记录。"""

    content: str = ""
    symptom: str
    root_cause: str
    solution: str
    environment: dict[str, JsonValue] = Field(default_factory=dict)
    outcome: Literal["success", "failure"]

    @model_validator(mode="after")
    def _ensure_content(self) -> ExperienceRecord:
        """若 content 为空，则由结构化字段拼接。"""
        if not self.content.strip():
            object.__setattr__(
                self,
                "content",
                (
                    f"symptom={self.symptom}; "
                    f"root_cause={self.root_cause}; "
                    f"solution={self.solution}"
                ),
            )
        # 便于 VectorMemoryStore 按 outcome 过滤
        meta = dict(self.metadata)
        meta.setdefault("outcome", self.outcome)
        object.__setattr__(self, "metadata", meta)
        return self


class ScoredLongHit(BaseModel):
    """带分数的长期记忆命中。"""

    item: LongMemoryItem
    score: float


class ScoredExperienceHit(BaseModel):
    """带分数的经验记忆命中。"""

    item: ExperienceRecord
    score: float


class AgentMemoryContext(BaseModel):
    """门面聚合输出，供后续 Agent 消费。"""

    messages: list[MemoryMessage] = Field(default_factory=list)
    session: SessionContext | None = None
    long_hits: list[ScoredLongHit] = Field(default_factory=list)
    experience_hits: list[ScoredExperienceHit] = Field(default_factory=list)
