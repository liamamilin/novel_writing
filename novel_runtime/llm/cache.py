from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class LLMCache:
    def __init__(self, db_path: str, ttl: int = 86400):
        self.db_path = db_path
        self.ttl = ttl
        self._init_db()

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS llm_cache (
                cache_key TEXT PRIMARY KEY,
                response_text TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at REAL NOT NULL,
                hit_count INTEGER DEFAULT 0
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_cache_created ON llm_cache(created_at)"
        )
        conn.commit()
        conn.close()

    @staticmethod
    def make_key(
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        model: str = "",
    ) -> str:
        raw = json.dumps({
            "p": prompt,
            "sp": system_prompt,
            "ctx": context,
            "t": temperature,
            "m": model,
        }, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT response_text, created_at FROM llm_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            conn.close()
            return None
        text, created = row
        if self.ttl > 0 and time.time() - created > self.ttl:
            conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None
        conn.execute("UPDATE llm_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (key,))
        conn.commit()
        conn.close()
        return text

    def set(self, key: str, text: str, model: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT OR REPLACE INTO llm_cache (cache_key, response_text, model, created_at, hit_count)
               VALUES (?, ?, ?, ?, 0)""",
            (key, text, model, time.time()),
        )
        conn.commit()
        conn.close()

    def stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0]
        hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) FROM llm_cache").fetchone()[0]
        conn.close()
        return {"total_entries": total, "total_hits": hits}

    def clear(self) -> int:
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0]
        conn.execute("DELETE FROM llm_cache")
        conn.commit()
        conn.close()
        return count
