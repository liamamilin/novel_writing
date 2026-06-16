from __future__ import annotations

from pathlib import Path

from novel_runtime.models.subplot import Subplot
from novel_runtime.storage.base import read_yaml, read_yaml_model, write_yaml, write_yaml_model


def _subplots_dir(project_path: Path) -> Path:
    return project_path / "subplots"


def save_subplots(project_path: Path, subplots: list[Subplot]) -> Path:
    subplots_dir = _subplots_dir(project_path)
    subplots_dir.mkdir(parents=True, exist_ok=True)
    registry = {"subplots": [{"subplot_id": s.subplot_id, "name": s.name, "status": s.status} for s in subplots]}
    write_yaml(subplots_dir / "subplot_registry.yaml", registry, overwrite=True)
    for sp in subplots:
        write_yaml_model(subplots_dir / f"{sp.subplot_id}.yaml", sp, overwrite=True)
    return subplots_dir / "subplot_registry.yaml"


def load_subplots(project_path: Path) -> list[Subplot]:
    registry_path = _subplots_dir(project_path) / "subplot_registry.yaml"
    if not registry_path.exists():
        return []
    data = read_yaml(registry_path)
    result = []
    for entry in data.get("subplots", []):
        sp_path = _subplots_dir(project_path) / f"{entry['subplot_id']}.yaml"
        if sp_path.exists():
            result.append(read_yaml_model(sp_path, Subplot))
    return result


def load_subplot(project_path: Path, subplot_id: str) -> Subplot | None:
    sp_path = _subplots_dir(project_path) / f"{subplot_id}.yaml"
    if not sp_path.exists():
        return None
    return read_yaml_model(sp_path, Subplot)


def update_subplot(project_path: Path, subplot_id: str, updates: dict) -> Subplot | None:
    sp = load_subplot(project_path, subplot_id)
    if sp is None:
        return None
    updated = sp.model_copy(update=updates)
    subplot_path = _subplots_dir(project_path) / f"{subplot_id}.yaml"
    write_yaml_model(subplot_path, updated, overwrite=True)
    registry_path = _subplots_dir(project_path) / "subplot_registry.yaml"
    registry = read_yaml(registry_path)
    for entry in registry.get("subplots", []):
        if entry["subplot_id"] == subplot_id:
            entry["status"] = updated.status
    write_yaml(registry_path, registry, overwrite=True)
    return updated


def delete_subplot(project_path: Path, subplot_id: str) -> bool:
    sp_path = _subplots_dir(project_path) / f"{subplot_id}.yaml"
    deleted = False
    if sp_path.exists():
        sp_path.unlink()
        deleted = True
    registry_path = _subplots_dir(project_path) / "subplot_registry.yaml"
    if registry_path.exists():
        data = read_yaml(registry_path)
        data["subplots"] = [s for s in data.get("subplots", []) if s.get("subplot_id") != subplot_id]
        write_yaml(registry_path, data, overwrite=True)
    return deleted


def get_active_subplots(project_path: Path) -> list[Subplot]:
    return [s for s in load_subplots(project_path) if s.status != "resolved"]


def get_subplots_by_chapter_range(project_path: Path, chapter_from: int, chapter_to: int) -> list[Subplot]:
    result = []
    for s in load_subplots(project_path):
        try:
            next_ch = int(s.interleave_plan.get("next_suggested_chapter", "0").split("_")[-1])
        except (ValueError, IndexError):
            continue
        if chapter_from <= next_ch <= chapter_to:
            result.append(s)
    return result
