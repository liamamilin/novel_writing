from __future__ import annotations

from pathlib import Path


def get_prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class PromptLoader:
    def __init__(self, prompts_dir: str | Path | None = None):
        self.prompts_dir = Path(prompts_dir) if prompts_dir else get_prompts_dir()
        self._cache: dict[str, str] = {}

    def load(self, template_name: str, variables: dict | None = None) -> str:
        if template_name in self._cache:
            template = self._cache[template_name]
        else:
            path = self.prompts_dir / f"{template_name}.md"
            if not path.exists():
                raise FileNotFoundError(f"Prompt template not found: {path}")
            template = path.read_text(encoding="utf-8")
            self._cache[template_name] = template

        if variables:
            for key, value in variables.items():
                template = template.replace("{{" + key + "}}", str(value))

        return template

    def list_templates(self) -> list[str]:
        return sorted(p.stem for p in self.prompts_dir.glob("*.md"))

    def clear_cache(self):
        self._cache.clear()
