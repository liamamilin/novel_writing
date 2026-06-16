# Novel Writing Runtime — AGENTS.md

## Quick start

```bash
pip install -e ".[dev]"     # backend
npm install                  # frontend (cd frontend/)
docker compose build         # Docker build
docker compose up -d         # Docker run (backend:8000, frontend:3000)
```

## Backend commands

```bash
uvicorn novel_runtime.main:app --reload   # start API on :8000
pytest tests/ -q                           # all tests (102, 1 skipped w/o LLM key)
pytest tests/unit/ -q                      # unit only
pytest tests/integration/ -q               # integration (mock LLM)
pytest tests/e2e/ -q                       # e2e (requires LLM_API_KEY)
```

## Frontend commands

```bash
cd frontend/
npm run dev       # dev server, proxies /api -> :8000
npm run build     # production build (tsc + vite)
```

## Architecture

```
novel_runtime/        # Python backend (FastAPI)
  agents/             # 10 LLM agents (BaseAgent subclass)
  api/                # 39 REST endpoints
  cli/                # 15 Typer CLI commands (subgroups: style/bible/context/chapter/state/cache)
  compiler/           # Deterministic code (ContextAssembler, StateHealthChecker, etc.)
  llm/                # LLM provider, prompt loader, token counter, validators, cache
  logging.py          # Centralized logging (json/text), request_id tracking
  metrics.py          # Prometheus metrics (5 custom metrics)
  models/             # 15 Pydantic data models
  services/           # Business logic orchestration
  storage/            # File system YAML/MD persistence + SQLite
  db/                 # SQLite database layer
prompts/              # 15 LLM prompt templates (Markdown)
frontend/             # React + Vite + TypeScript + Tailwind
dev_plan/             # 18 detailed phase-plan files (Phase 0–16)
```

## Endpoints

| Path | Description |
|------|-------------|
| `/health` | Health check (DB, storage, LLM key) |
| `/metrics` | Prometheus metrics (5 custom: llm_calls, llm_tokens, llm_latency, task_duration, chapter_status) |
| `POST /api/projects/{id}/chapters/{n}/draft/stream` | SSE streaming draft generation |
| `GET /api/projects/{id}/chapters/{n}/drafts` | List draft versions |
| `POST /api/projects/{id}/chapters/{n}/drafts/{vid}/promote` | Promote draft version |
| `POST /api/projects/{id}/chapters/{n}/review/multi-reader` | Multi-persona reader review |
| `POST /api/projects/{id}/export` | Export project (txt/md/epub/docx) |
| `GET /api/projects/{id}/exports/{task_id}/download` | Download exported file |
| `GET /api/projects/{id}/events` | Project event timeline |
| `POST /api/projects/{id}/share` | Generate share link |

## Key conventions

- **39 API routes** live in `novel_runtime/api/`, project-id is always a path param
- **Agents** extend `BaseAgent`; override `get_prompt_template()`, `process_output()`, optionally `get_validator()`
- **Data models** are Pydantic v2; state files on disk are YAML + Markdown
- **Confg**: env vars prefix `NWR_` (e.g. `NWR_LLM_API_KEY`, `NWR_STORAGE_BASE_PATH`, `NWR_AUTH_TOKEN`, `NWR_LLM_CACHE_ENABLED`)
- **Tests**: mock LLM via `MagicMock`, set `generate_with_usage.return_value` AND `generate.return_value` (both needed, `yaml.safe_load(MagicMock())` hangs)
- **CLI**: `novel style analyze`, `novel bible generate`, `novel context compile`, `novel chapter plan|draft|polish|review|approve`, `novel state update|rollback`, `novel init`, `novel health`, `novel next-suggest`, `novel cache stats|clear`
- **Chapter status flow**: `planned → drafted → reviewed → approved → locked`
- **Prompt templates** in `prompts/` use `{{variable}}` syntax, loaded by `PromptLoader`
- **Logging**: request_id injected via ContextVar, JSON output with `NWR_LOG_FORMAT=json`, text with `NWR_LOG_FORMAT=text`
- **Auth**: Bearer token via `NWR_AUTH_TOKEN` (empty = disabled). `/health`, `/metrics`, `/docs` exempt
- **Rate limit**: default 60/min per IP via slowapi
- **LLM Cache**: SQLite-backed, enabled with `NWR_LLM_CACHE_ENABLED=true`. Cache key = sha256(prompt+system+context+model+temperature)

## Gotchas

- Never pass a dict to `ProjectService.update_project()`; wrap in `ProjectUpdate(...)` first
- Mock provider needs both `.generate.return_value` (str) and `.generate_with_usage.return_value` (tuple[str, dict]) — unset mock creates MagicMock and hangs
- `Approved` chapters are read-only (frozen); `final.md` must exist before `StateService.update_state()`
- The `compiler/` directory contains deterministic code; `agents/` contains LLM-driven code — don't confuse them
- Adding a new API endpoint requires registering in `novel_runtime/main.py` with `app.include_router()`
- Python `datetime.isoformat()` uses `T` separator; SQLite `datetime()` uses space. `task_repo.py` uses `REPLACE(updated_at, 'T', ' ')` for timezone-aware comparisons
- TestClient + lifespan: use `with TestClient(app) as client:` to trigger lifespan events
- Prometheus metrics are registered as module-level objects; use `llm_calls_total.labels(agent, status).inc()` for manual instrumentation
