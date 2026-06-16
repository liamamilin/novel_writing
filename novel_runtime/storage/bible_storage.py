from __future__ import annotations

from datetime import datetime
from pathlib import Path

from novel_runtime.models.bible import BibleChangelog, BibleChangelogEntry
from novel_runtime.storage.base import read_md, read_yaml_model, write_md, write_yaml_model

BIBLE_FILENAMES = [
    "novel_bible.md",
    "world_setting.md",
    "character_profiles.md",
    "volume_plan.md",
    "chapter_plan.md",
]


def save_bible_file(project_path: Path, filename: str, content: str) -> Path:
    bible_dir = project_path / "bible"
    bible_dir.mkdir(parents=True, exist_ok=True)
    return write_md(bible_dir / filename, content, overwrite=True)


def load_bible_file(project_path: Path, filename: str) -> str:
    return read_md(project_path / "bible" / filename)


def save_bible_changelog(project_path: Path, changelog: BibleChangelog) -> Path:
    path = project_path / "bible" / "bible_changelog.yaml"
    return write_yaml_model(path, changelog, overwrite=True)


def load_bible_changelog(project_path: Path) -> BibleChangelog:
    path = project_path / "bible" / "bible_changelog.yaml"
    if not path.exists():
        return BibleChangelog()
    return read_yaml_model(path, BibleChangelog)


def add_changelog_entry(project_path: Path, chapter: str, changes: list[str]) -> BibleChangelogEntry:
    changelog = load_bible_changelog(project_path)
    version = len(changelog.entries) + 1
    entry = BibleChangelogEntry(
        version=version,
        chapter=chapter,
        changes=changes,
        timestamp=datetime.now(),
    )
    changelog.entries.append(entry)
    save_bible_changelog(project_path, changelog)
    return entry


def list_bible_files(project_path: Path) -> list[str]:
    bible_dir = project_path / "bible"
    if not bible_dir.exists():
        return []
    return [f.name for f in sorted(bible_dir.iterdir()) if f.suffix in (".md", ".yaml")]


def freeze_bible_version(project_path: Path, version: int) -> Path:
    snapshot_dir = project_path / "snapshots" / f"bible_v{version}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for filename in BIBLE_FILENAMES:
        src = project_path / "bible" / filename
        if src.exists():
            content = read_md(src)
            write_md(snapshot_dir / filename, content, overwrite=True)
    changelog_path = project_path / "bible" / "bible_changelog.yaml"
    if changelog_path.exists():
        from shutil import copy2
        copy2(changelog_path, snapshot_dir / "bible_changelog.yaml")
    return snapshot_dir


def get_bible_version(project_path: Path) -> int:
    changelog = load_bible_changelog(project_path)
    return len(changelog.entries)
