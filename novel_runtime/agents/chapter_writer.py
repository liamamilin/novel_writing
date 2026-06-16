from __future__ import annotations

import yaml

from novel_runtime.agents.base import BaseAgent, AgentResult
from novel_runtime.models.style import StyleAsset, CharacterVoice
from novel_runtime.models.chapter import AgentContract


class ChapterWriteResult:
    def __init__(self, draft: str, annotations: dict, contract_check: dict):
        self.draft = draft
        self.annotations = annotations
        self.contract_check = contract_check


class ChapterWriterOutputResult:
    def __init__(self, draft: str, annotations: dict, contract_check: dict, validation_errors: list[str] | None = None):
        self.draft = draft
        self.annotations = annotations
        self.contract_check = contract_check
        self.validation_errors = validation_errors or []
        self.success = len(self.validation_errors) == 0


class ChapterWriterAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "chapter_write"

    def get_validator(self):
        return None

    def validate_composite(self, raw_output: str) -> list[str]:
        errors = []
        from novel_runtime.llm.output_validator import MarkdownValidator
        from novel_runtime.llm.state_annotations_validator import StateAnnotationsValidator

        md_validator = MarkdownValidator()
        md_result = md_validator.validate(raw_output)
        if not md_result.is_valid:
            errors.extend(md_result.errors)

        if "---ANNOTATIONS---" in raw_output:
            annotations_part = raw_output.split("---ANNOTATIONS---")[1]
            sa_validator = StateAnnotationsValidator()
            sa_result = sa_validator.validate(annotations_part)
            if not sa_result.is_valid:
                errors.extend(sa_result.errors)

        return errors

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        errors = self.validate_composite(raw_output)
        if errors:
            return AgentResult(success=False, raw_output=raw_output, validation_errors=errors)

        annotations = {}
        contract_check = {"promises_fulfilled": [], "constraints_followed": [], "all_fulfilled": False}

        parts = raw_output.split("---ANNOTATIONS---")
        draft = parts[0].strip() if parts else raw_output

        if len(parts) > 1:
            try:
                annotations = yaml.safe_load(parts[1]) or {}
            except Exception:
                annotations = {}

        contract_text = context.get("contract_text", "")
        if contract_text:
            promises = context.get("promises", [])
            constraints = context.get("constraints", [])
            contract_check["promises_fulfilled"] = [
                p[:30] in draft for p in promises
            ] if promises else []
            contract_check["constraints_followed"] = [
                c[:30] in draft for c in constraints
            ] if constraints else []
            contract_check["all_fulfilled"] = (
                all(contract_check["promises_fulfilled"]) and
                all(contract_check["constraints_followed"])
            )

        result = ChapterWriteResult(draft, annotations, contract_check)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def parse_output(self, raw_output: str, contract: AgentContract | None = None) -> ChapterWriterOutputResult:
        """Deterministically parse raw LLM output into draft + annotations + contract check.

        This method does NOT call the LLM. It extracts the draft body, YAML annotations,
        and runs contract verification on the existing text.
        """
        errors = self.validate_composite(raw_output)
        if errors:
            return ChapterWriterOutputResult(draft=raw_output, annotations={}, contract_check={}, validation_errors=errors)

        parts = raw_output.split("---ANNOTATIONS---")
        draft = parts[0].strip() if parts else raw_output

        annotations = {}
        if len(parts) > 1:
            try:
                annotations = yaml.safe_load(parts[1]) or {}
            except Exception:
                annotations = {}

        contract_check = {"promises_fulfilled": [], "constraints_followed": [], "all_fulfilled": False}
        if contract:
            contract_check["promises_fulfilled"] = [
                p[:30] in draft for p in contract.promises
            ] if contract.promises else []
            contract_check["constraints_followed"] = [
                c[:30] in draft for c in contract.constraints
            ] if contract.constraints else []
            contract_check["all_fulfilled"] = (
                all(contract_check["promises_fulfilled"]) and
                all(contract_check["constraints_followed"])
            )

        return ChapterWriterOutputResult(draft=draft, annotations=annotations, contract_check=contract_check)

    def write(
        self,
        context_pack: str,
        chapter_plan: str,
        style: StyleAsset,
        character_voices: list[CharacterVoice],
        contract: AgentContract,
    ) -> AgentResult:
        style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False)
        voice_params = "\n".join(
            f"- {v.character_name}: {v.speech_patterns}" for v in character_voices
        )
        contract_promises = "\n".join(f"- {p}" for p in contract.promises)
        contract_constraints = "\n".join(f"- {c}" for c in contract.constraints)

        return self.execute(
            variables={
                "context_pack": context_pack,
                "chapter_plan": chapter_plan,
                "style_params": style_params,
                "voice_params": voice_params,
                "contract_promises": contract_promises,
                "contract_constraints": contract_constraints,
            },
            context={
                "contract_text": chapter_plan,
                "promises": contract.promises,
                "constraints": contract.constraints,
            },
        )
