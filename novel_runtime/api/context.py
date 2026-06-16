from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from novel_runtime.llm.provider import create_provider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.services.context_service import ContextService
from novel_runtime.services.project_service import ProjectService


router = APIRouter(prefix="/api/projects/{project_id}/context", tags=["context"])


def get_service(request: Request) -> ContextService:
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return ContextService(project_svc, provider, loader)


@router.post("/compile")
async def compile_context(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: ContextService = Depends(get_service),
):
    result = svc.compile_context(
        project_id, chapter_number,
        body.get("chapter_goal", ""),
    )
    return result
