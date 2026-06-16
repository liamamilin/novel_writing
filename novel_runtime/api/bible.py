from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from novel_runtime.models.bible import BibleUpdateItem
from novel_runtime.models.project import ProjectUpdate
from novel_runtime.services.bible_service import BibleService
from novel_runtime.services.bible_update_service import BibleUpdateService
from novel_runtime.llm.provider import create_provider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.services.project_service import ProjectService


router = APIRouter(prefix="/api/projects/{project_id}/bible", tags=["bible"])


def get_bible_service(request: Request) -> BibleService:
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return BibleService(db, project_svc, provider, loader)


def get_bible_update_service(request: Request) -> BibleUpdateService:
    return BibleUpdateService()


@router.post("/direction")
async def generate_direction_variants(
    project_id: str,
    body: dict,
    svc: BibleService = Depends(get_bible_service),
):
    update_fields = {}
    for field in ["idea", "genre", "target_reader", "core_selling_point"]:
        if body.get(field):
            update_fields[field] = body[field]
    if update_fields:
        svc.project_service.update_project(project_id, ProjectUpdate(**update_fields))
    variants = svc.generate_direction_variants(project_id)
    return {"variants": variants}


@router.post("/characters")
async def generate_characters(
    project_id: str,
    body: dict,
    svc: BibleService = Depends(get_bible_service),
):
    direction_id = body.get("direction_id")
    if direction_id:
        direction_data = svc.load_selected_direction(project_id)
    else:
        direction_data = body.get("direction", {})
    result = svc.generate_character_concepts(project_id, direction_data)
    return result


@router.post("/generate")
async def generate_bible(
    project_id: str,
    body: dict,
    svc: BibleService = Depends(get_bible_service),
):
    direction_id = body.get("direction_id")
    if direction_id:
        direction_data = svc.load_selected_direction(project_id)
    else:
        direction_data = body.get("direction", {})
    characters = body.get("characters", [])
    parts = svc.generate_bible(
        project_id,
        direction_data,
        characters,
    )
    return {"bible_files": parts, "bible_version": svc.get_bible_version(project_id)}


@router.get("")
async def get_bible(
    project_id: str,
    svc: BibleService = Depends(get_bible_service),
):
    return svc.get_bible(project_id)


@router.get("/version")
async def get_bible_version(
    project_id: str,
    svc: BibleService = Depends(get_bible_service),
):
    version = svc.get_bible_version(project_id)
    return {"version": version}


@router.get("/update-proposal")
async def get_bible_update_proposal(
    project_id: str,
    request: Request,
    svc: BibleUpdateService = Depends(get_bible_update_service),
):
    project_svc = ProjectService(
        request.app.state.db,
        Path(request.app.state.settings.storage_base_path),
    )
    project_path = project_svc.get_project_path(project_id)
    proposal = svc.detect_update_need(project_path, [], [])
    return {"proposal": proposal.model_dump() if proposal else None}


@router.post("/update")
async def apply_bible_update(
    project_id: str,
    body: dict,
    request: Request,
    svc: BibleUpdateService = Depends(get_bible_update_service),
):
    project_svc = ProjectService(
        request.app.state.db,
        Path(request.app.state.settings.storage_base_path),
    )
    project_path = project_svc.get_project_path(project_id)
    items = [BibleUpdateItem(**item) for item in body.get("updates", [])]
    from novel_runtime.models.bible import BibleUpdateProposal
    proposal = BibleUpdateProposal(
        project_id=project_id,
        trigger_chapter=body.get("trigger_chapter", ""),
        items=items,
    )
    result = svc.apply_update(project_path, proposal)
    return result
