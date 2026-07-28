"""Memory 系统单测。"""

from __future__ import annotations

import pytest

from app.memory import (
    ExperienceRecord,
    LongMemoryItem,
    MemoryMessage,
    MemoryStoreError,
    build_memory_manager,
)
from app.memory.backend.memory import InMemoryVectorMemoryStore
from app.schemas.filters import MetadataFilter


@pytest.mark.asyncio
async def test_conversation_and_session() -> None:
    mgr = build_memory_manager()
    await mgr.append_turn("c1", MemoryMessage(role="user", content="CPU 很高"))
    await mgr.append_turn("c1", MemoryMessage(role="assistant", content="先查指标"))
    recent = await mgr.conversation.aget_recent("c1", limit=1)
    assert len(recent) == 1
    assert recent[0].role == "assistant"

    await mgr.set_session("s1", {"incident_id": "inc-1", "hypothesis": "发布引起"})
    ctx = await mgr.session.aget("s1")
    assert ctx is not None
    assert ctx.data["incident_id"] == "inc-1"
    updated = await mgr.session.aupdate("s1", {"hypothesis": "慢查询"})
    assert updated.data["hypothesis"] == "慢查询"
    assert updated.data["incident_id"] == "inc-1"


@pytest.mark.asyncio
async def test_long_and_experience_recall() -> None:
    mgr = build_memory_manager()
    await mgr.long_term.asave(
        LongMemoryItem(
            id="long-1",
            content="Kubernetes Pod CPU 打满时优先检查 HPA 与最近发布",
            tags=["k8s", "cpu"],
        )
    )
    await mgr.remember_experience(
        ExperienceRecord(
            id="exp-1",
            symptom="API 延迟升高",
            root_cause="慢 SQL",
            solution="加索引并限流",
            environment={"svc": "checkout"},
            outcome="success",
        )
    )
    await mgr.remember_experience(
        ExperienceRecord(
            id="exp-2",
            symptom="OOM",
            root_cause="堆配置过小",
            solution="调大 heap",
            environment={"svc": "worker"},
            outcome="failure",
        )
    )

    long_hits = await mgr.long_term.arecall("Pod CPU 打满", top_k=3)
    assert long_hits
    assert long_hits[0].item.id == "long-1"

    success_hits = await mgr.experience.arecall(
        "API 延迟",
        top_k=5,
        filters=[MetadataFilter(field="outcome", operator="eq", value="success")],
    )
    assert len(success_hits) == 1
    assert success_hits[0].item.outcome == "success"
    assert success_hits[0].item.solution == "加索引并限流"


@pytest.mark.asyncio
async def test_get_context_gather() -> None:
    mgr = build_memory_manager()
    await mgr.append_turn("c1", MemoryMessage(role="user", content="排查 OOM"))
    await mgr.set_session("s1", {"env": "prod"})
    await mgr.long_term.asave(
        LongMemoryItem(id="l2", content="OOM 先看 RSS 与限流", tags=["oom"])
    )
    await mgr.remember_experience(
        ExperienceRecord(
            id="e3",
            symptom="OOM Kill",
            root_cause="内存泄漏",
            solution="重启并抓 heap dump",
            outcome="success",
        )
    )

    ctx = await mgr.get_context(
        conversation_id="c1",
        session_id="s1",
        query="OOM",
        long_top_k=2,
        experience_top_k=2,
    )
    assert len(ctx.messages) == 1
    assert ctx.session is not None
    assert ctx.session.data["env"] == "prod"
    assert ctx.long_hits
    assert ctx.experience_hits
    assert ctx.experience_hits[0].item.symptom


@pytest.mark.asyncio
async def test_vector_store_requires_embedding() -> None:
    store = InMemoryVectorMemoryStore()
    with pytest.raises(MemoryStoreError):
        await store.aupsert(
            "long",
            [LongMemoryItem(id="x", content="no emb", embedding=None)],
        )


@pytest.mark.asyncio
async def test_get_context_without_query() -> None:
    mgr = build_memory_manager()
    await mgr.append_turn("c1", MemoryMessage(role="user", content="hi"))
    ctx = await mgr.get_context(conversation_id="c1", session_id="missing")
    assert len(ctx.messages) == 1
    assert ctx.session is None
    assert ctx.long_hits == []
    assert ctx.experience_hits == []
