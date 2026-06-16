from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


def read_yaml(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")


def write_yaml(file_path: Path, data: dict, overwrite: bool = False) -> Path:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite and file_path.exists():
        raise FileExistsError(f"File already exists: {file_path}")
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return file_path


def read_md(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_md(file_path: Path, content: str, overwrite: bool = False) -> Path:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite and file_path.exists():
        raise FileExistsError(f"File already exists: {file_path}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def read_yaml_model(file_path: Path, model_class: type[BaseModel]) -> BaseModel:
    data = read_yaml(file_path)
    return model_class(**data)


def write_yaml_model(file_path: Path, model: BaseModel, overwrite: bool = False) -> Path:
    data = model.model_dump()
    return write_yaml(file_path, data, overwrite=overwrite)


def list_files(directory: Path, pattern: str = "*.yaml") -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(pattern))


def delete_file(file_path: Path) -> bool:
    if not file_path.exists():
        return False
    file_path.unlink()
    return True
