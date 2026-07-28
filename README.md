# OpsAgent

企业级 AI 运维 Agent 平台（AIOps）。

基于大语言模型 + Agent Workflow + RAG + MCP，支持故障分析、指标/日志排查、
知识库检索、人工审批后的自动化操作，以及事故复盘报告生成。

> 当前进度：**一键运维（auto_ops）+ 第九阶段 API / 演示前端**。

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
- Workflow：Plan-Execute 外层引擎 + MemorySaver + `interrupt`/`Command(resume)` 审批闸门
- API：`POST /incident`（SSE）+ `/ops/one-click` + `/workflows/{id}` 状态/审批/事件续订
- LLM：默认 Mock；可通过 `.env` 切换 OpenAI 兼容（DeepSeek 等）
- Web：Vue 3 + Vite 演示控制台（`web/`，proxy 联调）
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

按需修改 `.env` 中的 `APP_ENV`、`DATABASE_URL`、`API_PORT`、以及 LLM 配置等。

接入 DeepSeek（OpenAI 兼容）示例：

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=你的密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
```

密钥只放在本地 `.env`（已 gitignore），不要提交到仓库。

### 3. 启动服务

**命令行：**

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**PyCharm Run/Debug Configuration：**

| 项 | 值 |
|---|---|
| 类型 | Python |
| 运行方式 | 模块名（Module name） |
| 模块名 | `uvicorn` |
| 参数 | `app.main:app --host 0.0.0.0 --port 8000 --reload` |
| 工作目录 | 项目根目录（`OpsAgent`，不要选到 `app/`） |
| Python 解释器 | `OpsAgent/.venv/Scripts/python.exe`（须先 `uv sync`） |

不要用「脚本」直接跑 `app/main.py`，也不要用其他项目的 venv。

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

### 6. 前端演示控制台（Vue3）

另开终端：

```bash
cd web
npm install
npm run dev
```

浏览器打开 http://127.0.0.1:5173（需后端已在 `:8000` 运行）。  
主按钮 **一键运维** 调用 `POST /ops/one-click`（Agent 自主巡检，无需填描述、无需审批）。  
「高级选项」仍可自定义描述 / scenario。

## 目录结构

```
app/
  api/           # HTTP：/health /incident /ops/one-click /workflows
  db/            # Base / Session / Mixins
  models/        # SQLAlchemy ORM（15 张表）
  repositories/  # Async Repository
  tools/         # Tool 抽象 / Mock / Registry / 工厂
  adapters/      # MCP 等外部适配器接口
  agents/        # LangGraph Multi-Agent（事故排查图）
  workflows/     # Plan-Execute / Approval（MemorySaver + interrupt）
  rag/           # RAG：models / ingest / retrieve / store / adapters
  memory/        # Memory：能力组合 Backend + Manager
  services/      # IncidentService 等应用服务
  prompts/       # Prompt Markdown 文件
  providers/     # LLM / Embedding Provider（含 Mock Embedding）
  config/        # Settings + Logging
  schemas/       # Pydantic schemas（含共享 MetadataFilter）
  utils/         # 公共工具
web/             # Vue3 演示控制台（Vite proxy → :8000）
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
7. LangGraph Multi-Agent
8. Workflow（Plan-Execute / Approval）
9. API 接口（Chat / Incident / SSE）（当前）
10. Docker 部署
11. 测试完善

## License

Private / TBD.
