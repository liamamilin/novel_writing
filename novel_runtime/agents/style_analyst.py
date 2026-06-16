from __future__ import annotations

from dataclasses import dataclass

import yaml

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.llm.output_validator import YAMLValidator
from novel_runtime.models.style import StyleAsset


@dataclass
class AdversarialTestResult:
    passed: bool = False
    deviation_paragraph: str = ""
    analysis: str = ""
    identified_deviation: bool = False


class StyleAnalystAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "style_analysis"

    def get_validator(self):
        return YAMLValidator(
            required_fields=[
                "narration", "sentence_rhythm", "dialogue_style",
                "description_density", "emotion_curve", "conflict_pattern",
                "chapter_opening", "chapter_ending", "scene_density", "avoid",
            ],
        )

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        try:
            data = yaml.safe_load(raw_output)
        except Exception as e:
            return AgentResult(success=False, raw_output=raw_output, validation_errors=[str(e)])

        if not isinstance(data, dict):
            return AgentResult(
                success=False, raw_output=raw_output,
                validation_errors=["Output is not a dictionary"],
            )

        style = StyleAsset(
            style_id=context.get("style_id", "auto_001"),
            style_name=data.get("style_name", context.get("style_name", "")),
            narration=data.get("narration", ""),
            sentence_rhythm=data.get("sentence_rhythm", ""),
            dialogue_style=data.get("dialogue_style", ""),
            description_density=data.get("description_density", ""),
            emotion_curve=data.get("emotion_curve", ""),
            conflict_pattern=data.get("conflict_pattern", ""),
            chapter_opening=data.get("chapter_opening", ""),
            chapter_ending=data.get("chapter_ending", ""),
            scene_density=data.get("scene_density", ""),
            avoid=data.get("avoid", []),
            conditional_rules=[],
        )
        if "conditional_rules" in data and isinstance(data["conditional_rules"], list):
            from novel_runtime.models.style import ConditionalRule
            try:
                style.conditional_rules = [ConditionalRule(**r) for r in data["conditional_rules"]]
            except Exception:
                pass
        return AgentResult(success=True, data=style, raw_output=raw_output)

    def analyze_style(self, samples: list[str], style_name: str) -> AgentResult:
        combined_samples = "\n---\n".join(samples)
        return self.execute(
            variables={"samples": combined_samples, "style_name": style_name},
            context={"style_name": style_name},
        )

    def generate_test_paragraph(self, style: StyleAsset, topic: str = "一场激烈的拍卖会") -> AgentResult:
        style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False)
        test_prompt = f"根据以下文风参数，写一段{topic}场景的文字（约500字）：\n\n{style_params}"
        try:
            text = self.provider.generate(test_prompt)
            return AgentResult(success=True, data=text, raw_output=text)
        except Exception as e:
            return AgentResult(success=False, raw_output="", validation_errors=[str(e)])

    def adversarial_test(self, style: StyleAsset, max_rounds: int = 3) -> AdversarialTestResult:
        style_params = yaml.dump(style.model_dump(), allow_unicode=True, default_flow_style=False)

        for round_num in range(max_rounds):
            try:
                deviation_prompt = (
                    f"根据以下文风参数，写一段刻意违反这些特征的文字（约500字）。\n"
                    f"违反方式：句式节奏相反、对白风格相反、情绪曲线平坦、缺少冲突推进。\n\n"
                    f"{style_params}"
                )
                deviation = self.provider.generate(deviation_prompt)

                analysis_prompt = f"分析以下文字的文风特征，输出YAML格式（narration, sentence_rhythm, dialogue_style, description_density, emotion_curve, conflict_pattern）：\n\n{deviation}"
                analysis = self.provider.generate(analysis_prompt)

                try:
                    analysis_data = yaml.safe_load(analysis)
                except Exception:
                    continue

                if not isinstance(analysis_data, dict):
                    continue

                passed = True
                for key in ["sentence_rhythm", "dialogue_style", "emotion_curve"]:
                    orig = getattr(style, key, "")
                    ana = analysis_data.get(key, "")
                    if orig and ana and orig[:8] in ana:
                        passed = False

                return AdversarialTestResult(
                    passed=passed,
                    deviation_paragraph=deviation,
                    analysis=analysis,
                    identified_deviation=not passed,
                )
            except Exception:
                continue

        return AdversarialTestResult(passed=False)
