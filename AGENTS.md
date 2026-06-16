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
  api/                # 63 REST endpoints (59 REST + 4 docs)
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
- `DELETE /projects/{id}` removes both DB row + filesystem tree (`shutil.rmtree`) — irreversible
- `DELETE /subplots/{id}` cleans both individual YAML + registry entry
- `POST /styles/analyze-sync` is the synchronous alternative to `POST /styles/analyze` (async + task_id) — use analyze-sync in ProjectCreate wizard, analyze for large async operations
- AuthMiddleware exempt list now includes `/shared/` (frontend reader) — update when adding new public paths
- `generate_bible` now accepts `{direction_id, characters}` instead of `{direction: dict}` — frontend sends string direction_id; backend loads `selected_direction.yaml`
- `generate_characters` accepts `{direction_id}` — backend loads direction file automatically
- `GET /chapters/{ch}/reviews` returns raw review markdown content + fix_instructions; ReviewTabs on frontend does basic section parsing
- Since Batch A: ProjectList has 🗑 delete; ExportModal has chapter_range + includeTitle; TokenModal pops on 401
- Since Batch H: API client has AbortSignal timeout (60s GET / 120s POST); toast auto-clears; HealthBadge no longer navigates away

## 63 API Endpoints (59 REST + 4 docs) — v3

| Module | Count | Endpoints |
|--------|-------|-----------|
| Projects | 5 | POST/GET list, GET/PUT/DELETE by id |
| Styles | 6 | GET list, POST analyze/analyze-sync, POST sample, GET by id, POST test-paragraph |
| Tasks | 1 | GET task by id |
| Bible | 7 | GET bible, POST direction/characters/generate/update, GET update-proposal/version |
| Context | 1 | POST compile |
| Chapters | **15** | GET list, POST plan/draft/stream/polish/review/multi-reader/approve, GET drafts/draft detail/content/reviews, POST content/promote, POST state/update |
| State | 2 | POST rollback, GET snapshots |
| Export | 2 | POST export, GET download |
| Subplots | 5 | GET/POST list, GET suggestions, PUT/DELETE by id |
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
