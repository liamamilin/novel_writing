from __future__ import annotations
import os
import stat
from pathlib import Path

from novel_runtime.storage.base import read_md, write_md, read_yaml, write_yaml

MD_EXT = {"md"}
YAML_EXT = {"yaml"}

_FILE_TYPE_MAP = {
    "context_pack": ("md", "context_pack.md"),
    "plan": ("md", "chapter_plan.md"),
    "draft": ("md", "draft.md"),
    "styled_draft": ("md", "styled_draft.md"),
    "final": ("md", "final.md"),
    "state_annotations": ("yaml", "state_annotations.yaml"),
    "fix_instructions": ("yaml", "fix_instructions.yaml"),
    "review_continuity": ("md", "review_continuity.md"),
    "review_quality": ("md", "review_quality.md"),
    "review_cross_chapter": ("md", "review_cross_chapter.md"),
    "review_reader_sim": ("md", "review_reader_sim.md"),
}


def _chapter_dir(project_path: Path, chapter_number: int) -> Path:
    return project_path / "chapters" / f"chapter_{chapter_number:03d}"


def save_chapter_file(project_path: Path, chapter_number: int, file_type: str, content: str) -> Path:
    ext, filename = _FILE_TYPE_MAP[file_type]
    file_path = _chapter_dir(project_path, chapter_number) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if ext == "yaml":
        import yaml
        data = yaml.safe_load(content) if content.strip() else {}
        return write_yaml(file_path, data, overwrite=True)
    else:
        return write_md(file_path, content, overwrite=True)


def load_chapter_file(project_path: Path, chapter_number: int, file_type: str) -> str:
    ext, filename = _FILE_TYPE_MAP[file_type]
    file_path = _chapter_dir(project_path, chapter_number) / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Chapter file not found: {file_path}")
    if ext == "yaml":
        data = read_yaml(file_path)
        import yaml
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    else:
        return read_md(file_path)


def chapter_file_exists(project_path: Path, chapter_number: int, file_type: str) -> bool:
    ext, filename = _FILE_TYPE_MAP[file_type]
    file_path = _chapter_dir(project_path, chapter_number) / filename
    return file_path.exists()


def list_drafts(project_path: Path, chapter_number: int) -> list[dict]:
    drafts_dir = _chapter_dir(project_path, chapter_number) / "drafts"
    if not drafts_dir.exists():
        return []
    files = sorted(drafts_dir.glob("draft_v*.md"))
    result = []
    for f in files:
        vid = int(f.stem.split("_v")[1])
        result.append({"version_id": vid, "path": str(f), "size": f.stat().st_size})
    return result


def save_draft_version(project_path: Path, chapter_number: int, draft_id: int, content: str) -> Path:
    drafts_dir = _chapter_dir(project_path, chapter_number) / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    file_path = drafts_dir / f"draft_v{draft_id}.md"
    return write_md(file_path, content, overwrite=True)


def load_draft_version(project_path: Path, chapter_number: int, draft_id: int) -> str:
    file_path = _chapter_dir(project_path, chapter_number) / "drafts" / f"draft_v{draft_id}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"Draft version {draft_id} not found")
    return read_md(file_path)


def mark_reviews_stale(project_path: Path, chapter_number: int) -> None:
    """Rename review_*.md → review_*.md.stale to mark them invalid after content edit."""
    chapter_dir = _chapter_dir(project_path, chapter_number)
    if not chapter_dir.exists():
        return
    for f in chapter_dir.iterdir():
        if f.suffix == ".md" and f.stem.startswith("review_"):
            stale_name = f.with_name(f.name + ".stale")
            if not stale_name.exists():
                f.rename(stale_name)


def freeze_chapter(project_path: Path, chapter_number: int) -> None:
    chapter_dir = _chapter_dir(project_path, chapter_number)
    if not chapter_dir.exists():
        return
    for f in chapter_dir.rglob("*"):
        if f.is_file():
            os.chmod(f, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def unfreeze_chapter(project_path: Path, chapter_number: int) -> None:
    chapter_dir = _chapter_dir(project_path, chapter_number)
    if not chapter_dir.exists():
        return
    for f in chapter_dir.rglob("*"):
        if f.is_file():
            os.chmod(f, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
