from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from novel_runtime.models.character import CharacterState
from novel_runtime.models.hook import Hook
from novel_runtime.models.timeline import TimelineEvent
from novel_runtime.storage.base import read_yaml, write_yaml


def _states_dir(project_path: Path) -> Path:
    return project_path / "states"


def load_story_state(project_path: Path) -> dict:
    path = _states_dir(project_path) / "story_state.yaml"
    if not path.exists():
        return {}
    return read_yaml(path)


def save_story_state(project_path: Path, state: dict) -> Path:
    path = _states_dir(project_path) / "story_state.yaml"
    return write_yaml(path, state, overwrite=True)


def load_characters(project_path: Path) -> list[CharacterState]:
    path = _states_dir(project_path) / "characters.yaml"
    if not path.exists():
        return []
    data = read_yaml(path)
    return [CharacterState(**c) for c in data.get("characters", [])]


def save_characters(project_path: Path, characters: list[CharacterState]) -> Path:
    path = _states_dir(project_path) / "characters.yaml"
    return write_yaml(path, {"characters": [c.model_dump() for c in characters]}, overwrite=True)


def get_character_by_id(project_path: Path, character_id: str) -> CharacterState | None:
    characters = load_characters(project_path)
    for c in characters:
        if c.character_id == character_id:
            return c
    return None


def get_characters_by_chapter(project_path: Path, chapter_id: str) -> list[CharacterState]:
    characters = load_characters(project_path)
    try:
        ch_num = int(chapter_id.split("_")[-1])
    except (ValueError, IndexError):
        return characters
    result = []
    for c in characters:
        try:
            last_ch = int(c.last_seen_chapter.split("_")[-1]) if c.last_seen_chapter else -1
        except (ValueError, IndexError):
            result.append(c)
            continue
        if abs(last_ch - ch_num) <= 2:
            result.append(c)
    return result


def load_hooks(project_path: Path) -> list[Hook]:
    path = _states_dir(project_path) / "hooks.yaml"
    if not path.exists():
        return []
    data = read_yaml(path)
    return [Hook(**h) for h in data.get("hooks", [])]


def save_hooks(project_path: Path, hooks: list[Hook]) -> Path:
    path = _states_dir(project_path) / "hooks.yaml"
    return write_yaml(path, {"hooks": [h.model_dump() for h in hooks]}, overwrite=True)


def add_hook(project_path: Path, hook: Hook) -> Hook:
    hooks = load_hooks(project_path)
    if not hook.hook_id:
        hook.hook_id = f"H_{uuid4().hex[:6].upper()}"
    hooks.append(hook)
    save_hooks(project_path, hooks)
    return hook


def update_hook(project_path: Path, hook_id: str, updates: dict) -> Hook | None:
    hooks = load_hooks(project_path)
    for i, h in enumerate(hooks):
        if h.hook_id == hook_id:
            updated = h.model_copy(update=updates)
            hooks[i] = updated
            save_hooks(project_path, hooks)
            return updated
    return None


def get_hooks_by_status(project_path: Path, status: str) -> list[Hook]:
    return [h for h in load_hooks(project_path) if h.status == status]


def get_hooks_by_type(project_path: Path, hook_type: str) -> list[Hook]:
    return [h for h in load_hooks(project_path) if h.type == hook_type]


def get_open_hooks(project_path: Path) -> list[Hook]:
    return [h for h in load_hooks(project_path) if h.status == "open"]


def get_urgent_hooks(project_path: Path, current_chapter: int | None = None) -> list[Hook]:
    hooks = load_hooks(project_path)
    result = [h for h in hooks if h.priority == "high" or h.urgency in ("rising", "critical")]
    if current_chapter is not None:
        overdue = get_overdue_hooks(project_path, current_chapter)
        overdue_ids = {h.hook_id for h in overdue}
        for h in hooks:
            if h.hook_id in overdue_ids and h not in result:
                result.append(h)
    return result


def get_overdue_hooks(project_path: Path, current_chapter: int) -> list[Hook]:
    result = []
    for h in load_hooks(project_path):
        try:
            src = int(h.source_chapter.split("_")[-1]) if "_" in h.source_chapter else 9999
        except (ValueError, IndexError):
            continue
        if src + h.reader_patience < current_chapter and h.status in ("open", "triggered"):
            result.append(h)
    return result


def get_hooks_for_chapter(project_path: Path, chapter_number: int) -> dict:
    hooks = load_hooks(project_path)
    can_trigger = []
    must_not_forget = []
    should_resolve = []
    for h in hooks:
        is_open = h.status == "open"
        is_high = h.priority == "high" or h.urgency == "critical"
        range_low = 0
        range_high = 9999
        if h.planned_payoff_range:
            import re
            nums = re.findall(r"\d+", h.planned_payoff_range)
            if len(nums) >= 2:
                try:
                    range_low = int(nums[0])
                    range_high = int(nums[1])
                except ValueError:
                    pass
        if is_open and range_low <= chapter_number <= range_high:
            can_trigger.append(h)
        if is_open and is_high:
            must_not_forget.append(h)
    overdue = get_overdue_hooks(project_path, chapter_number)
    should_resolve = overdue
    return {"can_trigger": can_trigger, "must_not_forget": must_not_forget, "should_resolve": should_resolve}


def load_timeline(project_path: Path) -> list[TimelineEvent]:
    state = load_story_state(project_path)
    events = state.get("timeline", [])
    return [TimelineEvent(**e) for e in events]


def save_timeline(project_path: Path, events: list[TimelineEvent]) -> Path:
    state = load_story_state(project_path)
    state["timeline"] = [e.model_dump() for e in events]
    return save_story_state(project_path, state)
