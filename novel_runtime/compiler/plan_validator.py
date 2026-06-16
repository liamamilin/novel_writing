from __future__ import annotations

import re

from novel_runtime.models.chapter import AgentContract, ChapterPlanRhythm, SubplotAllocation
from novel_runtime.models.strategy import WritingStrategy


class PlanValidationResult:
    def __init__(self, is_valid: bool, errors: list[str] | None = None):
        self.is_valid = is_valid
        self.errors = errors or []


class PlanValidator:
    def validate(
        self,
        plan_content: str,
        rhythm: ChapterPlanRhythm | None = None,
        subplot_allocation: SubplotAllocation | None = None,
        contract: AgentContract | None = None,
        context_pack: str | None = None,
        strategy: WritingStrategy | None = None,
    ) -> PlanValidationResult:
        errors = []

        if contract is None:
            errors.append("缺少 Agent Contract")
        else:
            if len(contract.promises) < 2:
                errors.append(f"Agent Contract 至少需要2个 promises，当前{len(contract.promises)}个")
            if len(contract.constraints) < 1:
                errors.append("Agent Contract 至少需要1个 constraint")

        if "## Rhythm Plan" not in plan_content:
            errors.append("缺少 Rhythm Plan 章节")

        has_rhythm_fields = all(
            f in plan_content
            for f in ["本章节奏类型", "本章在卷中的节奏角色", "与前一章的节奏关系"]
        )
        if not has_rhythm_fields:
            errors.append("Rhythm Plan 缺少必需字段（节奏类型、卷中角色、与前一章关系）")

        scenes = re.findall(r"### Scene \d+", plan_content)
        if len(scenes) < 2:
            errors.append(f"Scene List 至少需要2个场景，当前{len(scenes)}个")

        for s in range(1, len(scenes) + 1):
            scene_section_start = plan_content.find(f"### Scene {s}")
            if scene_section_start == -1:
                continue
            scene_section_end = plan_content.find(f"### Scene {s + 1}", scene_section_start)
            if scene_section_end == -1:
                scene_section = plan_content[scene_section_start:]
            else:
                scene_section = plan_content[scene_section_start:scene_section_end]

            for field in ["地点", "出场人物", "冲突", "预期字数"]:
                if field not in scene_section:
                    errors.append(f"Scene {s} 缺少字段: {field}")

        if "## Ending Hook" not in plan_content:
            errors.append("缺少 Ending Hook 章节")

        total_word_count = 0
        for m in re.finditer(r"预期字数[：:]\s*(\d+)", plan_content):
            total_word_count += int(m.group(1))

        if total_word_count > 0:
            if strategy and total_word_count < strategy.chapter_length.min:
                errors.append(f"预期总字数{total_word_count}低于策略最小值{strategy.chapter_length.min}")
            elif strategy and total_word_count > strategy.chapter_length.max:
                errors.append(f"预期总字数{total_word_count}超过策略最大值{strategy.chapter_length.max}")

        if rhythm:
            if not rhythm.rhythm_type:
                errors.append("Rhythm Plan 缺少 rhythm_type")
            if not rhythm.rhythm_role_in_volume:
                errors.append("Rhythm Plan 缺少 rhythm_role_in_volume")
            if not rhythm.relationship_with_previous:
                errors.append("Rhythm Plan 缺少 relationship_with_previous")

        if subplot_allocation and strategy and len(subplot_allocation.advanced) > strategy.subplot_policy.max_simultaneous:
            errors.append(
                f"子线推进数量{len(subplot_allocation.advanced)}超过策略上限{strategy.subplot_policy.max_simultaneous}"
            )

        return PlanValidationResult(len(errors) == 0, errors)
