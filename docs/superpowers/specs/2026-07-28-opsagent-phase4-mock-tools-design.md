# OpsAgent 第四阶段：Mock Tool 实现

Date: 2026-07-28

## 目标

在第三阶段 Tool 抽象之上，落地四类确定性 Mock Tool 与 `build_mock_registry()` 工厂，供本地联调、单测与后续 Agent 显式装配使用。

## 关键决策

- 四类 Mock：`MockMetricTool` / `MockLogTool` / `MockExecutorTool` / `MockKnowledgeTool`
- 确定性内存假数据；不访问 Prometheus / SLS / K8s / 向量库
- `build_mock_registry()` 工厂；**不**自动注入 `create_app`
- **不**写生产实现
- 对外调用统一走 `ainvoke()`；语义方法（`query_range` / `search` / `execute` 等）内部亦如此
- `_execute(request, context, runtime) -> ToolOutput` 与第三阶段签名一致
- `MockExecutorTool`：`simulated=True`、`applied=False` 恒成立；`dry_run=False` 仅打警告日志
- Knowledge 输出提前兼容 RAG：`hits` + `citations`，含 `document_id` / `knowledge_id` / `chunk_id` / `score` / `content` / `source`
- 中文注释

## 结构

```
app/tools/
  metric/mock.py
  log/mock.py
  executor/mock.py
  knowledge/mock.py
  factory.py
tests/tools/test_mock_tools.py
```

## 工具名称

| 类 | name |
|----|------|
| MockMetricTool | `mock.metric` |
| MockLogTool | `mock.log` |
| MockExecutorTool | `mock.executor` |
| MockKnowledgeTool | `mock.knowledge` |

## Knowledge RAG 兼容输出

```python
{
  "query": "...",
  "top_k": 5,
  "hits": [
    {
      "rank": 1,
      "score": 0.92,
      "document_id": "doc-mock-1",
      "knowledge_id": "kn-mock-1",
      "chunk_id": "chk-mock-1",
      "title": "...",
      "content": "...",
      "source": "runbook/mock.md",
      "metadata": {"category": "cpu", "version": "1"}
    }
  ],
  "citations": [
    {"chunk_id": "chk-mock-1", "source": "runbook/mock.md", "title": "..."}
  ]
}
```

## 工厂

```python
def build_mock_registry() -> ToolRegistry:
    """注册四类 Mock，供测试与后续 Agent 显式使用。"""
```

## 明确不做

- 生产 Tool 类、Settings 自动装配、API、真实外部调用

## 验收

- 四类 Mock `ainvoke` / 语义方法成功；结构断言通过
- Executor：`dry_run` 强制；`execute(dry_run=False)` 仍 `applied=False`
- Knowledge：含 `hits` + `citations`
- `build_mock_registry()` 长度 4、按 category 可查
- pytest / ruff / black / isort 通过
