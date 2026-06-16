from __future__ import annotations

from pathlib import Path

from novel_runtime.models.style import CharacterVoice, StyleAsset
from novel_runtime.storage.base import (
    list_files,
    read_md,
    read_yaml_model,
    write_md,
    write_yaml_model,
)


def save_style_asset(project_path: Path, style: StyleAsset) -> Path:
    style_dir = project_path / "style_assets"
    style_dir.mkdir(parents=True, exist_ok=True)
    return write_yaml_model(style_dir / f"{style.style_id}.yaml", style, overwrite=True)


def load_style_asset(project_path: Path, style_id: str) -> StyleAsset:
    path = project_path / "style_assets" / f"{style_id}.yaml"
    return read_yaml_model(path, StyleAsset)


def list_style_assets(project_path: Path) -> list[StyleAsset]:
    paths = list_files(project_path / "style_assets", "*.yaml")
    result = []
    for p in paths:
        try:
            result.append(read_yaml_model(p, StyleAsset))
        except Exception:
            pass
    return result


def save_source_text(project_path: Path, sample_id: str, text: str) -> Path:
    source_dir = project_path / "source_texts"
    source_dir.mkdir(parents=True, exist_ok=True)
    return write_md(source_dir / f"{sample_id}.txt", text, overwrite=True)


def load_source_text(project_path: Path, sample_id: str) -> str:
    path = project_path / "source_texts" / f"{sample_id}.txt"
    return read_md(path)


def list_source_texts(project_path: Path) -> list[str]:
    paths = list_files(project_path / "source_texts", "*.txt")
    return [p.stem for p in paths]


def save_character_voice(project_path: Path, voice: CharacterVoice) -> Path:
    voices_dir = project_path / "style_assets" / "character_voices"
    voices_dir.mkdir(parents=True, exist_ok=True)
    return write_yaml_model(voices_dir / f"{voice.voice_id}.yaml", voice, overwrite=True)


def load_character_voice(project_path: Path, voice_id: str) -> CharacterVoice:
    path = project_path / "style_assets" / "character_voices" / f"{voice_id}.yaml"
    return read_yaml_model(path, CharacterVoice)


def list_character_voices(project_path: Path) -> list[CharacterVoice]:
    voices_dir = project_path / "style_assets" / "character_voices"
    paths = list_files(voices_dir, "*.yaml")
    result = []
    for p in paths:
        try:
            result.append(read_yaml_model(p, CharacterVoice))
        except Exception:
            pass
    return result
