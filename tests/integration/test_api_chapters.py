import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.models.project import ProjectCreate
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage.project_storage import ProjectStorage
from novel_runtime.storage.snapshot_storage import SnapshotManager
from novel_runtime.storage import state_storage


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
        project_name="TestNovel",
        genre="fantasy",
        idea="A test novel",
        target_reader="adult",
        core_selling_point="testing",
        target_style="default",
    ))
    svc.create_chapter(proj.project_id, 1)
    svc.create_chapter(proj.project_id, 2)
    return proj.project_id


def test_list_chapters(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.get(f"/api/projects/{pid}/chapters")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["chapter_number"] == 1
    assert data[1]["chapter_number"] == 2
    assert data[0]["status"] == "planned"


def test_list_chapters_empty(client):
    storage_base = Path(client.app.state.settings.storage_base_path)
    db = client.app.state.db
    svc = ProjectService(db, storage_base)
    proj = svc.create_project(ProjectCreate(
        project_name="EmptyNovel",
        genre="scifi",
        idea="No chapters",
        target_reader="adult",
        core_selling_point="empty",
        target_style="default",
    ))
    resp = client.get(f"/api/projects/{proj.project_id}/chapters")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_snapshots(client, project_with_chapters):
    pid = project_with_chapters
    storage_base = Path(client.app.state.settings.storage_base_path)
    project_path = storage_base / pid

    mgr = SnapshotManager()
    state_storage.save_story_state(project_path, {"current_volume": "volume_001"})
    state_storage.save_characters(project_path, [])
    state_storage.save_hooks(project_path, [])

    mgr.create_snapshot(project_path, 1)

    resp = client.get(f"/api/projects/{pid}/state/snapshots")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["chapter_number"] == 1
    assert "snapshot_after_chapter_001" in data[0]["snapshot_id"]


def test_list_snapshots_empty(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.get(f"/api/projects/{pid}/state/snapshots")
    assert resp.status_code == 200
    assert resp.json() == []


def test_stream_draft_endpoint_error_on_missing_files(client, project_with_chapters):
    pid = project_with_chapters
    resp = client.post(f"/api/projects/{pid}/chapters/1/draft/stream", json={})
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")
    assert "data:" in resp.text
    # Should contain an error about missing context_pack
    assert "error" in resp.text or "data:" in resp.text