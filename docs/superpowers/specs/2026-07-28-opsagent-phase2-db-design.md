# OpsAgent Phase 2 — Database / Model / Repository Design

Date: 2026-07-28

## Goal

Deliver enterprise-grade persistence for OpsAgent: full MySQL schema (15 tables),
SQLAlchemy 2.x async ORM models, Alembic migrations, and Repository pattern access.

## Decisions

- All 15 tables from `init.md` (session table named `user_sessions` to avoid reserved words)
- Async SQLAlchemy + `asyncmy` at runtime; Alembic uses sync `pymysql` URL
- Tests use in-memory `aiosqlite` + `metadata.create_all`
- Domain-split models + generic `BaseRepository[T]` + per-entity repositories
- Vectors stay in Milvus; MySQL stores only `milvus_id` references on `chunk`

## Tables

| Table | Purpose |
|-------|---------|
| users | Accounts |
| user_sessions | Auth sessions |
| conversation | Chat / investigation threads |
| message | Messages |
| incident | Incidents / alerts |
| agent_trace | Agent node spans |
| tool_call | Tool invocations |
| tool_result | Tool outputs |
| documents | Source documents |
| knowledge | Knowledge entries |
| chunk | Chunks + milvus_id |
| report | Postmortems |
| experience | Experience memory |
| workflow | Plan-execute instances |
| approval | Human approval gates |

## Package layout

- `app/db/` — Base, mixins, async session, `get_db`
- `app/models/` — ORM by domain
- `app/repositories/` — CRUD + domain queries
- `alembic/` — migrations (`upgrade head` against MySQL)

## Out of scope

Auth APIs, Agent/RAG business logic, Redis/Milvus wiring, Docker MySQL (phase 10).

## Verification

- `uv run pytest`
- `uv run ruff check app tests`
- `uv run black --check app tests`
- `uv run isort --check-only app tests`
