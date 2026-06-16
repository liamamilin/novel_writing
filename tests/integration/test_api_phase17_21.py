from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.models.project import ProjectCreate
from novel_runtime.services.project_service import ProjectService


@pytest.fixture
def client(tmp_path):
    from novel_runtime.main import app
    storage_dir = tmp_path / "projects"
    storage_dir.mkdir(parents=True, exist_ok=True)
    db = Database(str(tmp_path / "test.db"))
    db.init_db()
    settings = Settings(storage_base_path=str(storage_dir), db_path="")
    app.state.db = db
    app.state.settings = settings
    with TestClient(app) as c:
        yield c


@pytest.fixture
def project_with_chapters(client):
    storage_base = Path(client.app.state.settings.storage_base_path)
    db = client.app.state.db
    svc = ProjectService(db, storage_base)
    proj = svc.create_project(ProjectCreate(
        project_name="PhaseTest", genre="fantasy", idea="test",
        target_reader="adult", core_selling_point="test", target_style="default",
    ))
    svc.create_chapter(proj.project_id, 1)
    return proj.project_id


@pytest.fixture
def mock_provider(monkeypatch):
    provider = MagicMock()
    provider.generate.return_value = '{"pace_score": 7, "satisfaction_score": 8, "feedback": "Good pace"}'
    provider.generate_with_usage.return_value = (provider.generate.return_value, {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
    monkeypatch.setattr("novel_runtime.llm.provider.create_provider", lambda _: provider)
    return provider


# ---- SSE streaming ----

def test_sse_missing_context_pack(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/chapters/1/draft/stream", json={})
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")
    assert "error" in resp.text or "data:" in resp.text


# ---- Drafts versions ----

def test_drafts_list_empty(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.get(f"/api/projects/{pid}/chapters/1/drafts")
    assert resp.status_code == 200
    data = resp.json()
    assert "drafts" in data
    assert data["drafts"] == []
    assert data["draft_count"] is not None


def test_drafts_save_and_list(client, project_with_chapters):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    from novel_runtime.storage.chapter_storage import save_draft_version
    save_draft_version(storage_base / pid, 1, 1, "# v1 content")
    save_draft_version(storage_base / pid, 1, 2, "# v2 content")

    resp = client.get(f"/api/projects/{pid}/chapters/1/drafts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["drafts"]) == 2
    assert data["drafts"][0]["version_id"] == 1
    assert data["drafts"][1]["version_id"] == 2
    assert data["active_draft_id"] is not None


def test_drafts_get_content(client, project_with_chapters):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    from novel_runtime.storage.chapter_storage import save_draft_version
    save_draft_version(storage_base / pid, 1, 1, "# Hello test")

    resp = client.get(f"/api/projects/{pid}/chapters/1/drafts/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["draft_id"] == 1
    assert "Hello" in data["content"]


def test_drafts_get_missing(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.get(f"/api/projects/{pid}/chapters/1/drafts/99")
    assert resp.status_code == 404


def test_drafts_promote(client, project_with_chapters):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    from novel_runtime.storage.chapter_storage import save_draft_version
    save_draft_version(storage_base / pid, 1, 1, "# v1")
    save_draft_version(storage_base / pid, 1, 2, "# v2")

    resp = client.post(f"/api/projects/{pid}/chapters/1/drafts/2/promote")
    assert resp.status_code == 200
    assert resp.json()["active_draft_id"] == 2


# ---- Export ----

def test_export_txt(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/export", json={"format": "txt"})
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["format"] == "txt"


def test_export_unsupported_format(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/export", json={"format": "pdf"})
    assert resp.status_code == 400


def test_export_download(client, project_with_chapters):
    pid = project_with_chapters
    export_resp = client.post(f"/api/projects/{pid}/export", json={"format": "txt"})
    task_id = export_resp.json()["task_id"]

    resp = client.get(f"/api/projects/{pid}/exports/{task_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")


# ---- Events & Share ----

def test_events_list(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.get(f"/api/projects/{pid}/events")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert len(data["events"]) >= 1  # create_project + create_chapter
    assert data["events"][0]["action"] in ("project_created", "create_project", "chapter_created", "create_chapter")


def test_share_create(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/share", json={"actor": "tester"})
    assert resp.status_code == 200
    data = resp.json()
    assert "share_token" in data
    assert data["share_token"].startswith("share_")
    assert "/shared/" in data["url"]


def test_shared_read_project(client, project_with_chapters):
    pid = project_with_chapters
    share_resp = client.post(f"/api/projects/{pid}/share", json={})
    token = share_resp.json()["share_token"]

    resp = client.get(f"/api/shared/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == pid


def test_shared_read_chapters(client, project_with_chapters):
    pid = project_with_chapters
    share_resp = client.post(f"/api/projects/{pid}/share", json={})
    token = share_resp.json()["share_token"]

    resp = client.get(f"/api/shared/{token}/chapters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chapters"]) >= 1


def test_shared_invalid_token(client):
    resp = client.get("/api/shared/invalid_token_xxx")
    assert resp.status_code == 404


def test_shared_chapter_content(client, project_with_chapters):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    from novel_runtime.storage.chapter_storage import save_chapter_file
    save_chapter_file(storage_base / pid, 1, "draft", "# Shared draft content")

    share_resp = client.post(f"/api/projects/{pid}/share", json={})
    token = share_resp.json()["share_token"]

    resp = client.get(f"/api/shared/{token}/chapters/1?file_type=draft")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chapter_number"] == 1
    assert "Shared" in data["content"]


def test_shared_chapter_not_found(client, project_with_chapters):
    pid = project_with_chapters
    share_resp = client.post(f"/api/projects/{pid}/share", json={})
    token = share_resp.json()["share_token"]

    resp = client.get(f"/api/shared/{token}/chapters/99?file_type=draft")
    assert resp.status_code == 404


# ---- Multi-reader (mock LLM) ----

def test_multi_reader_basic(client, project_with_chapters, mock_provider):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    from novel_runtime.storage.chapter_storage import save_chapter_file
    save_chapter_file(storage_base / pid, 1, "draft", "# Chapter one draft")

    resp = client.post(f"/api/projects/{pid}/chapters/1/review/multi-reader", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) >= 1


def test_multi_reader_no_draft(client, project_with_chapters, mock_provider):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/chapters/1/review/multi-reader", json={})
    assert resp.status_code == 400
    assert "draft" in resp.json()["detail"]
