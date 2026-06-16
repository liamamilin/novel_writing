from __future__ import annotations

from novel_runtime.models.fix_instructions import FixInstruction, FixInstructionsFile


def merge_reviews(
    continuity_issues: list[dict] | None = None,
    quality_scores: dict | None = None,
    quality_problems: list[dict] | None = None,
    cross_chapter_text: str = "",
    reader_sim_text: str = "",
    styled_draft: str = "",
) -> FixInstructionsFile:
    instructions = []
    fix_counter = 0
    continuity_issues = continuity_issues or []
    quality_scores = quality_scores or {}
    quality_problems = quality_problems or []

    for issue in continuity_issues:
        severity = issue.get("severity", "moderate")
        if severity not in ("critical", "moderate"):
            continue
        fix_counter += 1
        action = _infer_action(issue.get("type", ""), severity)
        instructions.append(FixInstruction(
            fix_id=f"FIX_{fix_counter:03d}",
            type=_map_type(issue.get("type", "continuity_violation")),
            severity=severity,
            location=issue.get("location", ""),
            problem=issue.get("problem", ""),
            action=action,
            original_text=_extract_original(styled_draft, issue.get("location", "")),
            suggested_fix=issue.get("suggested_fix", ""),
            constraint=_infer_constraint(issue.get("type", "")),
        ))

    for dim, score in quality_scores.items():
        try:
            score_val = int(score) if not isinstance(score, int) else score
        except (ValueError, TypeError):
            continue
        if score_val < 6 and fix_counter < 10:
            fix_counter += 1
            instructions.append(FixInstruction(
                fix_id=f"FIX_{fix_counter:03d}",
                type=f"quality_{dim}",
                severity="moderate" if score_val < 4 else "low",
                location=f"全文（{dim}评分{score_val}/10）",
                problem=f"{dim}评分偏低（{score_val}/10）",
                action="rewrite",
                suggested_fix=f"改进{dim}表现",
            ))

    if "连续同节奏" in cross_chapter_text and fix_counter < 10:
        fix_counter += 1
        instructions.append(FixInstruction(
            fix_id=f"FIX_{fix_counter:03d}",
            type="rhythm_repetition",
            severity="moderate",
            location="跨章节奏",
            problem="连续多章节奏类型相同",
            action="rewrite",
            suggested_fix="下一章使用不同的节奏类型",
            constraint="节奏必须与前章形成对比",
        ))

    import re
    risk_match = re.search(r"弃书风险[评分]*[：:]\s*(\d+)", reader_sim_text)
    if risk_match:
        risk_score = int(risk_match.group(1))
        if risk_score > 6 and fix_counter < 10:
            fix_counter += 1
            instructions.append(FixInstruction(
                fix_id=f"FIX_{fix_counter:03d}",
                type="reader_risk",
                severity="critical" if risk_score > 8 else "moderate",
                location="全文",
                problem=f"读者弃书风险评分{risk_score}/10",
                action="rewrite",
                suggested_fix="根据读者模拟结果，调整章节开头或结尾吸引力",
            ))

    instructions.sort(key=lambda x: {"critical": 0, "moderate": 1, "low": 2}.get(x.severity, 3))
    instructions = instructions[:10]

    return FixInstructionsFile(fix_instructions=instructions)


def merge_all_reviews(
    continuity_issues: list[dict],
    quality_scores: dict,
    quality_problems: list[dict],
    cross_chapter_text: str,
    reader_sim_text: str,
    styled_draft: str = "",
) -> FixInstructionsFile:
    return merge_reviews(
        continuity_issues=continuity_issues,
        quality_scores=quality_scores,
        quality_problems=quality_problems,
        cross_chapter_text=cross_chapter_text,
        reader_sim_text=reader_sim_text,
        styled_draft=styled_draft,
    )


def _infer_action(issue_type: str, severity: str) -> str:
    if "continuity" in issue_type.lower() or "人物" in issue_type:
        return "replace"
    if "时间" in issue_type or "timeline" in issue_type.lower():
        return "rewrite"
    return "rewrite"


def _map_type(issue_type: str) -> str:
    mapping = {
        "人物状态": "continuity_character",
        "时间线": "continuity_timeline",
        "地点": "continuity_location",
        "能力": "continuity_ability",
        "信息边界": "continuity_information",
        "伏笔": "continuity_hook",
        "世界规则": "continuity_world",
        "章节目标": "continuity_goal",
    }
    for key, value in mapping.items():
        if key in issue_type:
            return value
    return "continuity_violation"


def _infer_constraint(issue_type: str) -> str:
    if "人物" in issue_type:
        return "保持人物设定一致性"
    if "时间" in issue_type:
        return "保持时间线逻辑"
    if "伏笔" in issue_type:
        return "保持伏笔状态一致性"
    return "保持剧情事实不变"


def _extract_original(draft: str, location: str) -> str:
    if not draft or not location:
        return ""
    lines = draft.split("\n")
    for i, line in enumerate(lines):
        if location in line:
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            return "\n".join(lines[start:end])
    return ""
