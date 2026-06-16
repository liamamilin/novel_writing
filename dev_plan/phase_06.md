# Phase 6: Context Assembler (确定性代码) + Token 预算管理

## 前置条件
- Phase 0-5 完成
- 特别是 Phase 5 的数据结构 (Hook, Subplot, Strategy) 可用

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 6.1 | Context Assembler 素材读取 | Phase 1, 5 | 1天 |
| 6.2 | Token 预算分配 + 截断 | Phase 2.4 | 1天 |
| 6.3 | 降级策略实现 | 6.2 | 0.5天 |
| 6.4 | Context Assembler 组装 | 6.1, 6.2, 6.3 | 1天 |
| 6.5 | Context Assembler 测试 (用真实数据) | 6.4 | 1天 |

依赖关系图:
```text
Phase 1 + 5 → 6.1
Phase 2.4 → 6.2 → 6.3
6.1 + 6.2 + 6.3 → 6.4 → 6.5
```

---

## Task 6.1: Context Assembler 素材读取

**文件:** `novel_runtime/compiler/context_assembler.py`

**依赖:** Phase 1 (Storage), Phase 5 (数据结构)

### Contract: compiler.context_assembler.ContextAssembler

**初始化参数:**
- `project_path: Path`
- `token_counter: TokenCounter`

#### `assemble(project_id: str, chapter_id: str, chapter_goal: str, style_id: str) → RawContext`

**Input:**
- `project_id`: 项目 ID
- `chapter_id`: 章节标识 (如 "chapter_023")
- `chapter_goal`: 本章目标 (用户输入)
- `style_id`: 文风资产 ID

**Output:**
- `RawContext` model (包含各部分内容和 token 统计)

**Behavior (步骤):**

1. **读取项目信息**
   - 加载 `project.yaml` → 项目元信息
   - 提取: 项目名称、类型、当前卷、当前章节

2. **读取文风资产**
   - 加载 `style_assets/{style_id}.yaml`
   - 提取: 全部文风参数 + conditional_rules

3. **读取角色声音**
   - 加载 `style_assets/character_voices/*.yaml`
   - 筛选: 本章出场角色的声音资产

4. **读取全局故事上下文**
   - 加载 `bible/novel_bible.md` → 核心卖点、主线目标
   - 加载 `bible/world_setting.md` → 世界规则 (精简)
   
5. **读取最近章节摘要**
   - 加载最近3章的 `states/` + `chapters/chapter_NNN/` 的 summary
   - 精简版: 只读取每章的 summary 字段和节奏标记

6. **读取当前状态**
   - 加载 `states/story_state.yaml` → 全局状态
   - 提取: 当前地点、当前时间、当前冲突、主角状态

7. **读取角色状态**
   - 加载 `states/characters.yaml`
   - 筛选: 本章相关角色（基于 `get_characters_by_chapter`）
   - 对每个角色提取: 目标、已知信息、未知信息、叙事功能

8. **读取伏笔**
   - 调用 `HookService.get_chapter_hooks(project_id, chapter_number)`
   - 获取: can_trigger, must_not_forget, should_resolve

9. **读取子线状态**
   - 加载 `subplots/subplot_registry.yaml`
   - 筛选: 活跃子线
   - 提取: 每条子线的当前阶段、上次推进章节、推进建议

10. **读取写作策略**
    - 加载 `strategies/writing_strategy.yaml`
    - 提取: 全部策略参数

11. **组装原始素材**
    - 将以上各部分组织为 `RawContext` model
    - 计算每部分的 token 数
    - 记录 `budget_used: dict[str, int]`

**Error cases:**
- 项目不存在 → `ProjectNotFoundError`
- 文风资产不存在 → `StyleNotSetError`，建议先运行 style_analysis
- 章节状态文件不存在 → 使用默认值（首个章节情况）

**Guarantees:**
- 每个部分的 token 数被记录
- 总 token 数不超过 `config.context_token_budget`
- 如果超过预算，由 Task 6.2 的截断逻辑处理

**验收标准:**
- [ ] 所有素材源正确读取
- [ ] 角色筛选逻辑正确
- [ ] 伏笔分类正确
- [ ] token 统计准确

**测试用例:**
- test_assemble_full: 完整项目（3章历史）→ RawContext 包含所有部分
- test_assemble_first_chapter: 第1章（无历史）→ 使用最小上下文
- test_assemble_no_style: 未设置文风 → StyleNotSetError
- test_assemble_role_filtering: 10个角色，3个相关 → 只返回3个角色的声音

---

## Task 6.2: Token 预算分配 + 截断

**文件:** `novel_runtime/llm/token_counter.py` (扩展)

**依赖:** Phase 2.4

### Contract: TokenBudgetManager 扩展

#### `allocate_for_context(sections: dict[str, str], config: Settings) → dict[str, str]`
- Input: 各部分名称到内容的映射
- Output: 裁剪后的各部分内容

