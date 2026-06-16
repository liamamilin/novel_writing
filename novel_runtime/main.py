import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.db.task_repo import TaskRepo
from novel_runtime.exceptions import (
    ChapterNotFoundError,
    InvalidStateTransitionError,
    LLMCallError,
    LLMOutputValidationError,
    NovelRuntimeError,
    ProjectNotFoundError,
    SnapshotNotFoundError,
    StateHealthCriticalError,
    StyleNotSetError,
    TokenBudgetExceededError,
)
from novel_runtime.logging import (
    request_id_var,
    setup_logging,
)
from novel_runtime.metrics import metrics_endpoint

settings = Settings()

EXCEPTION_STATUS_MAP: dict[type[NovelRuntimeError], int] = {
    ProjectNotFoundError: 404,
    ChapterNotFoundError: 404,
    StyleNotSetError: 400,
    InvalidStateTransitionError: 409,
    LLMCallError: 502,
    LLMOutputValidationError: 500,
    TokenBudgetExceededError: 400,
    SnapshotNotFoundError: 404,
    StateHealthCriticalError: 500,
}


logger = logging.getLogger("novel_runtime.main")


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            rid = str(uuid.uuid4())[:8]
            token = request_id_var.set(rid)
            try:
                await self.app(scope, receive, send)
            finally:
                request_id_var.reset(token)
        else:
            await self.app(scope, receive, send)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        status_code = [200]

        async def log_send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, log_send)
        finally:
            duration = (time.monotonic() - start) * 1000
            logger.info(
                "request",
                extra={
                    "method": scope.get("method", "?"),
                    "path": scope.get("path", "?"),
                    "status": status_code[0],
                    "duration_ms": f"{duration:.1f}",
                },
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Respect pre-configured app state (used by test fixtures with TestClient)
    preconfigured_db = getattr(app.state, "db", None)
    preconfigured_settings = getattr(app.state, "settings", None)
    if preconfigured_db is not None and preconfigured_settings is not None:
        logger.info("lifespan: using pre-configured app state (test mode)")
        yield
        return

    setup_logging(settings)

    storage_path = Path(settings.storage_base_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    db = Database(settings.db_path or str(storage_path / "nwr.db"))
    db.init_db()
    app.state.db = db
    app.state.settings = settings

    task_repo = TaskRepo(db)
    orphans = task_repo.list_orphans()
    if orphans:
        for t in orphans:
            task_repo.update_status(t.task_id, "failed", error="Service restart - orphan")
            logger.warning("orphan_failed", extra={"task_id": t.task_id, "project_id": t.project_id})
    else:
        logger.info("no_orphans_found")

    config_issues = []
    if not settings.llm_base_url:
        config_issues.append("NWR_LLM_BASE_URL not set")
    if not settings.llm_model:
        config_issues.append("NWR_LLM_MODEL not set")
    if not os.environ.get(settings.llm_api_key_env, ""):
        config_issues.append(f"{settings.llm_api_key_env} not set")
    if config_issues:
        logger.warning("config_missing", extra={"issues": config_issues})
    else:
        logger.info("config_ok")

    logger.info("server_started", extra={"version": "0.1.0", "storage": str(storage_path)})

    yield


app = FastAPI(
    title="Novel Writing Runtime",
    version="0.1.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = settings.auth_token
        if token:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth.removeprefix("Bearer ") != token:
                    if request.url.path not in ("/health", "/metrics", "/docs", "/openapi.json") and not request.url.path.startswith("/api/shared/") and not request.url.path.startswith("/shared/"):
                        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)


app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

from novel_runtime.api.bible import router as bible_router  # noqa: E402
from novel_runtime.api.chapters import router as chapters_router  # noqa: E402
from novel_runtime.api.context import router as context_router  # noqa: E402
from novel_runtime.api.events import router as events_router  # noqa: E402
from novel_runtime.api.export import router as export_router  # noqa: E402
from novel_runtime.api.hooks import router as hooks_router  # noqa: E402
from novel_runtime.api.projects import router as projects_router  # noqa: E402
from novel_runtime.api.shared import router as shared_router  # noqa: E402
from novel_runtime.api.state import router as state_router  # noqa: E402
from novel_runtime.api.strategy import router as strategy_router  # noqa: E402
from novel_runtime.api.styles import router as styles_router  # noqa: E402
from novel_runtime.api.subplots import router as subplots_router  # noqa: E402
from novel_runtime.api.tasks import router as tasks_router  # noqa: E402

app.include_router(projects_router)
app.include_router(styles_router)
app.include_router(bible_router)
app.include_router(subplots_router)
app.include_router(hooks_router)
app.include_router(strategy_router)
app.include_router(context_router)
app.include_router(chapters_router)
app.include_router(state_router)
app.include_router(export_router)
app.include_router(events_router)
app.include_router(shared_router)
app.include_router(tasks_router)


@app.exception_handler(NovelRuntimeError)
async def novel_runtime_error_handler(request: Request, exc: NovelRuntimeError):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    rid = request_id_var.get()
    logger.error("unhandled_exception", extra={"error": str(exc), "request_id": rid})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": rid},
    )


@app.get("/health")
async def health_check(request: Request):
    checks = {}

    db_ok = False
    try:
        if hasattr(request.app.state, "db"):
            conn = request.app.state.db.get_connection()
            conn.execute("SELECT 1")
            conn.close()
            db_ok = True
    except Exception:
        pass
    checks["database"] = {"status": "ok" if db_ok else "error"}

    storage_ok = Path(settings.storage_base_path).exists()
    checks["storage"] = {"status": "ok" if storage_ok else "error", "path": settings.storage_base_path}

    llm_ok = bool(os.environ.get(settings.llm_api_key_env, ""))
    llm_details = {"key_configured": llm_ok, "base_url": settings.llm_base_url, "model": settings.llm_model}

    llm_latency_ms = None
    llm_probe_ok = False
    if llm_ok and settings.llm_base_url:
        try:
            api_key = os.environ.get(settings.llm_api_key_env, "")
            t0 = time.monotonic()
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{settings.llm_base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            llm_latency_ms = int((time.monotonic() - t0) * 1000)
            llm_probe_ok = r.status_code < 500
            llm_details["latency_ms"] = llm_latency_ms
            llm_details["status_code"] = r.status_code
        except Exception as e:
            llm_details["probe_error"] = str(e)

    checks["llm"] = {
        "status": "ok" if llm_ok and llm_probe_ok else ("degraded" if llm_ok else "error"),
        "detail": llm_details,
    }

    overall = "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded"
    return {"status": overall, "version": "0.1.0", "checks": checks}


@app.get("/metrics", include_in_schema=False)
async def metrics(request: Request):
    return metrics_endpoint(request)
