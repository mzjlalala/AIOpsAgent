# OpsAgent

企业级 AI 运维 Agent 平台（AIOps）。

基于大语言模型 + Agent Workflow + RAG + MCP，支持故障分析、指标/日志排查、
知识库检索、人工审批后的自动化操作，以及事故复盘报告生成。

> 当前进度：**第七阶段 — LangGraph Multi-Agent**。

## 技术栈（截至本阶段）

- Python 3.13+
- FastAPI / Pydantic v2 / Loguru
- SQLAlchemy 2.x（async）+ asyncmy / Alembic + PyMySQL
- Tool 抽象：`ainvoke` / `_execute` / ToolRegistry / MCP Adapter 接口
- Mock Tool：`mock.metric` / `mock.log` / `mock.executor` / `mock.knowledge` + `build_mock_registry()`
- Embedding：`EmbeddingProvider` + sha256 `MockEmbeddingProvider`
- RAG：Ingest/Retrieve 分层流水线、InMemory VectorStore、可选 FAISS adapter
- Memory：能力组合 Backend + Conversation/Session/Long/Experience + `MemoryManager`
- Agents：LangGraph **1.x**（StateGraph + START/END + conditional_edges，不用 AgentExecutor）+ MockLLM
- uv（依赖与虚拟环境）
- pytest / aiosqlite / Ruff / Black / isort

## 快速开始

### 1. 安装依赖

```bash
uv sync --group dev
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

按需修改 `.env` 中的 `APP_ENV`、`DATABASE_URL`、`API_PORT` 等。

### 3. 启动服务

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

### 4. 数据库迁移（MySQL）

确保 MySQL 已创建库，并配置好 `DATABASE_URL` / `DATABASE_URL_SYNC`，然后：

```bash
uv run alembic upgrade head
```

本地无 MySQL 时，Repository 测试使用内存 SQLite（aiosqlite），无需本机数据库。

### 5. 运行测试与质量检查

```bash
uv run pytest
uv run ruff check app tests
uv run black --check app tests
uv run isort --check-only app tests
```

## 目录结构

```
app/
  api/           # HTTP 路由（本阶段仅 /health）
  db/            # Base / Session / Mixins
  models/        # SQLAlchemy ORM（15 张表）
  repositories/  # Async Repository
  tools/         # Tool 抽象 / Mock / Registry / 工厂
  adapters/      # MCP 等外部适配器接口
  agents/        # LangGraph Multi-Agent（事故排查图）
  workflows/     # LangGraph 工作流（后续阶段）
  rag/           # RAG：models / ingest / retrieve / store / adapters
  memory/        # Memory：能力组合 Backend + Manager
  services/      # 领域服务（后续阶段）
  prompts/       # Prompt Markdown 文件
  providers/     # LLM / Embedding Provider（含 Mock Embedding）
  config/        # Settings + Logging
  schemas/       # Pydantic schemas（含共享 MetadataFilter）
  utils/         # 公共工具
alembic/         # 数据库迁移
tests/           # pytest
```

## 开发阶段规划

1. 项目初始化
2. MySQL Schema / SQLAlchemy / Repository
3. Tool 接口设计
4. Mock Tool 实现
5. Embedding Provider + RAG
6. Memory 系统
7. LangGraph Multi-Agent（当前）
8. Workflow（Plan-Execute / Approval）
9. API 接口（Chat / Incident / SSE）
10. Docker 部署
11. 测试完善

## License

Private / TBD.
