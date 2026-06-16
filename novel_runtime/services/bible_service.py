from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from novel_runtime.agents.story_architect import StoryArchitectAgent
from novel_runtime.db.database import Database
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.models.project import ProjectUpdate
from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.models.subplot import Subplot
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import bible_storage, strategy_storage, subplot_storage


class BibleService:
    def __init__(
        self,
        db: Database,
        project_service: ProjectService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
    ):
        self.db = db
        self.project_service = project_service
        self.provider = provider
        self.prompt_loader = prompt_loader
        self._agent = StoryArchitectAgent(provider=provider, prompt_loader=prompt_loader)

    def generate_direction_variants(self, project_id: str) -> list[dict]:
        project = self.project_service.get_project(project_id)
        result = self._agent.generate_direction_variants(
            idea=project.idea,
            genre=project.genre,
            target_reader=project.target_reader,
            core_selling_point=project.core_selling_point,
        )
        if not result.success or not result.data:
            return []
        try:
            data = yaml.safe_load(result.data)
            return data.get("variants", [])
        except Exception:
            return []

    def generate_character_concepts(self, project_id: str, direction: dict) -> dict:
        project = self.project_service.get_project(project_id)
        result = self._agent.generate_character_concepts(direction, project.idea)
        if not result.success or not result.data:
            return {}
        try:
            return yaml.safe_load(result.data) or {}
        except Exception:
            return {}

    def load_selected_direction(self, project_id: str) -> dict:
        project_path = self.project_service.get_project_path(project_id)
        direction_path = project_path / "bible" / "selected_direction.yaml"
        if direction_path.exists():
            return yaml.safe_load(direction_path.read_text(encoding="utf-8")) or {}
        return {}

    def select_direction(self, project_id: str, variant_id: int, modifications: str = "") -> dict:
        self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)
        direction_path = project_path / "bible" / "selected_direction.yaml"
        data = {"variant_id": variant_id, "modifications": modifications, "timestamp": str(datetime.now())}
        direction_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        return data

    def confirm_characters(self, project_id: str, character_adjustments: dict) -> dict:
        self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)
        confirm_path = project_path / "bible" / "character_adjustments.yaml"
        data = {"adjustments": character_adjustments, "timestamp": str(datetime.now())}
        confirm_path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        return data

    def generate_bible(self, project_id: str, direction: dict, characters: list[dict]) -> dict:
        project = self.project_service.get_project(project_id)
        result = self._agent.generate_full_bible(direction, characters, project.idea, project.genre)
        if not result.success or not result.data:
            return {}
        raw = result.data
        raw.split("---PART")
        part_map = {}
        for i, filename in enumerate(["novel_bible.md", "world_setting.md", "character_profiles.md", "volume_plan.md", "chapter_plan.md"]):
            key = f"PART {i+1}"
            if key in raw:
                start = raw.find(key)
                end_idx = raw.find("---PART", start + len(key) + 1) if i < 4 else len(raw)
                content = raw[start:end_idx].split("\n", 1)[1].strip() if "\n" in raw[start:end_idx] else ""
                part_map[filename] = content

        project_path = self.project_service.get_project_path(project_id)
        for filename, content in part_map.items():
            if content:
                bible_storage.save_bible_file(project_path, filename, content)

        if part_map:
            bible_storage.add_changelog_entry(project_path, "chapter_000", [
                f"Initial generation: {', '.join(part_map.keys())}"
            ])
            bible_storage.freeze_bible_version(project_path, 1)
            self._generate_initial_strategy(project_path, project.genre, direction)
            self._generate_initial_subplots(project_path, part_map.get("chapter_plan.md", ""), part_map.get("character_profiles.md", ""))
            self.project_service.update_project(project_id, ProjectUpdate(bible_version=1))

        return part_map

    def _generate_initial_strategy(self, project_path: Path, genre: str, direction: dict):
        from novel_runtime.models.strategy import ChapterLengthConfig
        strategy = WritingStrategy(name=f"{direction.get('name', 'default')}策略")
        pacing = direction.get("pacing_style", "")
        if "爽文" in pacing or "快" in pacing:
            strategy.pacing_strategy.type = "variable_rhythm"
            strategy.chapter_length = ChapterLengthConfig(target=2500, min=2000, max=3000)
        elif "慢" in pacing:
            strategy.pacing_strategy.type = "steady"
            strategy.chapter_length = ChapterLengthConfig(target=3500, min=3000, max=4000)
        strategy_storage.save_strategy(project_path, strategy)

    def _generate_initial_subplots(self, project_path: Path, chapter_plan: str, character_profiles: str):
        main_plot = Subplot(subplot_id="subplot_main", name="主线", type="main_plot", status="setup")
        main_plot.arc = {"setup_chapter": "chapter_001", "current_stage": "setup"}
        subplot_storage.save_subplots(project_path, [main_plot])

    def get_bible(self, project_id: str) -> dict[str, str]:
        project_path = self.project_service.get_project_path(project_id)
        result = {}
        for filename in bible_storage.BIBLE_FILENAMES:
            try:
                result[filename] = bible_storage.load_bible_file(project_path, filename)
            except FileNotFoundError:
                result[filename] = ""
        return result

    def get_bible_version(self, project_id: str) -> int:
        project_path = self.project_service.get_project_path(project_id)
        return bible_storage.get_bible_version(project_path)
