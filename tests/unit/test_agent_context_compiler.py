from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from novel_runtime.agents.context_compiler import ContextCompilerAgent
from novel_runtime.llm.prompt_loader import PromptLoader


@pytest.fixture
def agent(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "context_compile.md").write_text("RAW: {{raw_context}}\nHEALTH: {{health_report}}")
    mock = MagicMock()
    mock.generate_with_usage.return_value = (
        "## Project Info\ntest\n## Style Asset\ntest\n## Character Voices\ntest\n"
        "## Global Story Context\ntest\n## Narrative Diagnosis\ntest\n## Subplot Status\ntest\n"
        "## Recent Chapters\ntest\n## Current State\ntest\n## Character State\ntest\n"
        "## Hooks\ntest\n## Chapter Goal\ntest\n## Generation Constraints\ntest\n## Writing Strategy\ntest",
        {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
    )
    loader = PromptLoader(prompts_dir)
    return ContextCompilerAgent(provider=mock, prompt_loader=loader)


class TestContextCompilerAgent:
    def test_compile(self, agent):
        result = agent.compile("raw context here", "health report here")
        assert result.success
        assert "Project Info" in result.data

    def test_validator_sections(self, agent):
        validator = agent.get_validator()
        sections = [
            "Project Info", "Style Asset", "Character Voices",
            "Global Story Context", "Narrative Diagnosis",
            "Subplot Status", "Recent Chapters", "Current State",
            "Character State", "Hooks", "Chapter Goal",
            "Generation Constraints", "Writing Strategy",
        ]
        for s in sections:
            assert s in validator.required_sections
