# OpsAgent 第六阶段：Memory 系统（接口优先）

Date: 2026-07-28

## 目标

落地四类 Memory（Conversation / Session / Long / Experience），采用能力组合式 Backend 与 MemoryManager 门面，供后续 Agent 接入。

## 关键决策

- MemoryBackend = ListStore + KvStore + VectorMemoryStore 组合（非万能接口）
- `BaseMemoryRecord`；Experience 含 symptom / root_cause / solution / environment / outcome
- `get_context` 使用 `asyncio.gather` 并发
- `MetadataFilter` 统一于 `app/schemas/filters.py`
- Long / Experience 使用 Mock Embedding 相似度召回；向量侧不负责 embed
- 默认 InMemory；不接 Redis / Milvus / Agent / API

## 验收

- 对话窗口、Session KV、向量召回、outcome filter、get_context 聚合
- RAG 现有 MetadataFilter 测试仍通过
- pytest / ruff / black / isort
