# Phase 8: Chapter Planner (含节奏规划 + 子线分配 + Agent Contract)

## 前置条件
- Phase 7 完成（Context Pack 可用）
- Phase 2 完成（LLM 调用层可用）
- Phase 5 完成（Subplot/Hook 数据可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 8.1 | Chapter Plan 数据模型增强 | Phase 0 | 0.5天 |
| 8.2 | Chapter Planner Agent + Prompt | Phase 2, 7 | 3天 |
| 8.3 | Plan Validator | 8.1 | 1天 |
| 8.4 | Chapter Service (plan 部分) | 8.2, 8.3 | 1天 |
| 8.5 | Chapter Plan API 端点 | 8.4 | 0.5天 |
| 8.6 | 集成测试 | 8.5 | 1天 |

依赖关系图:
```text
Phase 0 → 8.1 → 8.3 → 8.4 → 8.5 → 8.6
Phase 2+7 → 8.2 → 8.4
```

---

## Task 8.1: Chapter Plan 数据模型增强

**文件:** `novel_runtime/models/chapter.py` (扩展)

**依赖:** Phase 0

### Contract: models.chapter 新增

**ChapterPlanRhythm:**
- `rhythm_type: Literal["escalation","explosion","pressure","resonance","transition_charge"]`
- `rhythm_role_in_volume: Literal["setup","escalation","climax","fallback","turning_point"]`
- `relationship_with_previous: Literal["continue_accelerate","contrast_adjust","parallel_advance"]`
- `satisfaction_point_timing: str` （如 "scene_2_mid", "scene_3_end"）
- `pressure_point_timing: str`

**SubplotAllocation:**
- `advanced: list[dict]` — 每个 dict: subplot_id, advancement_type, planned_content
- `idle: list[dict]` — 每个 dict: subplot_id, reason

**ChapterPlanContent (Markdown 内容结构):**
- 需包含: Agent Contract, Chapter Goal, Reader Promise, Rhythm Plan, Subplot Allocation, Conflict, Scene List, Ending Hook

这些模型用于在 Task 8.3 中校验 Chapter Planner 的输出。

**验收标准:**
- [ ] 新增模型字段完整
- [ ] 序列化/反序列化正确

---

## Task 8.2: Chapter Planner Agent + Prompt

**文件:**
- `novel_runtime/agents/chapter_planner.py`
- `prompts/chapter_plan.md`

**依赖:** Phase 2, 7

### Agent: ChapterPlannerAgent

**继承:** BaseAgent

#### `plan(context_pack: str, strategy: WritingStrategy) → ChapterPlanResult`

**Contract:**

**Input:**
- context_pack: Context Compiler 产出的完整 Context Pack Markdown
- strategy: Writing Strategy

**Output:**
- `ChapterPlanResult`: `plan_content: str` (Markdown), `rhythm: ChapterPlanRhythm`, `subplot_allocation: SubplotAllocation`, `agent_contract: AgentContract`

**Behavior:**
1. 加载 Prompt 模板 `chapter_plan`
2. 渲染变量: `{context_pack}`, `{strategy_summary}`
3. 调用 LLM
4. 解析输出:
   - 提取 Agent Contract 部分
   - 提取 Rhythm Plan 部分
   - 提取 Subplot Allocation 部分
   - 提取 Scene List 部分
5. 校验输出包含所有必需章节
6. 返回结构化结果

**Validator:** MarkdownValidator，必需章节:
- `Agent Contract`
- `Chapter Goal`
- `Reader Promise`
- `Rhythm Plan`
- `Subplot Allocation`
- `Conflict`
- `Scene List`
- `Ending Hook`

### Prompt Design: chapter_plan.md

**Input Specification:**
- `{{context_pack}}`: 完整 Context Pack（含叙事诊断）
- `{{strategy_summary}}`: Writing Strategy 关键参数摘要

**Output Specification:**
- Markdown 格式，必须包含上述必需章节
- Agent Contract 必须有明确的 promises 和 constraints
- Rhythm Plan 必须包含所有5个字段
- Scene List 每个场景必须有: 地点, 出场人物, 场景功能, 冲突, 转折, 输出, 预期字数

**Key Instructions:**
1. Rhythm Plan 必须与前一章节的节奏形成合理搭配（参考 Context Pack 中的 Narrative Diagnosis）
2. 如果前一章是递进型/爆发型，本章建议过渡蓄力或反差调节
3. Subplot Allocation 必须与 Writing Strategy 的策略一致
4. 每个场景必须产生至少一个状态变化
5. Ending Hook 必须保留继续阅读的驱动力
6. Agent Contract 的 promises 必须具体（不能是"写好这一章"这种模糊承诺）
7. Agent Contract 的 constraints 必须包含字数范围
8. Scene List 的预期字数总和必须与 strategy 的 chapter_length 一致

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 缺少 Agent Contract | 校验失败 | 提示"必须包含 Agent Contract 章节，明确 promises 和 constraints" |
| 节奏建议与前章相同 | 如连续递进 | 提示"本章节奏类型不得与前一章相同，请参考 Narrative Diagnosis" |
| 场景无状态变化 | 场景缺乏推动力 | 提示"每个场景必须产生至少一个状态变化" |
| 字数范围不符合策略 | 过多或过少 | 提示"场景预期字数总和必须在 {min}-{max} 之间" |
| Agent Contract 太模糊 | 如"写好这一章" | 提示"promises 必须具体化，如'包含主角与赵坤的正面冲突'" |

