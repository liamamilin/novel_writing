from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest


SAMPLE_STYLE_TEXT = """
林云推开拍卖会的大门，刺眼的水晶灯光倾泻而下。他的目光扫过大厅，每一个角落都藏着算计和阴谋。

"这位先生，请出示邀请函。"门口的保安拦住了他。

林云微微一笑，从口袋里掏出一张烫金请柬。保安接过一看，脸色瞬间变了——这是顶级的贵宾邀请函，整个云海市只有三张。

"请...请进！"

林云收起请柬，头也不回地走进了大厅。他知道，今天这场拍卖会，将会改变一切。

角落里，一个身穿黑色西装的男人正盯着他。那人嘴角微微上扬，"有意思，终于来了个能看的。"

拍卖台上，主持人敲响了木槌。"各位贵宾，欢迎来到云海慈善拍卖会。今晚的第一件拍卖品，是一枚来历不明的古玉..."

林云的瞳孔骤然收缩。那枚古玉上刻着的纹路，和他脑海中那个古老的传承图案一模一样。

"五百万。"他直接举牌。

全场哗然。一枚起拍价只有五十万的古玉，居然有人直接出价五百万。

"这位先生出价五百万！还有更高的吗？"

"一千万。"角落里那个黑衣男人懒洋洋地开口。

林云转头看向他，两人的目光在空中碰撞，仿佛擦出了火花。

这场拍卖会，注定不会平静。
"""


@pytest.fixture
def real_llm_provider():
    try:
        import os
        api_key = os.environ.get("LLM_API_KEY", "")
        if api_key:
            from novel_runtime.llm.openai_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider(
                base_url=os.environ.get("NWR_LLM_BASE_URL", "https://api.openai.com/v1"),
                model=os.environ.get("NWR_LLM_MODEL", "gpt-4"),
                api_key_env="LLM_API_KEY",
            )
    except Exception:
        pass
    pytest.skip("LLM_API_KEY not set, skipping real LLM tests")


@pytest.fixture
def mock_e2e_provider():
    provider = MagicMock()
    provider.generate_with_usage.return_value = (
        "mock output",
        {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
    )
    provider.generate.return_value = "mock output"
    return provider


@pytest.fixture
def test_style_sample(tmp_path):
    path = tmp_path / "style_sample_urban.txt"
    path.write_text(SAMPLE_STYLE_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def full_project(tmp_path, mock_e2e_provider):
    from novel_runtime.db.database import Database
    from novel_runtime.services.project_service import ProjectService
    from novel_runtime.models.project import ProjectCreate

    db = Database(str(tmp_path / "test.db"))
    db.init_db()
    project_svc = ProjectService(db, tmp_path)
    project = project_svc.create_project(ProjectCreate(
        project_name="测试项目",
        genre="都市修仙",
        idea="一个被抛弃的年轻人获得古老传承",
        target_reader="喜欢快节奏爽文的读者",
        core_selling_point="都市修仙逆袭",
    ))
    return project, project_svc, tmp_path
