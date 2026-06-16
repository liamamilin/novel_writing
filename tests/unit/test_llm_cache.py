from pathlib import Path

from novel_runtime.llm.cache import LLMCache


def test_cache_set_and_get(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=3600)
    key = cache.make_key("test prompt", "", None, 0.7, "gpt-4")
    cache.set(key, "hello world", "gpt-4")
    result = cache.get(key)
    assert result == "hello world"


def test_cache_miss(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=3600)
    key = cache.make_key("never set", "", None, 0.7, "gpt-4")
    result = cache.get(key)
    assert result is None


def test_cache_key_different_prompts(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=3600)
    k1 = cache.make_key("prompt one", "", None, 0.7, "gpt-4")
    k2 = cache.make_key("prompt two", "", None, 0.7, "gpt-4")
    assert k1 != k2


def test_cache_stats(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=3600)
    key = cache.make_key("stats test", "", None, 0.7, "gpt-4")
    cache.set(key, "data", "gpt-4")
    cache.get(key)
    s = cache.stats()
    assert s["total_entries"] == 1
    assert s["total_hits"] >= 1


def test_cache_clear(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=3600)
    key = cache.make_key("clear test", "", None, 0.7, "gpt-4")
    cache.set(key, "data", "gpt-4")
    assert cache.stats()["total_entries"] == 1
    count = cache.clear()
    assert count == 1
    assert cache.stats()["total_entries"] == 0


def test_cache_ttl_no_expiry_when_zero(tmp_path: Path) -> None:
    db = str(tmp_path / "cache.db")
    cache = LLMCache(db, ttl=0)
    key = cache.make_key("no ttl", "", None, 0.7, "gpt-4")
    cache.set(key, "data", "gpt-4")
    result = cache.get(key)
    assert result == "data"
