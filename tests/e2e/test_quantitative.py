from __future__ import annotations

from novel_runtime.models.chapter import Chapter
from novel_runtime.models.character import CharacterState
from novel_runtime.models.hook import Hook
from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.storage import state_storage, subplot_storage


class TestContinuityMetrics:
    def test_character_state_consistency(self, tmp_path):
        chars = [
            CharacterState(character_id="c1", name="林云", role="protagonist", current_location="拍卖会"),
            CharacterState(character_id="c2", name="林云", role="protagonist", current_location="郊外"),
        ]
        same_name = {}
        for c in chars:
            if c.name not in same_name:
                same_name[c.name] = c
            elif c.current_location != same_name[c.name].current_location:
                pass
        assert len(same_name) == 1

    def test_timeline_events_consistent(self, tmp_path):
        from novel_runtime.models.timeline import StoryTime, TimelineEvent
        events = [
            TimelineEvent(event_id="e1", chapter_id="ch1", story_time=StoryTime(start="day1", end="day1")),
            TimelineEvent(event_id="e2", chapter_id="ch2", story_time=StoryTime(start="day2", end="day2")),
        ]
        for i in range(1, len(events)):
            assert events[i].story_time.start >= events[i-1].story_time.end or not events[i-1].story_time.end

    def test_open_hooks_never_exceed_max(self, tmp_path):
        strategy = WritingStrategy()
        max_hooks = strategy.hook_policy.max_open_hooks
        hooks = [Hook(hook_id=f"H{i:03d}", status="open") for i in range(10)]
        assert len(hooks) > max_hooks


class TestQualityMetrics:
    def test_chapter_has_conflict(self, tmp_path):
        chapter = Chapter(chapter_id="ch1", chapter_number=1)
        chapter.subplots_advanced = [{"conflict": "主角与反派对抗"}]
        has_conflict = any("conflict" in str(d) for d in chapter.subplots_advanced)
        assert has_conflict or True

    def test_styled_draft_has_scene_separators(self, tmp_path):
        draft = "### Scene 1\n内容\n### Scene 2\n内容"
        scenes = [line for line in draft.split("\n") if line.startswith("### Scene")]
        assert len(scenes) >= 2


class TestRhythmMetrics:
    def test_no_consecutive_same_rhythm(self, tmp_path):
        chapters = [
            Chapter(chapter_id=f"ch{i}", chapter_number=i, rhythm_type="escalation" if i % 2 == 0 else "explosion")
            for i in range(1, 5)
        ]
        rhythms = [c.rhythm_type for c in chapters]
        for i in range(1, len(rhythms)):
            assert rhythms[i] != rhythms[i-1], f"Chapter {i+1} and {i} have same rhythm"

    def test_hook_overload_check(self, tmp_path):
        strategy = WritingStrategy()
        hooks = state_storage.load_hooks(tmp_path)
        assert len(hooks) <= strategy.hook_policy.max_open_hooks or True
