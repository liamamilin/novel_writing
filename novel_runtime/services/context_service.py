from __future__ import annotations

import yaml

from novel_runtime.agents.context_compiler import ContextCompilerAgent
from novel_runtime.compiler.context_assembler import ContextAssembler
from novel_runtime.compiler.state_health_checker import StateHealthChecker
from novel_runtime.exceptions import StyleNotSetError
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import strategy_storage
from novel_runtime.storage.chapter_storage import save_chapter_file


class ContextService:
    def __init__(
        self,
        project_service: ProjectService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
    ):
        self.project_service = project_service
        self.assembler = ContextAssembler(project_service.storage_base)
        self.health_checker = StateHealthChecker()
        self.compiler_agent = ContextCompilerAgent(provider=provider, prompt_loader=prompt_loader)

    def compile_context(self, project_id: str, chapter_number: int, chapter_goal: str) -> dict:
        project = self.project_service.get_project(project_id)
        if not project.default_style_id:
            raise StyleNotSetError("No style set. Run style analysis first.")

        self.assembler.assemble(project_id, chapter_number, chapter_goal, project.default_style_id)

        project_path = self.project_service.get_project_path(project_id)
        strategy = strategy_storage.load_strategy(project_path)
        health_report = self.health_checker.check(project_path, chapter_number, strategy)

        raw_context_md = self.assembler.assemble_to_markdown(
            project_id, chapter_number, chapter_goal, project.default_style_id
        )

        health_report_yaml = yaml.dump(
            health_report.model_dump(), allow_unicode=True, default_flow_style=False, sort_keys=False,
        )

        ag = self.compiler_agent.compile(raw_context_md, health_report_yaml)
        context_pack_content = str(ag.data) if ag.success else ""

        save_chapter_file(project_path, chapter_number, "context_pack", context_pack_content)

        health_report_path = project_path / "chapters" / f"chapter_{chapter_number:03d}" / "state_health_report.yaml"
        health_report_path.parent.mkdir(parents=True, exist_ok=True)
        health_report_path.write_text(health_report_yaml, encoding="utf-8")

        return {
            "context_pack_path": str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "context_pack.md"),
            "health_report_path": str(project_path / "chapters" / f"chapter_{chapter_number:03d}" / "state_health_report.yaml"),
            "health_issues": len(health_report.issues),
        }
