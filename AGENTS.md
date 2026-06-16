# AGENTS.md — Novel Writing Runtime

## Commands

```bash
pip install -e ".[dev]"                          # backend deps
uvicorn novel_runtime.main:app --reload          # dev server :8000
pytest tests/ -q                                 # 122 baseline
pytest tests/unit/ -q                             # unit only
pytest tests/integration/ -q                      # integration (mock LLM)
cd frontend && npm install && npm run dev         # frontend :3000
cd frontend && npm run build                      # production (tsc + vite)
docker compose up -d                              # full stack
```

## Architecture

- **`novel_runtime/`**: FastAPI backend. `agents/` = LLM-driven. `compiler/` = deterministic. `api/` = routers (register in `main.py` + `api/__init__.py`). `db/` = SQLite. `storage/` = YAML+MD filesystem.
- **`frontend/`**: React 19 + Vite + Zustand + React Query + Tailwind. `@uiw/react-md-editor` (lazy-loaded, 1 MB).
- **Chapter status flow**: `planned → drafted → reviewed → approved → locked`.

## Gotchas

- `ProjectService.update_project(id, data)` — `data` must be `ProjectUpdate(...)`, NOT a raw dict.
- Mock LLM provider: set **both** `.generate.return_value` (str) and `.generate_with_usage.return_value` (tuple[str, dict]). Unset mock → MagicMock → hangs.
- `StyleAsset` must be imported at **module level** in `chapters.py`. Inlining it in the `event_stream()` closure causes `NameError`.
- TestClient + lifespan: use `with TestClient(app) as client:` to trigger lifespan events. Smoke tests must set `m.settings` before importing.
- `.env`: use `load_dotenv()` in `config.py` (top-level). Do NOT use pydantic's `env_file=` — it triggers `extra_forbidden` with `LLM_API_KEY`.
- `datetime.utcnow()` deprecated in 3.12+. Use `datetime.now(timezone.utc)`.
- SQLite stores datetimes with space separator; Python `isoformat()` uses `T`. `task_repo.py` works around this with `REPLACE(updated_at, 'T', ' ')`.
- AuthMiddleware: add new public paths to the exemption list in `main.py`.
- `DELETE /projects/{id}` = `shutil.rmtree` + DB row. Irreversible.
- `POST /bible/generate` accepts `{direction_id: str, characters: list}`. Backend loads `selected_direction.yaml` automatically.
- `POST /styles/analyze-sync` = synchronous. `POST /styles/analyze` = async (returns `task_id`). Use analyze-sync in wizard; analyze for background jobs.
- SSE stream: `finalize_streamed_draft()` parses `---ANNOTATIONS---` YAML deterministically (no 2nd LLM call). Identical result to sync `POST /draft`.
- Save dedup: `POST /chapters/{n}/content` overwrites same `active_draft` if last save <60s ago. Saving a `reviewed` chapter reverts to `drafted` and renames `review_*.md` → `review_*.md.stale`.
- URL state: chapter selection persisted via `?ch=N&asset=chapter`. MainLayout reads on mount. LeftPanel project dropdown does **not** update URL — use `navigate()`.
- Ctrl+S only fires when the editor container div is focused (guarded by `editorContainerRef.contains(target)`).
