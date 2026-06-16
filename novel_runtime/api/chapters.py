from __future__ import annotations
import json as json_mod
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse

from novel_runtime.llm.provider import create_provider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.models.style import StyleAsset
from novel_runtime.services.chapter_service import ChapterService
from novel_runtime.services.context_service import ContextService
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.review_service import ReviewService


router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


def get_services(request: Request):
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return settings, provider, loader, project_svc, db


def get_chapter_service(request: Request) -> ChapterService:
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    ctx_svc = ContextService(project_svc, provider, loader)
    return ChapterService(project_svc, ctx_svc, provider, loader)


def get_project_service(request: Request) -> ProjectService:
    settings = request.app.state.settings
    db = request.app.state.db
    return ProjectService(db, Path(settings.storage_base_path))


def get_review_service(request: Request) -> ReviewService:
    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    return ReviewService(project_svc, provider, loader)


@router.get("")
async def list_chapters(
    project_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    chapters = svc.list_chapters(project_id)
    return [
        {
            "chapter_number": c.chapter_number,
            "chapter_id": c.chapter_id,
            "title": c.title,
            "status": c.status,
            "rhythm_type": c.rhythm_type,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in chapters
    ]


@router.post("/{chapter_number}/plan")
async def generate_plan(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: ChapterService = Depends(get_chapter_service),
):
    return svc.generate_plan(project_id, chapter_number, body.get("chapter_goal", ""))


@router.post("/{chapter_number}/draft")
async def generate_draft(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: ChapterService = Depends(get_chapter_service),
):
    return svc.generate_draft(project_id, chapter_number)


@router.post("/{chapter_number}/draft/stream")
async def generate_draft_stream(
    project_id: str,
    chapter_number: int,
    body: dict,
    request: Request,
):
    settings, provider, loader, project_svc, _ = get_services(request)
    project_path = project_svc.get_project_path(project_id)
    project = project_svc.get_project(project_id)

    from novel_runtime.storage.chapter_storage import load_chapter_file
    from novel_runtime.exceptions import InvalidStateTransitionError

    def event_stream():
        try:
            chapter = project_svc.get_chapter(project_id, chapter_number)
        except Exception as e:
            yield f"data: {json_mod.dumps({'error': str(e)})}\n\n"
            return

        if chapter.status != "planned":
            yield f"data: {json_mod.dumps({'error': f'Chapter {chapter_number} is {chapter.status}'})}\n\n"
            return

        try:
            context_pack = load_chapter_file(project_path, chapter_number, "context_pack")
            chapter_plan = load_chapter_file(project_path, chapter_number, "plan")
        except FileNotFoundError as e:
            yield f"data: {json_mod.dumps({'error': str(e)})}\n\n"
            return

        from novel_runtime.storage import style_storage, state_storage
        try:
            style = style_storage.load_style_asset(project_path, project.default_style_id) if project.default_style_id else StyleAsset()
        except FileNotFoundError:
            style = StyleAsset()

        characters = state_storage.load_characters(project_path)
        voices = []
        for c in characters:
            if c.voice_id:
                try:
                    voice = style_storage.load_character_voice(project_path, c.voice_id)
                    voices.append(voice)
                except FileNotFoundError:
                    pass
        all_voices = voices + style_storage.list_character_voices(project_path)
        unique_voices = {v.voice_id: v for v in all_voices}.values() if all_voices else []

        import yaml

        style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False)
        voice_params = "\n".join(
            f"- {v.character_name}: {v.speech_patterns}" for v in unique_voices
        )

        write_prompt = loader.load("chapter_write", {
            "context_pack": context_pack,
            "chapter_plan": chapter_plan,
            "style_params": style_params,
            "voice_params": voice_params,
            "contract_promises": "",
            "contract_constraints": "",
        })

        full_text = ""
        try:
            for chunk in provider.generate_stream(write_prompt):
                full_text += chunk
                yield f"data: {json_mod.dumps({'token': chunk})}\n\n"

            # auto-save draft on successful completion
            from novel_runtime.storage.chapter_storage import save_draft_version
            from novel_runtime.storage.project_storage import ProjectStorage
            chapter.draft_count += 1
            current_draft_id = chapter.draft_count
            save_draft_version(project_path, chapter_number, current_draft_id, full_text)
            chapter.active_draft_id = current_draft_id
            chapter.draft_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "drafts" / f"draft_v{current_draft_id}.md")
            chapter.status = "drafted"
            ProjectStorage(Path(settings.storage_base_path)).save_chapter(project, chapter)

            yield f"data: {json_mod.dumps({'done': True, 'full': full_text, 'draft_id': current_draft_id})}\n\n"
        except Exception as e:
            yield f"data: {json_mod.dumps({'error': str(e), 'partial': full_text})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{chapter_number}/polish")
