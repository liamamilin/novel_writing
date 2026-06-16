from __future__ import annotations

from uuid import uuid4

from fastapi import BackgroundTasks

from novel_runtime.agents.style_analyst import StyleAnalystAgent
from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.models.style import CharacterVoice, StyleAsset
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.task_service import TaskService
from novel_runtime.storage import style_storage


class StyleService:
    def __init__(
        self,
        db: Database,
        project_service: ProjectService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
        config: Settings,
    ):
        self.db = db
        self.project_service = project_service
        self.provider = provider
        self.prompt_loader = prompt_loader
        self.config = config
        self.task_service = TaskService(db)

        self._agent = StyleAnalystAgent(
            provider=provider,
            prompt_loader=prompt_loader,
        )

    def upload_sample(self, project_id: str, sample_name: str, text: str) -> str:
        self.project_service.get_project(project_id)
        sample_id = f"sample_{uuid4().hex[:6]}"
        project_path = self.project_service.get_project_path(project_id)
        style_storage.save_source_text(project_path, sample_id, text)
        return sample_id

    def analyze_style_sync(
        self, project_id: str, sample_ids: list[str], style_name: str, run_adversarial: bool = True
    ) -> StyleAsset:
        self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        samples = []
        for sid in sample_ids:
            try:
                text = style_storage.load_source_text(project_path, sid)
                samples.append(text)
            except FileNotFoundError:
                pass

        style_id = f"style_{uuid4().hex[:6]}"
        result = self._agent.analyze_style(samples, style_name)
        if not result.success:
            style = StyleAsset(style_id=style_id, style_name=style_name)
        else:
            style = result.data
            style.style_id = style_id
            style.source_text_ids = sample_ids

        style_storage.save_style_asset(project_path, style)

        if run_adversarial and result.success:
            try:
                adv_result = self._agent.adversarial_test(style)
                if not adv_result.passed:
                    pass
            except Exception:
                pass

        from novel_runtime.models.project import ProjectUpdate
        self.project_service.update_project(project_id, ProjectUpdate(default_style_id=style_id))
        return style

    def analyze_style_async(
        self, project_id: str, sample_ids: list[str], style_name: str,
        background_tasks: BackgroundTasks, run_adversarial: bool = True,
    ):
        def _execute():
            self.analyze_style_sync(project_id, sample_ids, style_name, run_adversarial)
        task = self.task_service.create_task(project_id, "style_analysis", {
            "sample_ids": sample_ids, "style_name": style_name,
        })
        background_tasks.add_task(_execute)
        return task

    def generate_test_paragraph(self, project_id: str, style_id: str, topic: str = "一场激烈的拍卖会") -> str:
        project_path = self.project_service.get_project_path(project_id)
        style = style_storage.load_style_asset(project_path, style_id)
        result = self._agent.generate_test_paragraph(style, topic)
        return str(result.data) if result.success else ""

    def get_style(self, project_id: str, style_id: str) -> StyleAsset:
        project_path = self.project_service.get_project_path(project_id)
        return style_storage.load_style_asset(project_path, style_id)

    def list_styles(self, project_id: str) -> list[StyleAsset]:
        project_path = self.project_service.get_project_path(project_id)
        return style_storage.list_style_assets(project_path)

    def save_character_voice(self, project_id: str, voice: CharacterVoice) -> CharacterVoice:
        project_path = self.project_service.get_project_path(project_id)
        if not voice.voice_id:
            voice.voice_id = f"voice_{uuid4().hex[:6]}"
        style_storage.save_character_voice(project_path, voice)
        return voice

    def get_character_voice(self, project_id: str, voice_id: str) -> CharacterVoice:
        project_path = self.project_service.get_project_path(project_id)
        return style_storage.load_character_voice(project_path, voice_id)
