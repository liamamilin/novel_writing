from __future__ import annotations

from pathlib import Path

from novel_runtime.models.bible import BibleUpdateItem, BibleUpdateProposal
from novel_runtime.storage import bible_storage


class BibleUpdateService:
    def detect_update_need(
        self,
        project_path: Path,
        world_updates: list[str],
        character_updates: list[dict],
    ) -> BibleUpdateProposal | None:
        items = []

        for wu in world_updates:
            if any(kw in wu for kw in ["新势力", "新组织", "隐藏", "秘密", "重大"]):
                items.append(BibleUpdateItem(
                    file="world_setting.md",
                    section="势力设定",
                    change=wu,
                    reason="章节中出现了新的世界观设定",
                ))

        new_char_count = 0
        for cu in character_updates:
            char_id = cu.get("character_id", "")
            if char_id.startswith("new_") or "_new" in char_id:
                new_char_count += 1

        if new_char_count > 0:
            items.append(BibleUpdateItem(
                file="character_profiles.md",
                section="角色列表",
                change=f"新增{new_char_count}个角色",
                reason="章节中引入了新角色",
            ))

        if not items:
            return None

        proposal = BibleUpdateProposal(
            project_id=project_path.name if project_path else "",
            trigger_chapter="",
            items=items,
        )
        return proposal

    def apply_update(self, project_path: Path, proposal: BibleUpdateProposal) -> dict:
        updated_files = []
        for item in proposal.items:
            try:
                content = bible_storage.load_bible_file(project_path, item.file)
                updated = content + f"\n\n<!-- 更新: {item.change} ({item.reason}) -->"
                bible_storage.save_bible_file(project_path, item.file, updated)
                updated_files.append(item.file)
            except FileNotFoundError:
                bible_storage.save_bible_file(project_path, item.file, f"# {item.section}\n\n{item.change}\n")
                updated_files.append(item.file)

        if updated_files:
            bible_storage.add_changelog_entry(project_path, "auto", [
                f"Bible更新: {', '.join(updated_files)}"
            ])
            bible_storage.freeze_bible_version(project_path, bible_storage.get_bible_version(project_path))

        version = bible_storage.get_bible_version(project_path)
        return {"bible_version": version, "updated_files": updated_files}
