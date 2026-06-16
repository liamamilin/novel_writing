from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request

from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.llm.provider import create_provider
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.state_service import StateService
from novel_runtime.storage.snapshot_storage import SnapshotManager

router = APIRouter(prefix="/api/projects/{project_id}", tags=["state"])


def get_service(request: Request) -> StateService:
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return StateService(project_svc, provider, loader)


@router.post("/chapters/{chapter_number}/approve")
async def approve_chapter(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: StateService = Depends(get_service),
):
    final_text = body.get("final_text", "")
    project_path = svc.project_service.get_project_path(project_id)
    chapter_dir = project_path / "chapters" / f"chapter_{chapter_number:03d}"

    final_path = chapter_dir / "final.md"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(final_text, encoding="utf-8")

    from novel_runtime.storage.chapter_storage import freeze_chapter
    freeze_chapter(project_path, chapter_number)

    from novel_runtime.models.project import ProjectUpdate
    svc.project_service.update_project(project_id, ProjectUpdate(
        current_chapter_id=f"chapter_{chapter_number:03d}",
    ))

    chapter = svc.project_service.get_chapter(project_id, chapter_number)
    chapter.status = "approved"
    chapter.final_path = str(final_path)

    from novel_runtime.storage.project_storage import ProjectStorage
    ProjectStorage(svc.project_service.storage_base).save_chapter(
        svc.project_service.get_project(project_id), chapter,
    )

    try:
        state_result = svc.update_state(project_id, chapter_number)
        return {
            "chapter_id": f"chapter_{chapter_number:03d}",
            "status": "approved",
            "frozen": True,
            "state_update": state_result,
        }
    except Exception as e:
        from novel_runtime.storage.chapter_storage import unfreeze_chapter
        unfreeze_chapter(project_path, chapter_number)
        chapter.status = "reviewed"
        final_path.unlink(missing_ok=True)
        raise e


@router.post("/chapters/{chapter_number}/state/update")
async def update_state(
    project_id: str,
    chapter_number: int,
    svc: StateService = Depends(get_service),
):
    result = svc.update_state(project_id, chapter_number)
    return result


@router.get("/state/snapshots")
async def list_snapshots(
    project_id: str,
    svc: StateService = Depends(get_service),
):
    project_path = svc.project_service.get_project_path(project_id)
    mgr = SnapshotManager()
    chapter_numbers = mgr.list_snapshots(project_path)
    return [
        {
            "snapshot_id": f"snapshot_after_chapter_{ch:03d}",
            "chapter_number": ch,
        }
        for ch in chapter_numbers
    ]


@router.post("/state/rollback")
async def rollback_state(
    project_id: str,
    body: dict,
    svc: StateService = Depends(get_service),
):
    target = body.get("target_chapter", 0)
    result = svc.rollback_state(project_id, target)
    return result
