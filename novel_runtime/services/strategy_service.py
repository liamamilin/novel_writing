from __future__ import annotations

from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import strategy_storage


class StrategyService:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def get_strategy(self, project_id: str) -> WritingStrategy:
        return strategy_storage.load_strategy(self.project_service.get_project_path(project_id))

    def update_strategy(self, project_id: str, updates: dict) -> WritingStrategy:
        project_path = self.project_service.get_project_path(project_id)
        strategy = strategy_storage.load_strategy(project_path)
        for key, value in updates.items():
            setattr(strategy, key, value)
        strategy_storage.save_strategy(project_path, strategy)
        return strategy

    def reset_strategy(self, project_id: str) -> WritingStrategy:
        strategy = strategy_storage.get_default_strategy()
        strategy_storage.save_strategy(self.project_service.get_project_path(project_id), strategy)
        return strategy
