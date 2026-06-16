from __future__ import annotations
from pathlib import Path

import yaml

from novel_runtime.exceptions import ProjectNotFoundError
from novel_runtime.storage.base import write_yaml


INITIAL_STORY_STATE = {
    "current_location": "",
    "current_time": "",
    "current_conflict": "",
    "protagonist_status": "",
    "timeline": [],
}

INITIAL_CHARACTERS = {"characters": []}

INITIAL_HOOKS = {"hooks": []}

INITIAL_SUBPLOT_REGISTRY = {"subplots": []}


def create_project_layout(project_path: Path, project_meta: dict) -> dict[str, Path]:
    dirs = {
        "project_root": project_path,
        "style_assets": project_path / "style_assets",
        "source_texts": project_path / "source_texts",
        "bible": project_path / "bible",
        "strategies": project_path / "strategies",
        "chapters": project_path / "chapters",
        "subplots": project_path / "subplots",
        "states": project_path / "states",
        "snapshots": project_path / "snapshots",
    }

    files = {}

    for name, path in dirs.items():
        if name == "project_root":
            continue
        path.mkdir(parents=True, exist_ok=True)

    project_yaml_path = project_path / "project.yaml"
    write_yaml(project_yaml_path, project_meta, overwrite=True)
    files["project_yaml"] = project_yaml_path

    files["story_state"] = write_yaml(
        project_path / "states" / "story_state.yaml", INITIAL_STORY_STATE, overwrite=True
    )
    files["characters"] = write_yaml(
        project_path / "states" / "characters.yaml", INITIAL_CHARACTERS, overwrite=True
    )
    files["hooks"] = write_yaml(
        project_path / "states" / "hooks.yaml", INITIAL_HOOKS, overwrite=True
    )
    files["subplot_registry"] = write_yaml(
        project_path / "subplots" / "subplot_registry.yaml",
        INITIAL_SUBPLOT_REGISTRY,
        overwrite=True,
    )

    return files


def validate_project_layout(project_path: Path) -> bool:
    if not project_path.exists():
        return False
    required_dirs = [
        "style_assets", "source_texts", "bible", "strategies",
        "chapters", "subplots", "states", "snapshots",
    ]
    required_files = [
        "project.yaml",
        "states/story_state.yaml",
        "states/characters.yaml",
        "states/hooks.yaml",
        "subplots/subplot_registry.yaml",
    ]
    for d in required_dirs:
        if not (project_path / d).is_dir():
            return False
    for f in required_files:
        if not (project_path / f).is_file():
            return False
    try:
        from novel_runtime.storage.base import read_yaml
        read_yaml(project_path / "project.yaml")
    except Exception:
        return False
    return True
