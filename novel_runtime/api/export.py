from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from novel_runtime.services.export_service import ExportService
from novel_runtime.services.project_service import ProjectService
from novel_runtime.db.database import Database


router = APIRouter(prefix="/api/projects/{project_id}", tags=["export"])


@router.post("/export")
async def export_project(
    project_id: str,
    body: dict,
    request: Request,
):
    settings = request.app.state.settings
    db = request.app.state.db
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    svc = ExportService(project_svc)
    fmt = body.get("format", "txt")
    chapter_range = body.get("chapter_range")
    include_title = body.get("include_title", True)

    format_map = {
        "txt": svc.export_txt,
        "md": svc.export_md,
        "epub": svc.export_epub,
        "docx": svc.export_docx,
    }
    exporter = format_map.get(fmt)
    if not exporter:
        from fastapi import HTTPException
        raise HTTPException(400, f"Unsupported format: {fmt}")
    path = exporter(project_id, chapter_range, include_title)
    return {"task_id": path.stem, "format": fmt, "path": str(path)}


@router.get("/exports/{task_id}/download")
async def download_export(
    project_id: str,
    task_id: str,
    request: Request,
):
    settings = request.app.state.settings
    export_dir = Path(settings.storage_base_path) / "exports"
    for ext in ("txt", "md", "epub", "docx"):
        p = export_dir / f"{task_id}.{ext}"
        if p.exists():
            media_map = {
                "txt": "text/plain",
                "md": "text/markdown",
                "epub": "application/epub+zip",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
            return FileResponse(str(p), media_type=media_map.get(ext, "application/octet-stream"), filename=f"{task_id}{ext}")
    from fastapi import HTTPException
    raise HTTPException(404, "Export not found")
