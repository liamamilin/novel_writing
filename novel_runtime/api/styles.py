from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from novel_runtime.models.style import StyleAsset, CharacterVoice
from novel_runtime.services.style_service import StyleService


router = APIRouter(prefix="/api/projects/{project_id}/styles", tags=["styles"])


def get_style_service(request: Request) -> StyleService:
    from novel_runtime.config import Settings
    from novel_runtime.llm.provider import create_provider
    from novel_runtime.llm.prompt_loader import PromptLoader
    from novel_runtime.services.project_service import ProjectService
    from pathlib import Path

    settings: Settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader(Path("prompts"))
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return StyleService(db, project_svc, provider, loader, settings)


@router.post("/style-samples")
async def upload_sample(
    project_id: str,
    body: dict,
    svc: StyleService = Depends(get_style_service),
):
    sample_id = svc.upload_sample(project_id, body.get("sample_name", ""), body.get("text", ""))
    return {"sample_id": sample_id, "status": "uploaded"}


@router.post("/analyze")
async def analyze_style(
    project_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
    svc: StyleService = Depends(get_style_service),
):
    task = svc.analyze_style_async(
        project_id,
        body.get("sample_ids", []),
        body.get("style_name", ""),
        background_tasks,
        body.get("run_adversarial", True),
    )
    return {"task_id": task.task_id, "status": "pending"}


@router.get("/{style_id}")
async def get_style(
    project_id: str,
    style_id: str,
    svc: StyleService = Depends(get_style_service),
):
    return svc.get_style(project_id, style_id)


@router.get("")
async def list_styles(
    project_id: str,
    svc: StyleService = Depends(get_style_service),
):
    return svc.list_styles(project_id)


@router.post("/{style_id}/test-paragraph")
async def test_paragraph(
    project_id: str,
    style_id: str,
    body: dict,
    svc: StyleService = Depends(get_style_service),
):
    paragraph = svc.generate_test_paragraph(project_id, style_id, body.get("topic", "一场激烈的拍卖会"))
    return {"paragraph": paragraph}
