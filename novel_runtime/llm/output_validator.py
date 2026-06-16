from __future__ import annotations

import json
import re
from typing import Any

import yaml

from novel_runtime.llm.provider import LLMProvider


class ValidationResult:
    def __init__(
        self,
        is_valid: bool,
        parsed_data: Any = None,
        errors: list[str] | None = None,
        raw_output: str = "",
    ):
        self.is_valid = is_valid
        self.parsed_data = parsed_data
        self.errors = errors or []
        self.raw_output = raw_output


class BaseValidator:
    def validate(self, raw_output: str) -> ValidationResult:
        raise NotImplementedError

    def get_schema(self) -> dict:
        return {}


class YAMLValidator(BaseValidator):
    def __init__(
        self,
        required_fields: list[str] | None = None,
        optional_fields: list[str] | None = None,
        field_types: dict[str, type] | None = None,
    ):
        self.required_fields = required_fields or []
        self.optional_fields = optional_fields or []
        self.field_types = field_types or {}

    def validate(self, raw_output: str) -> ValidationResult:
        errors = []
        try:
            data = yaml.safe_load(raw_output)
        except yaml.YAMLError as e:
            return ValidationResult(False, errors=[f"Invalid YAML: {e}"], raw_output=raw_output)

        if not isinstance(data, dict):
            return ValidationResult(False, errors=["Output is not a YAML dictionary"], raw_output=raw_output)

        for field in self.required_fields:
            if field not in data:
                errors.append(f"Missing required field: '{field}'")
            elif data[field] is None:
                errors.append(f"Required field '{field}' is null")

        for field, expected_type in self.field_types.items():
            if field in data and data[field] is not None:
                if expected_type is list and not isinstance(data[field], list):
                    errors.append(f"Field '{field}' should be a list")
                elif expected_type is dict and not isinstance(data[field], dict):
                    errors.append(f"Field '{field}' should be a dict")

        return ValidationResult(len(errors) == 0, parsed_data=data, errors=errors, raw_output=raw_output)


class MarkdownValidator(BaseValidator):
    def __init__(
        self,
        required_sections: list[str] | None = None,
        section_content_rules: dict[str, str] | None = None,
    ):
        self.required_sections = required_sections or []
        self.section_content_rules = section_content_rules or {}

    def validate(self, raw_output: str) -> ValidationResult:
        errors = []
        for section in self.required_sections:
            if f"## {section}" not in raw_output:
                errors.append(f"Missing required section: '## {section}'")

        for section, rule in self.section_content_rules.items():
            if f"## {section}" in raw_output:
                pass

        return ValidationResult(len(errors) == 0, parsed_data=raw_output, errors=errors, raw_output=raw_output)


class FixInstructionsValidator(BaseValidator):
    def __init__(self):
        self.allowed_severities = {"critical", "moderate", "low"}
        self.allowed_actions = {"replace", "insert", "delete", "rewrite"}

    def validate(self, raw_output: str) -> ValidationResult:
        errors = []
        try:
            data = yaml.safe_load(raw_output)
        except yaml.YAMLError as e:
            return ValidationResult(False, errors=[f"Invalid YAML: {e}"], raw_output=raw_output)

        if not isinstance(data, dict):
            return ValidationResult(False, errors=["Output is not a dictionary"], raw_output=raw_output)

        instructions = data.get("fix_instructions", [])
        if not isinstance(instructions, list):
            return ValidationResult(False, errors=["'fix_instructions' must be a list"], raw_output=raw_output)

        for i, inst in enumerate(instructions):
            if not isinstance(inst, dict):
                errors.append(f"Instruction {i} is not a dictionary")
                continue
            for field in ["fix_id", "type", "severity", "location", "problem", "action"]:
                if field not in inst:
                    errors.append(f"Instruction {i} missing '{field}'")
            sev = inst.get("severity", "")
            if sev and sev not in self.allowed_severities:
                errors.append(f"Instruction {i} invalid severity '{sev}'")
            act = inst.get("action", "")
            if act and act not in self.allowed_actions:
                errors.append(f"Instruction {i} invalid action '{act}'")

        return ValidationResult(len(errors) == 0, errors=errors, raw_output=raw_output)


class ContinuityReviewValidator(MarkdownValidator):
    def __init__(self):
        super().__init__(required_sections=["Summary", "Issues"])


class QualityReviewValidator(MarkdownValidator):
    def __init__(self):
        super().__init__(required_sections=["Score", "Main Problems", "Rewrite Suggestions"])


def validate_with_retry(
    validator: BaseValidator,
    llm_output: str,
    max_retries: int = 1,
    provider: LLMProvider | None = None,
    original_prompt: str = "",
    original_system_prompt: str = "",
) -> ValidationResult:
    result = validator.validate(llm_output)
    if result.is_valid:
        return result

    for attempt in range(max_retries):
        if provider is None:
            break

        retry_prompt = (
            f"{original_prompt}\n\n"
            f"Previous output had format errors. Please fix:\n"
            f"{chr(10).join(result.errors)}\n\n"
            f"Make sure the output follows the required format exactly."
        )

        new_output = provider.generate(retry_prompt, system_prompt=original_system_prompt)
        result = validator.validate(new_output)
        if result.is_valid:
            return result

    return result


def extract_json(raw: str) -> dict:
    stripped = raw.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if m:
        stripped = m.group(1).strip()
    brace_start = stripped.find("{")
    brace_end = stripped.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        stripped = stripped[brace_start:brace_end + 1]
    return json.loads(stripped)
