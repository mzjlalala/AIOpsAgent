"""知识检索 Mock 工具：输出提前兼容 RAG 格式。"""

from __future__ import annotations

from pydantic import BaseModel

from app.tools.context import ToolContext
from app.tools.exceptions import ToolError
from app.tools.knowledge.base import BaseKnowledgeTool, KnowledgeSearchQuery
from app.tools.runtime import RuntimeDependencies
from app.tools.types import JsonValue, ToolOutput

# 确定性知识库假数据（对齐后续 RAG hit / citation 字段）
_MOCK_CORPUS: list[dict[str, JsonValue]] = [
    {
        "document_id": "doc-mock-1",
        "knowledge_id": "kn-mock-1",
        "chunk_id": "chk-mock-1",
        "title": "CPU 打满排查手册",
        "content": "检查进程 CPU、最近发布与慢查询；必要时滚动重启。",
        "source": "runbook/cpu-high.md",
        "score": 0.97,
        "metadata": {"category": "cpu", "version": "1"},
    },
    {
        "document_id": "doc-mock-2",
        "knowledge_id": "kn-mock-2",
        "chunk_id": "chk-mock-2",
        "title": "OOM 处理指南",
        "content": "确认内存水位、heap dump，并评估扩容或限流。",
        "source": "runbook/oom.md",
        "score": 0.88,
        "metadata": {"category": "memory", "version": "1"},
    },
    {
        "document_id": "doc-mock-3",
        "knowledge_id": "kn-mock-3",
        "chunk_id": "chk-mock-3",
        "title": "发布回滚预案",
        "content": "核对变更窗口，执行上一版本回滚并观察错误率。",
        "source": "runbook/rollback.md",
        "score": 0.81,
        "metadata": {"category": "deploy", "version": "1"},
    },
]


class MockKnowledgeTool(BaseKnowledgeTool):
    """Mock 知识检索工具（不访问真实向量库）。"""

    name = "mock.knowledge"
    description = "返回确定性 RAG 兼容命中结果，用于本地联调与测试。"
    timeout_seconds = 5.0

    def _execute(
        self,
        request: BaseModel,
        context: ToolContext,
        runtime: RuntimeDependencies,
    ) -> ToolOutput:
        """返回 hits + citations，字段兼容后续 RAG 阶段。"""
        _ = runtime
        if not isinstance(request, KnowledgeSearchQuery):
            raise ToolError(f"不支持的知识检索请求类型: {type(request).__name__}")

        query_lower = request.query.lower()
        ranked = sorted(
            _MOCK_CORPUS,
            key=lambda item: (
                0 if query_lower and query_lower in str(item["title"]).lower() else 1,
                -float(item["score"]),  # type: ignore[arg-type]
            ),
        )
        selected = ranked[: request.top_k]
        hits: list[dict[str, JsonValue]] = []
        citations: list[dict[str, JsonValue]] = []
        for index, item in enumerate(selected, start=1):
            hit: dict[str, JsonValue] = {
                "rank": index,
                "score": item["score"],
                "document_id": item["document_id"],
                "knowledge_id": item["knowledge_id"],
                "chunk_id": item["chunk_id"],
                "title": item["title"],
                "content": item["content"],
                "source": item["source"],
                "metadata": item["metadata"],
            }
            hits.append(hit)
            citations.append(
                {
                    "chunk_id": item["chunk_id"],
                    "source": item["source"],
                    "title": item["title"],
                }
            )

        return {
            "query": request.query,
            "top_k": request.top_k,
            "hits": hits,
            "citations": citations,
            "trace_id": context.trace_id,
            "mock": True,
        }
