# AGENTS.md — Novel Writing Runtime

## Commands

```bash
pip install -e ".[dev]"                          # backend deps
uvicorn novel_runtime.main:app --reload          # dev server :8000
pytest tests/ -q                                 # ALL tests (includes e2e → needs LLM!)
pytest tests/unit tests/integration -q           # offline-safe (mock LLM)
pytest tests/e2e/ -q                             # needs LLM_API_KEY (network)
ruff check novel_runtime/ tests/                 # CI lint gate (line-length 120, py310, E501 ignored)
cd frontend && npm install && npm run dev        # frontend :5173 (not :3000!)
cd frontend && npm run build                     # production (tsc + vite)
cd frontend && npm run lint                      # eslint
novel --help                                     # Typer CLI (entry: novel_runtime.cli.main:app)
docker compose up -d                              # full stack
```

## Architecture

- **`novel_runtime/`**: FastAPI backend. `agents/` = LLM-driven. `compiler/` = deterministic. `api/` = routers (register in `main.py` + `api/__init__.py`). `db/` = SQLite. `storage/` = YAML+MD filesystem.
- **`frontend/`**: React 19 + Vite + Zustand + React Query + Tailwind. `@uiw/react-md-editor` (lazy-loaded, 1 MB).
- **Chapter status flow**: `planned → drafted → reviewed → approved → locked`.
- **`novel_projects/`**: live project data on disk (gitignored, Docker volume). Treat as user data.
- **`dev_plan/`** = phase-by-phase specs; **`DEVELOPMENT_PLAN.md`** = full architecture; **`docs/DEPLOY.md`** = deploy guide.

## Tooling

- **Lint**: `ruff check` (CI gate). Config in `pyproject.toml` — line-length 120, target py310, ignores E501. Tests exempt from F401.
- **Format**: `ruff format` (double quotes).
- **Type**: `mypy` via pre-commit (`--ignore-missing-imports --exclude tests/`).
- **Pre-commit**: `.pre-commit-config.yaml` (ruff + ruff-format + mypy).
- **CI**: `.github/workflows/ci.yml` — py3.10, ruff check, pytest, frontend build.

## Env vars

- `LLM_API_KEY` is bare (no prefix). All others use `NWR_` prefix. See `.env.example`.
- `Settings` reads `.env` via `load_dotenv()` in `config.py`. Do NOT add `model_config = SettingsConfigDict(env_file=...)` — collides with bare `LLM_API_KEY` and triggers `extra_forbidden`.
- Public paths exempt from auth: `/health`, `/metrics`, `/docs`, `/openapi.json`, `/api/shared/*`, `/shared/*` (defined in `main.py`).

## Gotchas

- `ProjectService.update_project(id, data)` — `data` must be `ProjectUpdate(...)`, NOT a raw dict.
- Mock LLM provider: set **both** `.generate.return_value` (str) and `.generate_with_usage.return_value` (tuple[str, dict]). Unset mock → MagicMock → hangs.
- `StyleAsset` must be imported at **module level** in `chapters.py`. Inlining it in the `event_stream()` closure causes `NameError`.
- TestClient + lifespan: use `with TestClient(app) as client:` to trigger lifespan events. Smoke tests must set `m.settings` before importing.
- **TestClient 污染 live 数据**: `with TestClient(app) as client:` 触发 `lifespan()`，其中读取的是**模块级** `settings`（默认 `storage_base_path=./novel_projects`），不是 `app.state.settings`。fixture 需在 lifespan 前设置 `app.state.db` + `app.state.settings`，且 `lifespan()` 必须在第一行检查预配置状态跳过默认 init（见 `main.py` lifespan 实现）。
- `datetime.utcnow()` deprecated in 3.12+. Use `datetime.now(timezone.utc)`.
- SQLite stores datetimes with space separator; Python `isoformat()` uses `T`. `task_repo.py` works around this with `REPLACE(updated_at, 'T', ' ')`.
- `DELETE /projects/{id}` = `shutil.rmtree` + DB row. Irreversible.
- `POST /bible/generate` accepts `{direction_id: str, characters: list}`. Backend loads `selected_direction.yaml` automatically.
- `POST /styles/analyze-sync` = synchronous. `POST /styles/analyze` = async (returns `task_id`). Use analyze-sync in wizard; analyze for background jobs.
- SSE stream: `finalize_streamed_draft()` parses `---ANNOTATIONS---` YAML deterministically (no 2nd LLM call). Identical result to sync `POST /draft`.
- Save dedup: `POST /chapters/{n}/content` overwrites same `active_draft` if last save <60s ago. Saving a `reviewed` chapter reverts to `drafted` and renames `review_*.md` → `review_*.md.stale`.
- URL state: chapter selection persisted via `?ch=N&asset=chapter`. MainLayout reads on mount. LeftPanel project dropdown does **not** update URL — use `navigate()`.
- Ctrl+S only fires when the editor container div is focused (guarded by `editorContainerRef.contains(target)`).
- e2e tests (`tests/e2e/`) hit a real LLM via `LLM_API_KEY`. For offline runs use `pytest tests/unit tests/integration -q`.
- `npm run build` runs `tsc -b && vite build` (TypeScript check + production build). A failing `tsc` also fails the build.
- The `novel` CLI entrypoint (Typer) is defined at `novel_runtime/cli/main.py`. Use `novel --help` to discover commands.
- Vite dev server runs on port **5173** (not 3000). The README's `:3000` is the Docker/Nginx production port.
- `api.rawGet('/health')` for root-level endpoints. The `api` client prefixes `/api` automatically, but `/health` and `/metrics` live at the root (no `/api` prefix). Use `api.rawGet()` bypass added in `client.ts`.
- Always write Chinese text directly (actual characters) in `.tsx` files, not `\uXXXX` JS escape sequences. Unicode escapes make code unreadable and fragile in the build pipeline.
- Lazy-loaded CenterPanel components can throw blank pages on import errors. New `ErrorBoundary` wraps the panel — add new lazy components inside it. If `useNavigate` is used in a lazy component, the `import` for `useNavigate` must be at the file top (not inside a lazy `then()` callback).
- Project/chapter auto-select: `App.tsx` auto-selects the first chapter when navigating to a project URL without `?ch=N`. Modifying chapter selection logic must account for both URL param and fallback-to-first behavior.
