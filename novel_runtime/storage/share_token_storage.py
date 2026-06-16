from __future__ import annotations
import json
from pathlib import Path


class ShareTokenStorage:
    def __init__(self, storage_base: Path):
        self._base = storage_base

    def _tokens_path(self) -> Path:
        p = self._base / "share_tokens.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save(self, token: str, project_id: str) -> None:
        path = self._tokens_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"token": token, "project_id": project_id}, ensure_ascii=False) + "\n")

    def resolve(self, token: str) -> str | None:
        path = self._tokens_path()
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry["token"] == token:
                        return entry["project_id"]
        return None
