from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from novel_runtime.services.hook_service import HookService
from novel_runtime.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects/{project_id}/hooks", tags=["hooks"])


def get_service(request: Request) -> HookService:
    settings = request.app.state.settings
    from pathlib import Path
    return HookService(ProjectService(request.app.state.db, Path(settings.storage_base_path)))


@router.get("")
async def list_hooks(
    project_id: str, status: str | None = None,
    hook_type: str | None = None, priority: str | None = None,
    svc: HookService = Depends(get_service),
):
    return svc.list_hooks(project_id, status, hook_type, priority)


@router.post("")
async def add_hook(
    project_id: str, body: dict,
    svc: HookService = Depends(get_service),
):
    hook = svc.add_hook(
        project_id, body.get("content", ""), body.get("source_chapter", ""),
        body.get("type", "mystery"), body.get("priority", "medium"),
        body.get("reader_patience", 8), body.get("related_characters"),
    )
    return hook


@router.put("/{hook_id}")
async def update_hook(
    project_id: str, hook_id: str, body: dict,
    svc: HookService = Depends(get_service),
):
    return svc.update_hook(project_id, hook_id, body)


@router.post("/{hook_id}/trigger")
async def trigger_hook(
    project_id: str, hook_id: str,
    svc: HookService = Depends(get_service),
):
    return svc.trigger_hook(project_id, hook_id)


@router.post("/{hook_id}/resolve")
async def resolve_hook(
    project_id: str, hook_id: str, body: dict,
    svc: HookService = Depends(get_service),
):
    return svc.resolve_hook(project_id, hook_id, body.get("resolution", ""), body.get("chapter", ""))


@router.get("/chapter/{chapter_number}")
async def chapter_hooks(
    project_id: str, chapter_number: int,
    svc: HookService = Depends(get_service),
):
    return svc.get_chapter_hooks(project_id, chapter_number)
