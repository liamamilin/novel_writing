from __future__ import annotations

from pathlib import Path

from novel_runtime.exceptions import ProjectNotFoundError, StyleNotSetError
from novel_runtime.llm.token_counter import TokenBudgetManager, TokenCounter
from novel_runtime.models.context import RawContext
from novel_runtime.storage import (
    bible_storage,
    state_storage,
    strategy_storage,
    style_storage,
    subplot_storage,
)
from novel_runtime.storage.chapter_storage import load_chapter_file


class ContextAssembler:
    def __init__(self, storage_base: Path):
        self.storage_base = storage_base
        self.counter = TokenCounter()

    def _project_path(self, project_id: str) -> Path:
        return self.storage_base / project_id

    def _read_bible_summary(self, project_path: Path, filename: str, max_chars: int = 2000) -> str:
        try:
            content = bible_storage.load_bible_file(project_path, filename)
            return content[:max_chars]
        except FileNotFoundError:
            return ""

    def assemble(self, project_id: str, chapter_number: int, chapter_goal: str, style_id: str) -> RawContext:
        project_path = self._project_path(project_id)
        if not project_path.exists():
            raise ProjectNotFoundError(f"Project {project_id} not found")

        rc = RawContext(project_id=project_id, chapter_id=f"chapter_{chapter_number:03d}")

        rc.chapter_goal_content = chapter_goal

        try:
            style = style_storage.load_style_asset(project_path, style_id)
            rc.style_and_voices_content = (
                f"文风名称: {style.style_name}\n"
                f"叙述视角: {style.narration}\n"
                f"句子节奏: {style.sentence_rhythm}\n"
                f"对白风格: {style.dialogue_style}\n"
                f"描写密度: {style.description_density}\n"
                f"情绪曲线: {style.emotion_curve}\n"
                f"冲突模式: {style.conflict_pattern}\n"
                f"章节开头: {style.chapter_opening}\n"
                f"章节结尾风格: {style.chapter_ending}\n"
                f"场景密度: {style.scene_density}\n"
                f"禁用表达: {', '.join(style.avoid)}\n"
            )
            if style.conditional_rules:
                for rule in style.conditional_rules:
                    rc.style_and_voices_content += f"场景规则[{rule.condition}]: {rule.adjustments}\n"
        except FileNotFoundError:
            raise StyleNotSetError(f"Style {style_id} not found. Run style analysis first.")

        voices = style_storage.list_character_voices(project_path)
        voice_lines = []
        for v in voices:
            voice_lines.append(f"- {v.character_name}: {v.speech_patterns}")
        rc.character_state_content = "角色声音:\n" + "\n".join(voice_lines) if voice_lines else ""

        rc.story_context_content = self._read_bible_summary(project_path, "novel_bible.md", 1500)

        recent_chapters_lines = []
        for n in range(max(1, chapter_number - 3), chapter_number):
            try:
                summary = load_chapter_file(project_path, n, "draft")
                if summary:
                    first_line = summary.strip().split("\n")[0][:100]
                    recent_chapters_lines.append(f"第{n}章: {first_line}")
            except FileNotFoundError:
                continue
        rc.recent_chapters_content = "\n".join(recent_chapters_lines)

        story_state = state_storage.load_story_state(project_path)
        rc.current_state_content = (
            f"地点: {story_state.get('current_location', '')}\n"
            f"时间: {story_state.get('current_time', '')}\n"
            f"冲突: {story_state.get('current_conflict', '')}\n"
            f"主角状态: {story_state.get('protagonist_status', '')}\n"
        )

        characters = state_storage.load_characters(project_path)
        char_lines = []
        for c in characters:
            char_lines.append(
                f"{c.name}({c.role}): 目标={c.current_goal}, "
                f"位置={c.current_location}, 情绪={c.current_emotion}"
            )
        rc.character_state_content += "\n" + "\n".join(char_lines)

        hooks = state_storage.get_hooks_for_chapter(project_path, chapter_number)
        hook_lines = []
        for hook in hooks.get("can_trigger", []):
            hook_lines.append(f"[可触发] {hook.content}")
        for hook in hooks.get("must_not_forget", []):
            hook_lines.append(f"[不可忘] {hook.content}")
        for hook in hooks.get("should_resolve", []):
            hook_lines.append(f"[待回收] {hook.content}")
        rc.hooks_content = "\n".join(hook_lines)

        subplots = subplot_storage.load_subplots(project_path)
        subplot_lines = []
        for s in subplots:
            if s.status != "resolved":
                subplot_lines.append(f"- {s.name}({s.type}): 状态={s.status}")
        rc.subplots_content = "\n".join(subplot_lines)

        try:
            strategy = strategy_storage.load_strategy(project_path)
            rc.writing_strategy_content = (
                f"字数范围: {strategy.chapter_length.min}-{strategy.chapter_length.max}\n"
                f"节奏策略: {strategy.pacing_strategy.type}\n"
                f"同时子线: {strategy.subplot_policy.max_simultaneous}\n"
                f"最大开放伏笔: {strategy.hook_policy.max_open_hooks}\n"
            )
        except FileNotFoundError:
            pass

        sections = {
            "style_and_voices": rc.style_and_voices_content,
            "story_context": rc.story_context_content,
            "recent_chapters": rc.recent_chapters_content,
            "current_state": rc.current_state_content,
            "character_state": rc.character_state_content,
            "hooks": rc.hooks_content,
            "subplots": rc.subplots_content,
            "chapter_goal": rc.chapter_goal_content,
            "writing_strategy": rc.writing_strategy_content,
        }

        budget_mgr = TokenBudgetManager()
        allocated = budget_mgr.allocate(sections)
        summary = budget_mgr.get_budget_summary(sections)

        rc.style_and_voices_content = allocated.get("style_and_voices", "")
        rc.story_context_content = allocated.get("story_context", "")
        rc.recent_chapters_content = allocated.get("recent_chapters", "")
        rc.current_state_content = allocated.get("current_state", "")
        rc.character_state_content = allocated.get("character_state", "")
        rc.hooks_content = allocated.get("hooks", "")
        rc.subplots_content = allocated.get("subplots", "")
        rc.chapter_goal_content = allocated.get("chapter_goal", "")
        rc.writing_strategy_content = allocated.get("writing_strategy", "")

        total = 0
        budget_used = {}
        for name in sections:
            actual_content = getattr(rc, f"{name}_content", "")
            tokens = self.counter.count_tokens(actual_content)
            budget_used[name] = tokens
            total += tokens
            if name in summary:
                budget_used[f"{name}_truncated"] = summary[name].get("truncated", False)

        rc.total_tokens = total
        rc.budget_used = budget_used

        return rc

    def apply_degradation_strategy(self, sections: dict[str, str], token_stats: dict[str, int], budget: int) -> dict[str, str]:
        result = dict(sections)
        total_tokens = sum(token_stats.values())
        if total_tokens <= budget:
            return result

        degradation_levels = {
            "recent_chapters": [
                lambda t: t,
                lambda t: "\n".join(t.split("\n")[:len(t.split("\n")) * 2 // 3]),
                lambda t: "\n".join(t.split("\n")[:len(t.split("\n")) // 2]),
            ],
            "character_state": [
                lambda t: t,
                lambda t: "\n".join(line for line in t.split("\n") if "目标" in line or "位置" in line or "名称" in line or "角色" in line),
                lambda t: "\n".join(line[:60] for line in t.split("\n") if ("目标" in line or "位置" in line) and len(line) > 5),
            ],
            "hooks": [
                lambda t: t,
                lambda t: "\n".join(line for line in t.split("\n") if "[不可忘]" in line or "[待回收]" in line),
                lambda t: "\n".join(line for line in t.split("\n") if "[待回收]" in line),
            ],
            "subplots": [
                lambda t: t,
                lambda t: "\n".join(line for line in t.split("\n") if "-" in line[:5] and "状态=" in line),
                lambda t: "",
            ],
        }

        for name in ["subplots", "hooks", "character_state", "recent_chapters"]:
            if name not in result:
                continue
            levels = degradation_levels.get(name, [lambda t: t])
            for level in reversed(levels):
                degraded = level(result[name])
                degraded_tokens = self.counter.count_tokens(degraded)
                current_total = sum(self.counter.count_tokens(v) for v in result.values())
                if degraded_tokens <= token_stats.get(name, 0) and current_total <= budget:
                    result[name] = degraded
                    break
                if degraded_tokens < token_stats.get(name, 0):
                    result[name] = degraded
                    break

        return result

    def assemble_to_markdown(self, project_id: str, chapter_number: int, chapter_goal: str, style_id: str) -> str:
        rc = self.assemble(project_id, chapter_number, chapter_goal, style_id)
        voice_content = ""
        state_content = rc.character_state_content
        if rc.character_state_content.startswith("角色声音:"):
            idx = rc.character_state_content.find("\n\n")
            if idx > 0:
                voice_content = rc.character_state_content[:idx].replace("角色声音:\n", "")
                state_content = rc.character_state_content[idx:].strip()

        md = f"""# Context Pack for {rc.chapter_id}

## 项目信息
项目ID: {rc.project_id}

## 文风资产
{rc.style_and_voices_content}
{voice_content}

## 全局故事上下文
{rc.story_context_content}

## 最近章节
{rc.recent_chapters_content}

## 当前状态
{rc.current_state_content}

## 角色状态
{state_content}

## 伏笔
{rc.hooks_content}

## 子线
{rc.subplots_content}

## 本章目标
{rc.chapter_goal_content}

## 写作策略
{rc.writing_strategy_content}

---
Token 统计: {rc.total_tokens} tokens
"""
        return md
