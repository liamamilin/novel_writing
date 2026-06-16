from __future__ import annotations
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request

from novel_runtime.storage.event_storage import EventStorage
from novel_runtime.storage.share_token_storage import ShareTokenStorage


router = APIRouter(prefix="/api/projects/{project_id}", tags=["events"])


@router.get("/events")
async def list_events(
    project_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
):
    settings = request.app.state.settings
    storage = EventStorage(Path(settings.storage_base_path))
    events = storage.list_events(project_id, limit, offset)
    return {"events": [e.model_dump(mode="json") for e in events], "limit": limit, "offset": offset}


@router.post("/share")
async def share_project(
    project_id: str,
    body: dict,
    request: Request,
):
    token = f"share_{uuid4().hex[:16]}"
    base = Path(request.app.state.settings.storage_base_path)
    EventStorage(base).record(project_id, "share_link_created", actor=body.get("actor", "user"), details={"token": token})
    ShareTokenStorage(base).save(token, project_id)
    return {"share_token": token, "url": f"/shared/{token}"}