**Behavior:**
- 总预算: `config.context_token_budget`
- 分配比例: `config.context_budget_allocation` (默认比例见 overview)
- 优先级: `config.context_priority_order` (默认优先级见 overview)
- 超预算时按优先级从低到高截断
- 每部分截断到分配预算的 80%
- 截断位置在句子边界（句号、感叹号、问号、换行）

#### `summarize_section(content: str, level: str) → str`
- Input: 完整内容 + 精简级别 (full / reduced / minimal)
- Output: 精简后的内容

**Behavior:**
- `full`: 原样返回
- `reduced`: 只保留关键段落（每段第一句 + 最后一句）
- `minimal`: 只保留每节标题 + 第一句摘要

**Guarantees:**
- 返回内容总 token 数 ≤ budget
- 截断位置在句子边界
- 每部分至少保留 50 tokens（即使超预算）

**验收标准:**
- [ ] 预算内内容完整保留
- [ ] 超预算按优先级截断
- [ ] 截断在句子边界
- [ ] 每部分至少保留 50 tokens

**测试用例:**
- test_allocate_within_budget: 总量 5000 < budget 8000 → 原样返回
- test_allocate_over_budget: 总量 12000 > budget 8000 → 低优先级截断
- test_summarize_reduced: reduced 级别 → 保留关键段落
- test_summarize_minimal: minimal 级别 → 只保留标题+摘要
- test_minimum_tokens: 即使超预算 → 每部分 ≥ 50 tokens

---

## Task 6.3: 降级策略实现

**文件:** `novel_runtime/compiler/context_assembler.py` (扩展)

**依赖:** Task 6.2

### Contract: ContextAssembler 新增方法

#### `apply_degradation_strategy(sections: dict[str, str], token_stats: dict[str, int], budget: int) → dict[str, str]`

**Behavior:**
- 对每个超预算的部分，按降级策略精简:
  - `recent_chapters`: 3章 → 2章完整+1章精简 → 1章完整+2章极简
  - `character_state`: 完整状态 → 核心状态 → 目标+位置
  - `hooks`: 完整伏笔 → 只保留 must_not_forget → 只保留 should_resolve
  - `subplots`: 完整子线 → 只保留活跃子线 → 只保留推进建议

**Guarantees:**
- 每次降级后重新计算 token 数
- 降级是渐进式的（逐级降低，不是一步到最低）

**验收标准:**
- [ ] 降级策略按级别正确执行
- [ ] 降级后 token 数在预算内

---

## Task 6.4: Context Assembler 组装

**文件:** `novel_runtime/compiler/context_assembler.py` (主方法)

**依赖:** Task 6.1, 6.2, 6.3

### Contract: ContextAssembler.assemble (完整流程)

**完整流程:**
1. 读取所有素材 (Task 6.1)
2. 计算各部分 token 数 (Task 6.2)
3. 如果总 token 数超预算:
   a. 按优先级截断 (Task 6.2)
   b. 如果仍然超预算，应用降级策略 (Task 6.3)
4. 将所有部分组装为 Markdown 格式的 raw_context

**raw_context.md 格式:**
```markdown
# Raw Context for Chapter {chapter_id}

## Style Asset
{style_and_voices_content}

## Character Voices
{character_voices_content}

## Global Story Context
{story_context_content}

## Recent Chapters
{recent_chapters_content}

## Current State
{current_state_content}

## Character State
{character_state_content}

## Hooks
{hooks_content}

## Subplots
{subplots_content}

## Chapter Goal
{chapter_goal_content}

## Writing Strategy
{writing_strategy_content}

## Health Report
{health_report_content}

---
Token Budget: {total_tokens}/{budget}
Budget Allocation: {budget_used}
```

**Guarantees:**
- raw_context.md 的总 token 数 ≤ budget
- 每部分至少保留 50 tokens
- 降级信息在末尾标注

**验收标准:**
- [ ] 组装的 raw_context 格式正确
- [ ] token 统计信息准确
- [ ] 超预算时截断/降级正确

---

## Task 6.5: Context Assembler 测试

**文件:** `tests/unit/test_context_assembler.py`, `tests/unit/test_token_budget.py`

**测试范围:**

### Unit Tests
- test_assemble_full_context: 完整项目 → 所有部分包含
- test_assemble_first_chapter: 第1章 → 最小上下文
- test_token_budget_within: 预算内 → 不截断
- test_token_budget_over: 超预算 → 低优先级截断
- test_degradation_recent_chapters: 3章→2章完整+1章精简
- test_degradation_character_state: 完整→核心→最小
- test_minimum_guarantee: 极端超预算 → 每部分 ≥ 50 tokens
- test_raw_context_format: 输出格式正确

### Integration Tests (Mock LLM)
- test_assemble_with_real_files: 创建完整项目目录 → assemble → 格式正确
- test_assemble_budget_scenarios: 不同预算下的截断行为

**验收标准:**
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 测试覆盖率 > 85%