from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from novel_runtime.models.event import ProjectEvent


class EventStorage:
    def __init__(self, storage_base: Path):
        self._base = storage_base

    def _events_path(self, project_id: str) -> Path:
        p = self._base / project_id / "events.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def record(self, project_id: str, action: str, actor: str = "system", details: dict | None = None) -> ProjectEvent:
        event = ProjectEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            project_id=project_id,
            action=action,
            actor=actor,
            details=details or {},
        )
        line = json.dumps(event.model_dump(mode="json", exclude_none=True), ensure_ascii=False)
        path = self._events_path(project_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return event

    def list_events(self, project_id: str, limit: int = 50, offset: int = 0) -> list[ProjectEvent]:
        path = self._events_path(project_id)
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        events = []
        for line in lines[offset:offset + limit]:
            if line.strip():
                data = json.loads(line)
                events.append(ProjectEvent(**data))
        return events