**Test Inputs:**
- Case 1: 第1章（无前文）→ 初始节奏 setup/escalation
- Case 2: 前一章是爆发型 → 建议反差调节或回响型
- Case 3: 有活跃子线需要推进 → Subplot Allocation 包含推进建议

**验收标准:**
- [ ] 生成包含所有必需章节的 chapter_plan.md
- [ ] Agent Contract 包含具体 promises 和 constraints
- [ ] Rhythm Plan 所有字段完整
- [ ] 节奏建议与前章形成合理搭配

---

## Task 8.3: Plan Validator

**文件:** `novel_runtime/compilers/plan_validator.py`

**依赖:** Task 8.1

### Contract: compiler.plan_validator.PlanValidator

#### `validate(plan_content: str, rhythm: ChapterPlanRhythm, subplot_allocation: SubplotAllocation, contract: AgentContract, context_pack: str, strategy: WritingStrategy) → ValidationResult`

**Behavior:**
1. 校验 Agent Contract 包含至少 2 个 promises 和 1 个 constraint
2. 校验 Rhythm Plan 所有字段非空
3. 校验 Scene List 至少 2 个场景
4. 校验每个场景包含必需字段（地点、出场人物、冲突、预期字数）
5. 校验结尾钩子存在且非空
6. 校验字数范围在 strategy.chapter_length 的 min-max 之间
7. 校验子线推进数量不超过 strategy.subplot_policy.max_simultaneous

**Output:**
- `ValidationResult`: `is_valid`, `errors: list[str]`

**验收标准:**
- [ ] 所有校验规则正确实现
- [ ] 合法计划通过校验
- [ ] 非法计划返回具体错误

**测试用例:**
- test_valid_plan: 合法计划 → is_valid=True
- test_missing_contract: 缺少 Agent Contract → is_valid=False
- test_missing_rhythm: 缺少 Rhythm Plan → is_valid=False
- test_too_few_scenes: 只有1个场景 → is_valid=False
- test_word_count_out_of_range: 字数超范围 → is_valid=False
- test_too_many_subplots: 子线推进超限 → is_valid=False

---

## Task 8.4: Chapter Service (plan 部分)

**文件:** `novel_runtime/services/chapter_service.py`

**依赖:** Task 8.2, 8.3

### Contract: services.chapter_service.ChapterService (plan 方法)

#### `generate_plan(project_id: str, chapter_number: int, chapter_goal: str = "") → ChapterPlanResult`

**Contract:**

**Input:**
- 项目 ID
- 章节号
- 本章目标（可选，如果未提供则从 Context Pack 的 Chapter Goal 中提取）

**Behavior:**
1. 检查章节状态（必须是 planned 或未创建）
2. 调用 ContextService.compile_context() 获取 context_pack
3. 加载 Writing Strategy
4. 调用 ChapterPlannerAgent.plan(context_pack, strategy)
5. 用 PlanValidator 校验输出
6. 保存 chapter_plan.md 到章节目录
7. 更新章节状态为 planned
8. 返回结构化结果

**Error cases:**
- 章节已 drafted/approved → `InvalidStateTransitionError`
- Context Pack 未编译 → 先自动编译

**验收标准:**
- [ ] 完整流程可跑通
- [ ] 文件保存正确
- [ ] 章节状态更新正确

---

## Task 8.5: Chapter Plan API 端点

**文件:** `novel_runtime/api/chapters.py`

### API 端点

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/plan`
- Request body: `{"chapter_goal": "...", "style_id": "style_001"}`
- Response: `{"plan_path": "...", "rhythm_type": "...", "agent_contract": {...}}`
- 异步执行，返回 task_id

**验收标准:**
- [ ] API 端点可调用
- [ ] 返回正确结果

---

## Task 8.6: 集成测试

**文件:** `tests/integration/test_chapter_planner.py`

**测试范围:**
- test_plan_first_chapter: 第1章规划 → 包含初始节奏
- test_plan_after_climax: 爆发型后的章节 → 建议反差节奏
- test_plan_with_subplots: 有活跃子线 → Subplot Allocation 包含推进建议
- test_plan_validation: 校验规则 → 合法计划通过，非法计划报错
- test_plan_service_full_flow: 完整流程 → context_pack + plan
- test_plan_api: HTTP 测试

**验收标准:**
- [ ] 所有集成测试通过
- [ ] Chapter Planner 生成的计划包含所有必需章节
- [ ] 节奏建议与 Narrative Diagnosis 关联
