from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from novel_runtime.cli.main import app

runner = CliRunner()


class TestCLI:
    def test_init_command(self, tmp_path):
        with patch("novel_runtime.cli.main._get_services") as mock_get:
            settings = MagicMock()
            settings.storage_base_path = str(tmp_path)
            settings.db_path = str(tmp_path / "test.db")
            provider = MagicMock()
            loader = MagicMock()
            db = MagicMock()
            project_svc = MagicMock()
            project_svc.create_project.return_value.project_id = "novel_test_001"
            project_svc.get_project_path.return_value = tmp_path / "novel_test_001"
            mock_get.return_value = (settings, provider, loader, project_svc, db, tmp_path)

            result = runner.invoke(app, [
                "init", "--name", "测试小说", "--genre", "都市修仙",
            ])
            assert result.exit_code == 0
            assert "项目" in result.stdout

    def test_health_command(self, tmp_path):
        with patch("novel_runtime.cli.main._get_services") as mock_get:
            settings = MagicMock()
            settings.storage_base_path = str(tmp_path)
            provider = MagicMock()
            loader = MagicMock()
            db = MagicMock()
            project_svc = MagicMock()
            project_svc.get_project_path.return_value = tmp_path
            mock_get.return_value = (settings, provider, loader, project_svc, db, tmp_path)

            result = runner.invoke(app, ["health", "--project", "test"])
            assert result.exit_code == 0
            assert "检查" in result.stdout or "健康" in result.stdout

    def test_next_suggest(self, tmp_path):
        with patch("novel_runtime.cli.main._get_services") as mock_get:
            settings = MagicMock()
            provider = MagicMock()
            loader = MagicMock()
            db = MagicMock()
            project_svc = MagicMock()
            project_svc.get_project_path.return_value = tmp_path
            mock_get.return_value = (settings, provider, loader, project_svc, db, tmp_path)

            result = runner.invoke(app, ["next-suggest", "--project", "test"])
            assert result.exit_code == 0
            assert "建议" in result.stdout or "下一章" in result.stdout

    def test_style_analyze(self, tmp_path):
        with patch("novel_runtime.cli.main._get_services") as mock_get:
            settings = MagicMock()
            settings.storage_base_path = str(tmp_path)
            provider = MagicMock()
            loader = MagicMock()
            db = MagicMock()
            project_svc = MagicMock()
            project_svc.get_project_path.return_value = tmp_path
            mock_get.return_value = (settings, provider, loader, project_svc, db, tmp_path)

            sample_file = tmp_path / "sample.txt"
            sample_file.write_text("样本文本")

            result = runner.invoke(app, [
                "style", "analyze",
                "--project", "test",
                "--sample", str(sample_file),
                "--name", "测试文风",
            ])
            assert result.exit_code == 0