async def polish_draft(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: ChapterService = Depends(get_chapter_service),
):
    return svc.polish_draft(project_id, chapter_number)


@router.post("/{chapter_number}/review")
async def review_chapter(
    project_id: str,
    chapter_number: int,
    body: dict,
    svc: ReviewService = Depends(get_review_service),
):
    return svc.review_chapter(
        project_id,
        chapter_number,
        body.get("review_types", ["continuity", "quality"]),
    )


@router.get("/{chapter_number}/content")
async def get_content(
    project_id: str,
    chapter_number: int,
    request: Request,
):
    """Get the current active content for a chapter: active draft, final, or empty."""
    settings = request.app.state.settings
    from novel_runtime.services.project_service import ProjectService
    from novel_runtime.db.database import Database
    from pathlib import Path

    db = request.app.state.db
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    project_path = project_svc.get_project_path(project_id)
    chapter = project_svc.get_chapter(project_id, chapter_number)

    # approved/locked → return final.md
    if chapter.status in ("approved", "locked"):
        from novel_runtime.storage.chapter_storage import load_chapter_file
        try:
            content = load_chapter_file(project_path, chapter_number, "final")
            return {"content": content, "source": "final"}
        except FileNotFoundError:
            return {"content": "", "source": "final"}

    # has active draft → return it
    if chapter.active_draft_id > 0:
        from novel_runtime.storage.chapter_storage import load_draft_version
        try:
            content = load_draft_version(project_path, chapter_number, chapter.active_draft_id)
            return {"content": content, "source": "draft", "draft_id": chapter.active_draft_id}
        except FileNotFoundError:
            pass

    # try draft.md as fallback
    from novel_runtime.storage.chapter_storage import load_chapter_file
    try:
        content = load_chapter_file(project_path, chapter_number, "draft")
        return {"content": content, "source": "draft_file"}
    except FileNotFoundError:
        return {"content": "", "source": "none"}


@router.post("/{chapter_number}/content")
async def save_content(
    project_id: str,
    chapter_number: int,
    body: dict,
    request: Request,
):
    """Save user-edited content as a new draft version."""
    settings = request.app.state.settings
    from novel_runtime.services.project_service import ProjectService
    from novel_runtime.db.database import Database
    from pathlib import Path
    from novel_runtime.storage.chapter_storage import save_draft_version
    from novel_runtime.storage.project_storage import ProjectStorage

    db = request.app.state.db
    content = body.get("content", "")
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    project_path = project_svc.get_project_path(project_id)
    project = project_svc.get_project(project_id)
    chapter = project_svc.get_chapter(project_id, chapter_number)

    if chapter.status in ("approved", "locked"):
        from fastapi import HTTPException
        raise HTTPException(400, "Cannot edit a locked/approved chapter")

    chapter.draft_count += 1
    current_draft_id = chapter.draft_count
    save_draft_version(project_path, chapter_number, current_draft_id, content)
    chapter.active_draft_id = current_draft_id
    chapter.draft_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "drafts" / f"draft_v{current_draft_id}.md")

    if chapter.status == "planned":
        chapter.status = "drafted"

    ProjectStorage(Path(settings.storage_base_path)).save_chapter(project, chapter)

    return {"draft_id": current_draft_id, "draft_count": chapter.draft_count, "status": chapter.status}


