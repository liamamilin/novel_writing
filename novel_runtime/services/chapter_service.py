from __future__ import annotations
import yaml
from pathlib import Path

from novel_runtime.agents.chapter_planner import ChapterPlannerAgent, ChapterPlanResult
from novel_runtime.agents.chapter_writer import ChapterWriterAgent, ChapterWriteResult
from novel_runtime.agents.narrative_polisher import NarrativePolisherAgent
from novel_runtime.compiler.plan_validator import PlanValidator
from novel_runtime.exceptions import ChapterNotFoundError, InvalidStateTransitionError, StyleNotSetError
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.models.style import StyleAsset
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import strategy_storage, style_storage, state_storage
from novel_runtime.storage.chapter_storage import save_chapter_file, load_chapter_file, save_draft_version
from novel_runtime.storage.project_storage import ProjectStorage
from novel_runtime.services.context_service import ContextService


class ChapterService:
    def __init__(
        self,
        project_service: ProjectService,
        context_service: ContextService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
    ):
        self.project_service = project_service
        self.context_service = context_service
        self.provider = provider
        self.prompt_loader = prompt_loader
        self._planner = ChapterPlannerAgent(provider=provider, prompt_loader=prompt_loader)
        self._writer = ChapterWriterAgent(provider=provider, prompt_loader=prompt_loader)
        self._polisher = NarrativePolisherAgent(provider=provider, prompt_loader=prompt_loader)
        self._validator = PlanValidator()

    def generate_plan(self, project_id: str, chapter_number: int, chapter_goal: str = "") -> dict:
        project = self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        try:
            existing_chapter = self.project_service.get_chapter(project_id, chapter_number)
            if existing_chapter.status not in ("planned", ""):
                raise InvalidStateTransitionError(
                    f"Chapter {chapter_number} is already {existing_chapter.status}, cannot plan"
                )
        except ChapterNotFoundError:
            self.project_service.create_chapter(project_id, chapter_number)

        ctx_result = self.context_service.compile_context(project_id, chapter_number, chapter_goal)

        strategy = strategy_storage.load_strategy(project_path)
        strategy_summary = (
            f"字数: {strategy.chapter_length.min}-{strategy.chapter_length.max}\n"
            f"节奏: {strategy.pacing_strategy.type}\n"
            f"最大子线: {strategy.subplot_policy.max_simultaneous}\n"
        )

        context_pack_path = ctx_result.get("context_pack_path", "")
        try:
            context_pack_content = Path(context_pack_path).read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            context_pack_content = ""

        result = self._planner.plan(context_pack_content, strategy_summary)
        if not result.success:
            return {"plan_path": "", "errors": result.validation_errors}

        plan_result: ChapterPlanResult = result.data

        validation = self._validator.validate(
            plan_result.plan_content,
            rhythm=plan_result.rhythm,
            subplot_allocation=plan_result.subplot_allocation,
            contract=plan_result.agent_contract,
            strategy=strategy,
        )
        if not validation.is_valid:
            return {"plan_path": "", "errors": validation.errors}

        save_chapter_file(project_path, chapter_number, "plan", plan_result.plan_content)

        chapter = self.project_service.get_chapter(project_id, chapter_number)
        chapter.rhythm_type = plan_result.rhythm.rhythm_type
        chapter.subplots_advanced = plan_result.subplot_allocation.advanced
        chapter.subplots_idle = plan_result.subplot_allocation.idle
        chapter.plan_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "chapter_plan.md")
        chapter.status = "planned"

        ProjectStorage(self.project_service.storage_base).save_chapter(project, chapter)

        return {
            "plan_path": chapter.plan_path,
            "rhythm_type": plan_result.rhythm.rhythm_type,
            "agent_contract": {
                "promises": plan_result.agent_contract.promises,
                "constraints": plan_result.agent_contract.constraints,
            },
        }

    def generate_draft(self, project_id: str, chapter_number: int) -> dict:
        project = self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        chapter = self.project_service.get_chapter(project_id, chapter_number)
        if chapter.status != "planned":
            raise InvalidStateTransitionError(
                f"Chapter {chapter_number} is {chapter.status}, cannot generate draft"
            )

        try:
            context_pack = load_chapter_file(project_path, chapter_number, "context_pack")
        except FileNotFoundError:
            context_pack = ""
        try:
            chapter_plan = load_chapter_file(project_path, chapter_number, "plan")
        except FileNotFoundError:
            chapter_plan = ""

        style_id = project.default_style_id
        try:
            style = style_storage.load_style_asset(project_path, style_id) if style_id else StyleAsset()
        except FileNotFoundError:
            raise StyleNotSetError("No style set. Run style analysis first.")

        characters = state_storage.load_characters(project_path)
        voices = []
        for c in characters:
            if c.voice_id:
                try:
                    voice = style_storage.load_character_voice(project_path, c.voice_id)
                    voices.append(voice)
                except FileNotFoundError:
                    pass
        all_voices = voices + style_storage.list_character_voices(project_path)
        unique_voices = {v.voice_id: v for v in all_voices}.values() if all_voices else []

        from novel_runtime.models.chapter import AgentContract
        contract = AgentContract()
        if "## Agent Contract" in chapter_plan:
            plan_section = chapter_plan.split("## Agent Contract")[1].split("##")[0] if "## Agent Contract" in chapter_plan else ""
            for line in plan_section.split("\n"):
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    content = line.lstrip("- *").strip()
                    if "约束" in content or "不得" in content or "字数" in content:
                        contract.constraints.append(content)
                    else:
                        contract.promises.append(content)

        result = self._writer.write(context_pack, chapter_plan, style, list(unique_voices), contract)
        if not result.success:
            return {"draft_path": "", "state_annotations_path": "", "contract_check": {}, "errors": result.validation_errors}

        write_result: ChapterWriteResult = result.data

        chapter.draft_count += 1
        current_draft_id = chapter.draft_count
        save_draft_version(project_path, chapter_number, current_draft_id, write_result.draft)

        chapter.active_draft_id = current_draft_id
        chapter.draft_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "drafts" / f"draft_v{current_draft_id}.md")
        chapter.state_annotations_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "state_annotations.yaml")

        annotations_yaml = yaml.dump(write_result.annotations, allow_unicode=True, default_flow_style=False) if write_result.annotations else "{}"
        save_chapter_file(project_path, chapter_number, "state_annotations", annotations_yaml)

        chapter.status = "drafted"
        ProjectStorage(self.project_service.storage_base).save_chapter(project, chapter)

        return {
            "draft_path": chapter.draft_path,
            "state_annotations_path": chapter.state_annotations_path,
            "contract_check": write_result.contract_check,
        }

    def polish_draft(self, project_id: str, chapter_number: int) -> dict:
        project = self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        chapter = self.project_service.get_chapter(project_id, chapter_number)
        if chapter.status != "drafted":
            raise InvalidStateTransitionError(
                f"Chapter {chapter_number} is {chapter.status}, cannot polish"
            )

        try:
            draft = load_chapter_file(project_path, chapter_number, "draft")
        except FileNotFoundError:
            draft = ""
        try:
            plan = load_chapter_file(project_path, chapter_number, "plan")
        except FileNotFoundError:
            plan = ""

        style_id = project.default_style_id
        try:
            style = style_storage.load_style_asset(project_path, style_id) if style_id else StyleAsset()
        except FileNotFoundError:
            raise StyleNotSetError("No style set.")

        style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False)
        rhythm_type = chapter.rhythm_type or ""

        characters = state_storage.load_characters(project_path)
        voices = style_storage.list_character_voices(project_path)
        voice_params = "\n".join(f"- {v.character_name}: {v.speech_patterns}" for v in voices)

        result = self._polisher.polish(draft, style_params, rhythm_type, voice_params, annotations_summary="")
        if not result.success:
            return {"styled_draft_path": "", "errors": result.validation_errors}

        polished = str(result.data)
        save_chapter_file(project_path, chapter_number, "styled_draft", polished)

        chapter.styled_draft_path = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "styled_draft.md")
        ProjectStorage(self.project_service.storage_base).save_chapter(project, chapter)

        return {"styled_draft_path": chapter.styled_draft_path}
