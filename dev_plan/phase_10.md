# Phase 10: Continuity Auditor + Quality Auditor

## 前置条件
- Phase 7 完成（Context Pack 可用）
- Phase 9 完成（Chapter Draft/Styled Draft 可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 10.1 | Review 数据模型 + Validator | Phase 0 | 0.5天 |
| 10.2 | Continuity Auditor Agent + Prompt | Phase 2, 9 | 2天 |
| 10.3 | Quality Auditor Agent + Prompt | Phase 2, 3, 9 | 2天 |
| 10.4 | Fix Instruction Merger (确定性代码) | 10.1 | 1天 |
| 10.5 | Review Service 编排层 | 10.2, 10.3, 10.4 | 1天 |
| 10.6 | Review API 端点 | 10.5 | 0.5天 |
| 10.7 | 集成测试 | 10.6 | 1天 |

依赖关系图:
```text
Phase 0 → 10.1 → 10.4 → 10.5 → 10.6 → 10.7
Phase 2+9 → 10.2 → 10.5
Phase 2+3+9 → 10.3 → 10.5
```

---

## Task 10.1: Review 数据模型 + Validator

**文件:** `novel_runtime/models/fix_instructions.py` (已在 Phase 0 定义，实现 Validator)

### Contract: output_validator.FixInstructionsValidator(BaseValidator)

**Behavior:**
- 校验 YAML 格式
- 校验每个 fix_instructions 包含: fix_id, type, severity, location, problem, action
- severity 必须是 critical/moderate/low 之一
- action 必须是 replace/insert/delete/rewrite 之一

### Contract: Review Validator (组合)

**ContinuityReviewValidator:** MarkdownValidator
- 必需章节: Summary, Issues (至少1个)
- 每个 Issue 包含: type, location, problem, suggested_fix

**QualityReviewValidator:** MarkdownValidator
- 必需章节: Score, Main Problems, Rewrite Suggestions
- Score 包含: opening, conflict, pacing, satisfaction, style, ending_hook (1-10)
- compared_to_previous 包含: tension_change, pacing_change, style_consistency

**验收标准:**
- [ ] 修复指令格式校验正确
- [ ] 连续性审查校验正确
- [ ] 质量审查校验正确

---

## Task 10.2: Continuity Auditor Agent + Prompt

**文件:**
- `novel_runtime/agents/continuity_auditor.py`
- `prompts/continuity_review.md`

### Agent: ContinuityAuditorAgent

#### `review(styled_draft: str, context_pack: str, character_state: list[CharacterState], timeline: list[TimelineEvent], hooks: list[Hook], world_setting: str) → ContinuityReviewResult`

**Contract:**

**Input:**
- styled_draft: 润色后的章节正文
- context_pack: 上下文包
- character_state: 当前角色状态
- timeline: 时间线
- hooks: 当前伏笔状态
- world_setting: 世界观设定

**Output:**
- `ContinuityReviewResult`: `review_content: str`, `issues: list[dict]`
- issues: 每个 dict 包含 type, location, problem, severity, suggested_fix

**审查维度:**
1. 人物状态一致性（位置、情绪、能力）
2. 时间线一致性（时间流逝、地点变化）
3. 地点一致性
4. 能力体系一致性
5. 人物已知信息边界（角色不应该知道还没发生/听说的事）
6. 伏笔状态一致性
7. 世界规则一致性
8. 章节目标完成度

### Prompt Design: continuity_review.md

**Key Instructions:**
1. 逐句检查角色位置是否与前文矛盾
2. 检查角色提及的信息是否其已知范围内
3. 检查时间线是否有跳跃或矛盾
4. 检查能力使用是否与角色当前等级匹配
5. 检查伏笔引用是否与当前状态一致
6. 检查世界设定是否有矛盾
7. 对每个问题给出具体位置和修改建议
8. severity: critical（必须修改）、moderate（建议修改）、low（可忽略）
9. 输出格式必须包含 Summary 和 Issues 章节

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 没有发现任何问题 | 过于宽松 | 提示"请更仔细审查，至少检查8个维度" |
| 问题没有具体位置 | 如"某处有问题" | 提示"每个 Issue 的 location 必须指向具体段落或场景" |
| 缺少修改建议 | 只有问题描述 | 提示"每个 Issue 必须包含 suggested_fix" |

---

## Task 10.3: Quality Auditor Agent + Prompt

**文件:**
- `novel_runtime/agents/quality_auditor.py`
- `prompts/quality_review.md`

### Agent: QualityAuditorAgent

#### `review(styled_draft: str, chapter_plan: str, style_asset: StyleAsset) → QualityReviewResult`

**Contract:**

**Input:**
- styled_draft: 润色后的章节正文
- chapter_plan: 章节规划（含节奏要求）
- style_asset: 文风资产

