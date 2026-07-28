# OpsAgent

企业级 AI 运维 Agent 平台（AIOps）。

基于大语言模型 + Agent Workflow + RAG + MCP，支持故障分析、指标/日志排查、
知识库检索、人工审批后的自动化操作，以及事故复盘报告生成。

> 当前进度：**第一阶段 — 项目初始化**（可运行脚手架，业务能力后续分阶段交付）。

## 技术栈（本阶段）

- Python 3.13+
- FastAPI / Pydantic v2 / Loguru
- uv（依赖与虚拟环境）
- pytest / Ruff / Black / isort

## 快速开始

### 1. 安装依赖

```bash
uv sync --group dev
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

按需修改 `.env` 中的 `APP_ENV`、`LOG_LEVEL`、`API_PORT` 等。

### 3. 启动服务

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期响应示例：

```json
{
  "status": "ok",
  "service": "OpsAgent",
  "env": "dev",
  "version": "0.1.0"
}
```

### 4. 运行测试与质量检查

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
  agents/        # Multi-Agent（后续阶段）
  workflows/     # LangGraph 工作流（后续阶段）
  tools/         # Tool Adapter（后续阶段）
  rag/           # RAG 流水线（后续阶段）
  memory/        # 记忆系统（后续阶段）
  models/        # ORM（后续阶段）
  repositories/  # 数据访问（后续阶段）
  services/      # 领域服务（后续阶段）
  prompts/       # Prompt Markdown 文件
  providers/     # LLM / Embedding Provider
  adapters/      # MCP 等外部适配器
  config/        # Settings + Logging
  schemas/       # Pydantic schemas
  utils/         # 公共工具
tests/           # pytest
config/          # 环境覆盖预留
```

## 开发阶段规划

1. 项目初始化（当前）
2. MySQL Schema / SQLAlchemy / Repository
3. Tool 接口设计
4. Mock Tool 实现
5. Embedding Provider + RAG
6. Memory 系统
7. LangGraph Multi-Agent
8. Workflow（Plan-Execute / Approval）
9. API 接口（Chat / Incident / SSE）
10. Docker 部署
11. 测试完善

## License

Private / TBD.
