from __future__ import annotations
from pathlib import Path

import yaml

from novel_runtime.agents.continuity_auditor import ContinuityAuditorAgent
from novel_runtime.agents.quality_auditor import QualityAuditorAgent
from novel_runtime.agents.cross_chapter_auditor import CrossChapterAuditorAgent
from novel_runtime.agents.reader_simulator import ReaderSimulatorAgent
from novel_runtime.compiler.fix_instruction_merger import merge_all_reviews
from novel_runtime.exceptions import InvalidStateTransitionError
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import state_storage, style_storage, strategy_storage, subplot_storage
from novel_runtime.storage.chapter_storage import save_chapter_file, load_chapter_file, chapter_file_exists
from novel_runtime.storage.project_storage import ProjectStorage
from novel_runtime.models.strategy import WritingStrategy


class ReviewService:
    def __init__(
        self,
        project_service: ProjectService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
    ):
        self.project_service = project_service
        self.continuity_agent = ContinuityAuditorAgent(provider=provider, prompt_loader=prompt_loader)
        self.quality_agent = QualityAuditorAgent(provider=provider, prompt_loader=prompt_loader)
        self.cross_chapter_agent = CrossChapterAuditorAgent(provider=provider, prompt_loader=prompt_loader)
        self.reader_sim_agent = ReaderSimulatorAgent(provider=provider, prompt_loader=prompt_loader)

    def review_chapter(
        self,
        project_id: str,
        chapter_number: int,
        review_types: list[str] | None = None,
    ) -> dict:
        if review_types is None:
            review_types = ["continuity", "quality"]

        project = self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        chapter = self.project_service.get_chapter(project_id, chapter_number)
        if chapter.status not in ("drafted", "reviewed"):
            raise InvalidStateTransitionError(
                f"Chapter {chapter_number} is {chapter.status}, cannot review"
            )

        try:
            styled_draft = load_chapter_file(project_path, chapter_number, "styled_draft")
        except FileNotFoundError:
            try:
                styled_draft = load_chapter_file(project_path, chapter_number, "draft")
            except FileNotFoundError:
                styled_draft = ""

        try:
            context_pack = load_chapter_file(project_path, chapter_number, "context_pack")
        except FileNotFoundError:
            context_pack = ""
        try:
            chapter_plan = load_chapter_file(project_path, chapter_number, "plan")
        except FileNotFoundError:
            chapter_plan = ""

        continuity_issues = []
        quality_scores = {}
        quality_problems = []
        cross_chapter_text = ""
        reader_sim_text = ""

        if "continuity" in review_types:
            characters = state_storage.load_characters(project_path)
            character_state = yaml.dump(
                [c.model_dump() for c in characters], allow_unicode=True, default_flow_style=False,
            ) if characters else ""
            hooks_list = state_storage.load_hooks(project_path)
            hooks_text = yaml.dump(
                [h.model_dump() for h in hooks_list], allow_unicode=True, default_flow_style=False,
            ) if hooks_list else ""
            timeline = state_storage.load_story_state(project_path)
            timeline_text = yaml.dump(timeline, allow_unicode=True, default_flow_style=False) if timeline else ""

            world_setting = ""
            try:
                from novel_runtime.storage import bible_storage
                world_setting = bible_storage.load_bible_file(project_path, "world_setting.md")
            except FileNotFoundError:
                pass

            ag_result = self.continuity_agent.review(
                styled_draft, context_pack, character_state, timeline_text, hooks_text, world_setting,
            )
            if ag_result.success and ag_result.data:
                review_content = ag_result.data.review_content
                save_chapter_file(project_path, chapter_number, "review_continuity", review_content)
                continuity_issues = ag_result.data.issues

        if "quality" in review_types:
            style_id = project.default_style_id
            style = style_storage.load_style_asset(project_path, style_id) if style_id else None
            style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False) if style else ""

            ag_result = self.quality_agent.review(styled_draft, chapter_plan, style_params)
            if ag_result.success and ag_result.data:
                review_content = ag_result.data.review_content
                save_chapter_file(project_path, chapter_number, "review_quality", review_content)
                quality_scores = ag_result.data.scores
                quality_problems = ag_result.data.problems

        if "cross_chapter" in review_types:
            recent_plans = []
            recent_reviews = []
            for n in range(max(1, chapter_number - 4), chapter_number):
                try:
                    recent_plans.append(load_chapter_file(project_path, n, "plan"))
                except FileNotFoundError:
                    pass
                try:
                    recent_reviews.append(load_chapter_file(project_path, n, "review_continuity"))
                except FileNotFoundError:
                    pass

            story_state_text = yaml.dump(
                state_storage.load_story_state(project_path), allow_unicode=True, default_flow_style=False,
            )
            hooks_full = state_storage.load_hooks(project_path)
            hooks_detail = yaml.dump(
                [h.model_dump() for h in hooks_full], allow_unicode=True, default_flow_style=False,
            ) if hooks_full else ""
            subplots = subplot_storage.load_subplots(project_path)
            subplots_text = yaml.dump(
                [s.model_dump() for s in subplots], allow_unicode=True, default_flow_style=False,
            ) if subplots else ""

            strategy = strategy_storage.load_strategy(project_path)
            strategy_summary = (
                f"节奏: {strategy.pacing_strategy.type}, "
                f"最大子线: {strategy.subplot_policy.max_simultaneous}, "
                f"最大伏笔: {strategy.hook_policy.max_open_hooks}"
            )

            ag_result = self.cross_chapter_agent.review(
                styled_draft,
                "\n---\n".join(recent_plans),
                "\n---\n".join(recent_reviews),
                story_state_text,
                hooks_detail,
                subplots_text,
                strategy_summary,
            )
            if ag_result.success and ag_result.data:
                cross_chapter_text = ag_result.data.review_content
                save_chapter_file(project_path, chapter_number, "review_cross_chapter", cross_chapter_text)

        if "reader_sim" in review_types:
            style_id = project.default_style_id
            style = style_storage.load_style_asset(project_path, style_id) if style_id else None
            style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False) if style else ""

            recent_summary = ""
            if chapter_number > 1:
                try:
                    prev_draft = load_chapter_file(project_path, chapter_number - 1, "draft")
                    if prev_draft:
                        lines = prev_draft.strip().split("\n")
                        recent_summary = "\n".join(lines[:5]) if len(lines) > 5 else prev_draft[:500]
                except FileNotFoundError:
                    pass

            target_reader = project.target_reader or "喜欢快节奏爽文的读者"

            strategy = strategy_storage.load_strategy(project_path)
            strategy_summary = (
                f"节奏: {strategy.pacing_strategy.type}, "
                f"张力曲线: {strategy.pacing_strategy.tension_curve}"
            )

            ag_result = self.reader_sim_agent.simulate(
                styled_draft, style_params, recent_summary, target_reader, strategy_summary,
            )
            if ag_result.success and ag_result.data:
                reader_sim_text = ag_result.data.review_content
                save_chapter_file(project_path, chapter_number, "review_reader_sim", reader_sim_text)

        fix_file = merge_all_reviews(
            continuity_issues=continuity_issues,
            quality_scores=quality_scores,
            quality_problems=quality_problems,
            cross_chapter_text=cross_chapter_text,
            reader_sim_text=reader_sim_text,
            styled_draft=styled_draft,
        )
        fix_yaml = yaml.dump(fix_file.model_dump(), allow_unicode=True, default_flow_style=False)
        save_chapter_file(project_path, chapter_number, "fix_instructions", fix_yaml)

        chapter.status = "reviewed"
        ProjectStorage(self.project_service.storage_base).save_chapter(project, chapter)

        review_paths = {}
        if "continuity" in review_types:
            review_paths["continuity"] = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "review_continuity.md")
        if "quality" in review_types:
            review_paths["quality"] = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "review_quality.md")
        if "cross_chapter" in review_types:
            review_paths["cross_chapter"] = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "review_cross_chapter.md")
        if "reader_sim" in review_types:
            review_paths["reader_sim"] = str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "review_reader_sim.md")

        has_critical = any(
            i.get("severity") == "critical" for i in continuity_issues
        )

        if not has_critical and "critical" in str(fix_file.model_dump()):
            has_critical = True

        return {
            "review_paths": review_paths,
            "fix_instructions_path": str(
                project_path / "chapters" / f"chapter_{chapter_number:03d}" / "fix_instructions.yaml"
            ),
            "has_critical_issues": has_critical,
        }