**Output:**
- `QualityReviewResult`: `review_content: str`, `scores: dict`, `problems: list[dict]`

**审查维度:**
1. 开头吸引力 (1-10)
2. 冲突强度 (1-10)
3. 节奏推进 (1-10)
4. 爽点释放 (1-10)
5. 对白有效性 (1-10)
6. 信息密度 (1-10)
7. 场景变化 (1-10)
8. 人物行为目的 (1-10)
9. 结尾钩子 (1-10)
10. 文风一致性 (1-10)

**与前章比较维度:**
- tension_change: 上升/平稳/下降
- pacing_change: 加快/不变/减慢
- style_consistency: 一致/偏离

### Prompt Design: quality_review.md

**Key Instructions:**
1. 每个维度必须给出 1-10 分数和具体理由
2. 分数必须参考 style_asset 中的文风标准
3. Main Problems 列出最重要的 3-5 个问题
4. Rewrite Suggestions 给出具体的修改建议
5. compared_to_previous 必须基于 chapter_plan 中的节奏信息判断
6. 不要只写"还行"、"可以"等模糊评价，必须具体

---

## Task 10.4: Fix Instruction Merger (确定性代码)

**文件:** `novel_runtime/compiler/fix_instruction_merger.py`

### Contract: compiler.fix_instruction_merger.merge_reviews

**Input:**
- `continuity_review: ContinuityReviewResult`
- `quality_review: QualityReviewResult`

**Output:**
- `FixInstructionsFile` — 合并后的结构化修复指令

**Behavior:**
1. 提取 continuity_review 中 severity=critical 和 moderate 的问题
2. 提取 quality_review 中分数 < 6 的维度
3. 为每个问题生成 FixInstruction:
   - fix_id: 自动编号 (FIX_001, FIX_002, ...)
   - type: 从审查类型映射 (continuity_violation, pacing_issue, etc.)
   - severity: 从审查 severity 映射
   - location: 从审查 location 提取
   - problem: 审查问题描述
   - action: 根据类型推断 (continuity → replace, pacing → rewrite, etc.)
   - original_text: 从 styled_draft 中按 location 提取（如果可能）
   - suggested_fix: 从审查 suggested_fix 提取
   - constraint: 根据类型推断（如 continuity 问题约束"保持后续逻辑不变"）
4. 按 severity 排序: critical → moderate → low
5. 去重（相似问题合并）

**Guarantees:**
- 修复指令数量不超过 10 条（超过则只保留 critical + 前 moderate）
- 每条指令的 action 类型是合法的 FixAction 枚举值

**验收标准:**
- [ ] 合并逻辑正确
- [ ] severity 排序正确
- [ ] 去重逻辑正确
- [ ] action 类型映射正确

---

## Task 10.5: Review Service 编排层

**文件:** `novel_runtime/services/review_service.py`

### Contract: services.review_service.ReviewService

#### `review_chapter(project_id: str, chapter_number: int, review_types: list[str] = ["continuity", "quality"]) → ReviewResult`

**Contract:**

**Input:**
- 项目 ID, 章节号, 审查类型列表

**Behavior:**
1. 加载 styled_draft.md
2. 加载 context_pack.md, characters, timeline, hooks, world_setting
3. 加载 chapter_plan.md, style_asset
4. 按类型调用审查 Agent:
   - "continuity" → ContinuityAuditorAgent
   - "quality" → QualityAuditorAgent
5. 保存各审查报告
6. 合并生成 fix_instructions.yaml
7. 更新章节状态为 reviewed
8. 返回结果

**Output:**
- `ReviewResult`: `review_paths: dict`, `fix_instructions_path: str`, `has_critical_issues: bool`

**验收标准:**
- [ ] 审查流程可跑通
- [ ] 报告文件保存正确
- [ ] 修复指令合并正确

---

## Task 10.6: Review API 端点

**文件:** `novel_runtime/api/chapters.py` (扩展)

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/review`
- Request: `{"review_types": ["continuity", "quality"]}`
- Response: `{"review_paths": {...}, "fix_instructions_path": "...", "has_critical_issues": true}`

**验收标准:**
- [ ] API 端点可调用
- [ ] 返回正确结果

---

## Task 10.7: 集成测试

**测试范围:**
- test_continuity_review: Mock LLM → 审查报告包含 Issues
- test_quality_review: Mock LLM → 审查报告包含 Score 和 Problems
- test_fix_merger: 两个审查结果 → 合并修复指令
- test_review_service: 完整审查流程
- test_review_api: HTTP 测试

**验收标准:**
- [ ] 所有集成测试通过
- [ ] 连续性审查覆盖8个维度
- [ ] 质量审查包含10个评分维度
- [ ] 修复指令合并逻辑正确
