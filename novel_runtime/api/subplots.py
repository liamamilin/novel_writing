from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.subplot_service import SubplotService

router = APIRouter(prefix="/api/projects/{project_id}/subplots", tags=["subplots"])


def get_service(request: Request) -> SubplotService:
    settings = request.app.state.settings
    from pathlib import Path
    return SubplotService(ProjectService(request.app.state.db, Path(settings.storage_base_path)))


@router.get("")
async def list_subplots(
    project_id: str, status: str | None = None,
    svc: SubplotService = Depends(get_service),
):
    return svc.list_subplots(project_id, status)


@router.post("")
async def create_subplot(
    project_id: str, body: dict,
    svc: SubplotService = Depends(get_service),
):
    sp = svc.create_subplot(
        project_id, body.get("name", ""), body.get("type", "main_plot"),
        body.get("involved_characters"),
    )
    return sp


@router.put("/{subplot_id}")
async def update_subplot(
    project_id: str, subplot_id: str, body: dict,
    svc: SubplotService = Depends(get_service),
):
    return svc.update_subplot(project_id, subplot_id, body)


@router.delete("/{subplot_id}")
async def delete_subplot(
    project_id: str, subplot_id: str,
    svc: SubplotService = Depends(get_service),
):
    ok = svc.delete_subplot(project_id, subplot_id)
    return {"deleted": ok}


@router.get("/suggestions")
async def suggest_subplots(
    project_id: str, chapter_number: int,
    svc: SubplotService = Depends(get_service),
):
    return svc.suggest_subplot_allocation(project_id, chapter_number)