@router.get("/{chapter_number}/drafts")
async def list_drafts(
    project_id: str,
    chapter_number: int,
    request: Request,
):
    settings = request.app.state.settings
    _, _, _, project_svc, _ = get_services(request)
    project_path = project_svc.get_project_path(project_id)
    from novel_runtime.storage.chapter_storage import list_drafts as _list_drafts
    chapter = project_svc.get_chapter(project_id, chapter_number)
    drafts = _list_drafts(project_path, chapter_number)
    return {"drafts": drafts, "active_draft_id": chapter.active_draft_id, "draft_count": chapter.draft_count}


@router.get("/{chapter_number}/drafts/{draft_id}")
async def get_draft_content(
    project_id: str,
    chapter_number: int,
    draft_id: int,
    request: Request,
):
    _, _, _, project_svc, _ = get_services(request)
    project_path = project_svc.get_project_path(project_id)
    from novel_runtime.storage.chapter_storage import load_draft_version
    try:
        content = load_draft_version(project_path, chapter_number, draft_id)
    except FileNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(404, f"Draft version {draft_id} not found")
    return {"draft_id": draft_id, "content": content}


@router.post("/{chapter_number}/drafts/{draft_id}/promote")
async def promote_draft(
    project_id: str,
    chapter_number: int,
    draft_id: int,
    request: Request,
):
    from novel_runtime.storage.chapter_storage import load_draft_version
    settings = request.app.state.settings
    from novel_runtime.services.project_service import ProjectService
    from novel_runtime.db.database import Database
    from pathlib import Path

    db = request.app.state.db
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    project_path = project_svc.get_project_path(project_id)
    project = project_svc.get_project(project_id)
    chapter = project_svc.get_chapter(project_id, chapter_number)
    chapter.active_draft_id = draft_id
    from novel_runtime.storage.project_storage import ProjectStorage
    ProjectStorage(Path(settings.storage_base_path)).save_chapter(project, chapter)
    return {"active_draft_id": draft_id}


@router.post("/{chapter_number}/review/multi-reader")
async def multi_reader_review(
    project_id: str,
    chapter_number: int,
    body: dict,
    request: Request,
):
    from novel_runtime.agents.reader_personas import BUILTIN_PERSONAS, PERSONA_MAP
    from novel_runtime.llm.provider import create_provider
    from novel_runtime.services.project_service import ProjectService
    from novel_runtime.db.database import Database
    from pathlib import Path
    import json as _json

    settings = request.app.state.settings
    db = request.app.state.db
    provider = create_provider(settings)
    project_svc = ProjectService(db, Path(settings.storage_base_path))
    project_path = project_svc.get_project_path(project_id)

    from novel_runtime.storage.chapter_storage import load_chapter_file
    try:
        draft_text = load_chapter_file(project_path, chapter_number, "draft")
    except FileNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(400, "Chapter has not been drafted yet")
    if not draft_text.strip():
        from fastapi import HTTPException
        raise HTTPException(400, "Chapter draft is empty, draft the chapter first")

    persona_ids = body.get("persona_ids") or [p.persona_id for p in BUILTIN_PERSONAS]
    selected = [PERSONA_MAP[pid] for pid in persona_ids if pid in PERSONA_MAP]

    results = []
    for persona in selected:
        prompt = f"{persona.review_prompt_template}\n\n## 章节正文\n\n{draft_text[:3000]}"
        try:
            raw = provider.generate(prompt, system_prompt=f"你是一位{persona.name}读者画像")
            from novel_runtime.llm.output_validator import extract_json
            parsed = extract_json(raw)
            parsed["persona_id"] = persona.persona_id
            parsed["persona_name"] = persona.name
            results.append(parsed)
        except Exception:
            results.append({"persona_id": persona.persona_id, "persona_name": persona.name, "error": "parse failed"})

    return {"results": results}
