from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from novel_runtime.storage.chapter_storage import load_chapter_file
from novel_runtime.storage.project_storage import ProjectStorage
from novel_runtime.storage.share_token_storage import ShareTokenStorage

router = APIRouter(prefix="/api/shared", tags=["shared"])


def _get_project_id(token: str, request: Request) -> str:
    base = Path(request.app.state.settings.storage_base_path)
    pid = ShareTokenStorage(base).resolve(token)
    if pid is None:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    return pid


@router.get("/{token}")
async def shared_project(token: str, request: Request):
    pid = _get_project_id(token, request)
    project = ProjectStorage(Path(request.app.state.settings.storage_base_path)).load_project(pid)
    return project.model_dump(mode="json", exclude_none=True)


@router.get("/{token}/chapters")
async def shared_chapters(token: str, request: Request):
    pid = _get_project_id(token, request)
    base = Path(request.app.state.settings.storage_base_path)
    chapters = ProjectStorage(base).list_chapters(pid)
    return {"chapters": [c.model_dump(mode="json", exclude_none=True) for c in chapters]}


@router.get("/{token}/chapters/{chapter_number}")
async def shared_chapter_detail(token: str, chapter_number: int, request: Request, file_type: str = "draft"):
    pid = _get_project_id(token, request)
    base = Path(request.app.state.settings.storage_base_path)
    project = ProjectStorage(base).load_project(pid)
    try:
        content = load_chapter_file(base / pid, chapter_number, file_type)
    except FileNotFoundError:
        raise HTTPException(404, f"Chapter {chapter_number} file not found")
    return {"project_id": pid, "project_name": project.project_name, "chapter_number": chapter_number, "file_type": file_type, "content": content}
