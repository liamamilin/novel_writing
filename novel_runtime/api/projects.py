from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi import Request

from novel_runtime.models.project import Project, ProjectCreate, ProjectUpdate
from novel_runtime.services.project_service import ProjectService


router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_service(request: Request) -> ProjectService:
    return ProjectService(
        db=request.app.state.db,
        storage_base=Path(request.app.state.settings.storage_base_path),
    )


@router.post("", response_model=dict)
async def create_project(create: ProjectCreate, svc: ProjectService = Depends(get_service)):
    project = svc.create_project(create)
    return {"project_id": project.project_id, "status": project.status}


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, svc: ProjectService = Depends(get_service)):
    return svc.get_project(project_id)


@router.get("", response_model=list[Project])
async def list_projects(
    status: str | None = Query(None),
    svc: ProjectService = Depends(get_service),
):
    return svc.list_projects(status)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    svc: ProjectService = Depends(get_service),
):
    ok = svc.delete_project(project_id)
    return {"deleted": ok}


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    svc: ProjectService = Depends(get_service),
):
    return svc.update_project(project_id, updates)
