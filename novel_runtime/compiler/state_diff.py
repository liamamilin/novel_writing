from __future__ import annotations

from pathlib import Path


class StateDiff:
    def __init__(self, has_changes: bool = False, change_segments: list[dict] | None = None, summary: str = ""):
        self.has_changes = has_changes
        self.change_segments = change_segments or []
        self.summary = summary


class StateDiffer:
    def diff(self, draft_path: Path, final_path: Path) -> StateDiff:
        draft_content = ""
        final_content = ""

        try:
            if draft_path.exists():
                draft_content = draft_path.read_text(encoding="utf-8")
        except Exception:
            pass

        try:
            if final_path.exists():
                final_content = final_path.read_text(encoding="utf-8")
        except Exception:
            pass

        if not draft_content.strip() and final_content.strip():
            return StateDiff(
                has_changes=True,
                change_segments=[{"location": "全文", "type": "added", "content": final_content[:200]}],
                summary=f"用户从头写，共{len(final_content)}字",
            )

        if draft_content == final_content:
            return StateDiff(has_changes=False, change_segments=[], summary="无修改")

        draft_lines = draft_content.split("\n")
        final_lines = final_content.split("\n")

        import difflib
        diff = list(difflib.ndiff(draft_lines, final_lines))

        added = 0
        removed = 0
        modified = 0
        segments = []

        i = 0
        while i < len(diff):
            line = diff[i]
            if line.startswith("+ "):
                added += 1
                segments.append({"location": f"line_{i}", "type": "added", "content": line[2:][:100]})
            elif line.startswith("- "):
                removed += 1
                segments.append({"location": f"line_{i}", "type": "removed", "content": line[2:][:100]})
            elif line.startswith("? "):
                modified += 1
            i += 1

        summary = f"用户修改了{modified}处，删除了{removed}处，添加了{added}处"
        return StateDiff(
            has_changes=(added + removed + modified > 0),
            change_segments=segments[:20],
            summary=summary,
        )
