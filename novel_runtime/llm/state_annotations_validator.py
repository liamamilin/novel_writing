from __future__ import annotations

import yaml

from novel_runtime.llm.output_validator import BaseValidator, ValidationResult
from novel_runtime.models.state_annotations import StateAnnotationsFile


class StateAnnotationsValidator(BaseValidator):
    def __init__(self, required_annotation_types: list[str] | None = None):
        self.required_types = required_annotation_types or [
            "character_state_change", "new_hook", "subplot_advance",
        ]

    def validate(self, raw_output: str) -> ValidationResult:
        errors = []
        try:
            data = yaml.safe_load(raw_output)
        except yaml.YAMLError as e:
            return ValidationResult(False, errors=[f"Invalid YAML: {e}"], raw_output=raw_output)

        if not isinstance(data, dict):
            return ValidationResult(False, errors=["Output is not a dictionary"], raw_output=raw_output)

        annotations = data.get("annotations", [])
        if not isinstance(annotations, list):
            errors.append("'annotations' must be a list")
            return ValidationResult(False, errors=errors, raw_output=raw_output)

        found_types = set()
        for i, ann in enumerate(annotations):
            if not isinstance(ann, dict):
                errors.append(f"Annotation {i} is not a dictionary")
                continue
            ann_type = ann.get("type", "")
            if not ann_type:
                errors.append(f"Annotation {i} missing 'type'")
            else:
                found_types.add(ann_type)
            if not ann.get("location", ""):
                errors.append(f"Annotation {i} missing 'location'")
            if not ann.get("change", ""):
                errors.append(f"Annotation {i} missing 'change'")

        for req_type in self.required_types:
            if req_type not in found_types:
                errors.append(f"Missing required annotation type: '{req_type}'")

        if errors:
            return ValidationResult(False, errors=errors, raw_output=raw_output)
        try:
            StateAnnotationsFile(**data)
        except Exception as e:
            return ValidationResult(False, errors=[f"Invalid StateAnnotationsFile: {e}"], raw_output=raw_output)

        return ValidationResult(True, parsed_data=data, raw_output=raw_output)
