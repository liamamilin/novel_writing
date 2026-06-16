from __future__ import annotations

from pathlib import Path

from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.storage.base import read_yaml_model, write_yaml_model


def save_strategy(project_path: Path, strategy: WritingStrategy) -> Path:
    strategy_dir = project_path / "strategies"
    strategy_dir.mkdir(parents=True, exist_ok=True)
    return write_yaml_model(strategy_dir / "writing_strategy.yaml", strategy, overwrite=True)


def load_strategy(project_path: Path) -> WritingStrategy:
    path = project_path / "strategies" / "writing_strategy.yaml"
    if not path.exists():
        return WritingStrategy(name="默认策略")
    return read_yaml_model(path, WritingStrategy)


def get_default_strategy() -> WritingStrategy:
    return WritingStrategy(name="默认策略")
