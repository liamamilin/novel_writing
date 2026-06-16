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
pytest tests/ -q                           # all tests (122 passed)
pytest tests/unit/ -q                      # unit only
pytest tests/integration/ -q               # integration (mock LLM)
pytest tests/e2e/ -q                       # e2e (requires LLM_API_KEY)
cd frontend && npm run build               # frontend build (0 error)
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
  api/                # 57 REST endpoints
  cli/                # 15 Typer CLI commands
  compiler/           # Deterministic code (ContextAssembler, StateHealthChecker)
  llm/                # LLM provider, prompt loader, token counter, validators, cache
  logging.py          # Centralized logging (json/text), request_id tracking
  metrics.py          # Prometheus metrics (5 custom metrics)
  models/             # 15 Pydantic data models
  services/           # Business logic orchestration
  storage/            # File system YAML/MD persistence
  db/                 # SQLite database layer
prompts/              # 15 LLM prompt templates (Markdown)
frontend/             # React 19 + Vite + TypeScript + Tailwind
grafana/              # Dashboard JSON + alert rules
dev_plan/             # 18 detailed phase-plan files
docs/                 # Deployment guide
```

## 57 API Endpoints (53 REST + 4 docs)

| Module | Count | Endpoints |
|--------|-------|-----------|
| Projects | 4 | POST/GET list, GET/PUT by id |
| Styles | 5 | GET list, POST analyze, POST sample, GET by id, POST test-paragraph |
| Bible | 7 | GET bible, POST direction/characters/generate/update, GET update-proposal/version |
| Context | 1 | POST compile |
| Chapters | 12 | GET list, POST plan/draft/stream/polish/review/multi-reader/approve, GET drafts/draft detail, POST promote, POST state/update |
| State | 2 | POST rollback, GET snapshots |
| Export | 2 | POST export, GET download |
| Subplots | 4 | GET/POST list, GET suggestions, PUT by id |
| Hooks | 6 | GET/POST list, GET by chapter, PUT by id, POST resolve/trigger |
| Strategy | 3 | GET/PUT, POST reset |
| Events | 1 | GET timeline |
| Share | 1 | POST share link |
| Shared | 3 | GET token/chapters/chapter detail (no auth) |
| System | 2 | GET health (LLM latency probe), GET metrics |

## Key conventions

- **57 API routes** live in `novel_runtime/api/`, project-id is always a path param
- **Agents** extend `BaseAgent`; override `get_prompt_template()`, `process_output()`, optionally `get_validator()`
- **Data models** are Pydantic v2; state files on disk are YAML + Markdown
- **Config**: env vars prefix `NWR_`; `LLM_API_KEY` (no prefix) loaded via `load_dotenv()` → `os.environ`
- **Tests**: mock LLM via `MagicMock`, set both `.generate.return_value` and `.generate_with_usage.return_value`
- **CLI**: `novel style analyze`, `novel bible generate`, `novel context compile`, `novel chapter plan|draft|polish|review|approve`, `novel state update|rollback`, `novel init`, `novel health`, `novel next-suggest`, `novel cache stats|clear`
- **Chapter status flow**: `planned → drafted → reviewed → approved → locked`
- **Prompt templates** in `prompts/` use `{{variable}}` syntax, loaded by `PromptLoader`
- **Logging**: request_id via ContextVar; JSON with `NWR_LOG_FORMAT=json`, text with `NWR_LOG_FORMAT=text`
- **Auth**: Bearer token via `NWR_AUTH_TOKEN` (empty = disabled). `/health`, `/metrics`, `/docs`, `/api/shared/` exempt
- **Rate limit**: default 60/min per IP via slowapi
- **LLM Cache**: SQLite-backed, enabled with `NWR_LLM_CACHE_ENABLED=true`. Key = sha256(prompt+system+context+model+temperature)
- **Monitoring**: 5 Prometheus metrics (`nwr_llm_calls_total`, `nwr_llm_tokens_total`, `nwr_llm_latency_seconds`, `nwr_task_duration_seconds`, `nwr_chapter_status_count`) + Grafana dashboard + alert rules

## Gotchas

- Never pass a dict to `ProjectService.update_project()`; wrap in `ProjectUpdate(...)` first
- Mock provider needs both `.generate.return_value` (str) and `.generate_with_usage.return_value` (tuple[str, str]) — unset mock creates MagicMock and hangs
- `Approved` chapters are read-only (frozen); `final.md` must exist before `StateService.update_state()`
- The `compiler/` directory contains deterministic code; `agents/` contains LLM-driven code — don't confuse them
- Adding a new API endpoint requires registering in `novel_runtime/main.py` with `app.include_router()`, adding to `api/__init__.py`, and adding to the AuthMiddleware exemption list if needed
- Python `datetime.isoformat()` uses `T` separator; SQLite `datetime()` uses space. `task_repo.py` uses `REPLACE(updated_at, 'T', ' ')` for timezone-aware comparisons
- TestClient + lifespan: use `with TestClient(app) as client:` to trigger lifespan events; smoke tests must set `m.settings` before importing
- Prometheus metrics are registered as module-level objects; use `llm_calls_total.labels(agent, status).inc()` for manual instrumentation
- `datetime.utcnow()` is deprecated in Python 3.12+; use `datetime.now(timezone.utc)` instead
- `StyleAsset()` is imported at module level in `chapters.py` — do NOT inline-import it inside the `event_stream()` closure to avoid NameError
- `api/__init__.py` must export all routers — missing entries cause confusing import errors
- `.env` must use `load_dotenv()` (top of `config.py`) instead of pydantic's `env_file=` to avoid `extra_forbidden` error with `LLM_API_KEY`

## 57 API Endpoints (53 REST + 4 docs) — v2

| Module | Count | Endpoints |
|--------|-------|-----------|
| Projects | 4 | POST/GET list, GET/PUT by id |
| Styles | 5 | GET list, POST analyze, POST sample, GET by id, POST test-paragraph |
| Bible | 7 | GET bible, POST direction/characters/generate/update, GET update-proposal/version |
| Context | 1 | POST compile |
| Chapters | **14** | GET list, POST plan/draft/stream/polish/review/multi-reader/approve, GET drafts/draft detail/content, POST content/promote, POST state/update |
| State | 2 | POST rollback, GET snapshots |
| Export | 2 | POST export, GET download |
| Subplots | 4 | GET/POST list, GET suggestions, PUT by id |
| Hooks | 6 | GET/POST list, GET by chapter, PUT by id, POST resolve/trigger |
| Strategy | 3 | GET/PUT, POST reset |
| Events | 1 | GET timeline |
| Share | 1 | POST share link |
| Shared | 3 | GET token/chapters/chapter detail (no auth) |
| System | 2 | GET health (LLM latency probe), GET metrics |

### Chapter API detail
- `GET /{chapter_number}/content` — returns active draft content (or final for approved/locked)
- `POST /{chapter_number}/content` — save user-edited text as new draft version; deduplicates saves < 60s into same version; if status=reviewed, reverts to drafted and marks reviews stale

## SSE / Stream gotchas

- SSE flow: `token` events → `done` event with `draft_id`. On done, backend auto-calls `ChapterService.finalize_streamed_draft()` which:
  1. Parses the `---ANNOTATIONS---` YAML section (same format as sync draft) — no extra LLM call
  2. Writes `state_annotations.yaml`
  3. Runs contract check (deterministic substring match)
  4. Sets chapter status to `drafted`
- Streamed drafts are **identical** to sync `POST /draft` in terms of files produced
- Cancelling stream mid-way loses partial content (no draft saved)
- Stream disable chapter switching (ChapterList blocks onClick while `isStreaming`)

## URL state / refresh

- Chapter selection is persisted via URL query: `/project/:id?ch=3&asset=chapter`
- On refresh, `MainLayout` reads `?ch` from URL and restores `currentChapter` + `selectedAsset`
- `ProjectCreate` navigates to `?ch=1&asset=chapter` after Bible generation
- `LeftPanel` project dropdown auto-loads from `useProjectStore.loadProjects()` on MainLayout mount

## Save / dirty state

- `POST /content` deduplicates: if last save was < 60s ago, overwrites same `active_draft_id` instead of creating new version
- Saving a `reviewed` chapter reverts to `drafted` and renames `review_*.md` → `review_*.md.stale`
- Editor tracks `isDirty` (content !== loadedContent); triggers `beforeunload` warning if dirty
- Ctrl+S only fires when the editor container is focused (not globally)
