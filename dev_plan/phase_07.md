# Phase 7: Context Compiler (Agent) + State Health Checker

## 前置条件
- Phase 6 完成（Context Assembler 可用）
- Phase 2 完成（LLM 调用层可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 7.1 | State Health Checker (确定性代码) | Phase 1, 5 | 1.5天 |
| 7.2 | Context Compiler Agent + Prompt | Phase 2, 6 | 2天 |
| 7.3 | Context Service 编排层 | 7.1, 7.2 | 1天 |
| 7.4 | Context API 端点 | 7.3 | 0.5天 |
| 7.5 | 集成测试 | 7.4 | 1天 |

依赖关系图:
```text
Phase 1+5 → 7.1
Phase 2+6 → 7.2
7.1 + 7.2 → 7.3 → 7.4 → 7.5
```

---

## Task 7.1: State Health Checker (确定性代码)

**文件:** `novel_runtime/compiler/state_health_checker.py`

**依赖:** Phase 1 (Storage), Phase 5 (数据结构)

### Contract: compiler.state_health_checker.StateHealthChecker

#### `check(project_path: Path, chapter_id: str, strategy: WritingStrategy) → StateHealthReport`

**Input:**
- 项目路径
- 当前章节 ID
- 写作策略

**Output:**
- `StateHealthReport` model

**Behavior (检查规则):**

1. **角色遗漏检查**
   - 遍历所有角色
   - 如果 `chapters_since_development > strategy.character_policy.character_development_frequency`
   - 生成 issue: `type="character_idle"`, severity="warning"

2. **伏笔过期检查**
   - 遍历所有 open 和 triggered 的 hook
   - 如果当前章节 > `source_chapter_number + reader_patience`
   - 生成 issue: `type="hook_overdue"`, severity="critical"

3. **伏笔过载检查**
   - 统计 open 状态的 hook 数量
   - 如果 > `strategy.hook_policy.max_open_hooks`
   - 生成 issue: `type="hook_overload"`, severity="warning"

4. **子线遗忘检查**
   - 遍历所有活跃子线
   - 如果 `chapters_since_advance > strategy.subplot_policy.max_gap_between_advances`
   - 生成 issue: `type="subplot_neglect"`, severity="warning"

5. **子线过载检查**
   - 统计活跃子线数
   - 如果 > `strategy.subplot_policy.max_simultaneous`
   - 生成 issue: `type="subplot_overload"`, severity="warning"

6. **主角缺席检查**
   - 检查最近 N 章（N = `strategy.character_policy.max_scenes_without_protagonist`）的摘要
   - 如果主角未出现
   - 生成 issue: `type="protagonist_absent"`, severity="warning"

7. **节奏重复检查**
   - 获取最近 3 章的 rhythm_type
   - 如果连续 3 章相同节奏类型
   - 生成 issue: `type="rhythm_repetition"`, severity="warning"

8. **新角色过密检查**
   - 检查最近 N 章（N = `strategy.character_policy.new_character_introduction_rate`）引入的新角色
   - 如果数量 > 1
   - 生成 issue: `type="new_character_density"`, severity="info"

**Guarantees:**
- 每个检查规则独立执行
- 所有检查完成后按 severity 排序: critical > warning > info
- 报告 ID 自动生成

**Error cases:**
- 项目数据不完整 → 跳过缺失部分的检查，在报告中标注

**验收标准:**
- [ ] 8 条检查规则全部实现
- [ ] 报告按 severity 排序
- [ ] 不完整数据不崩溃

**测试用例:**
- test_character_idle: 角色超过N章没发展 → 警告
- test_hook_overdue: 伏笔超过patience → critical
- test_hook_overload: 伏笔超过上限 → 警告
- test_subplot_neglect: 子线超过max_gap → 警告
- test_rhythm_repetition: 连续3章同节奏 → 警告
- test_no_issues: 健康项目 → 空报告
- test_incomplete_data: 缺少角色数据 → 不崩溃

---

## Task 7.2: Context Compiler Agent + Prompt

**文件:**
- `novel_runtime/agents/context_compiler.py`
- `prompts/context_compile.md`

**依赖:** Phase 2, 6

### Agent: ContextCompilerAgent

**继承:** BaseAgent

#### `compile(raw_context: str, health_report: StateHealthReport) → str`

**Contract:**

**Input:**
- `raw_context`: Context Assembler 产出的原始素材 Markdown
- `health_report`: State Health Checker 产出的健康报告

**Output:**
- `context_pack.md` 的完整 Markdown 内容（包含叙事诊断章节）

**Behavior:**
1. 加载 Prompt 模板 `context_compile`
2. 渲染变量: `{raw_context}`, `{health_report}`
3. 调用 LLM
4. 校验输出包含所有必需章节
5. 返回 context_pack.md 内容

**Validator:** MarkdownValidator，必需章节:
- `Project Info`
- `Style Asset`
- `Character Voices`
- `Global Story Context`
- `Narrative Diagnosis` ← 核心
- `Subplot Status`
- `Recent Chapters`
- `Current State`
- `Character State`
- `Hooks`
- `Chapter Goal`
- `Generation Constraints`
- `Writing Strategy`

### Prompt Design: context_compile.md

**Input Specification:**
- `{{raw_context}}`: Context Assembler 产出的原始素材
- `{{health_report}}`: State Health Checker 的 YAML 报告

**Output Specification:**
- Markdown 格式，包含上述必需章节
- Narrative Diagnosis 章节必须包含:
  - 当前故事弧线阶段 (setup/rising/climax/falling/resolution)
  - 读者耐心评估 (high/medium/low + 理由)
  - 建议本章节奏类型
  - 建议本章推进的子线
  - 建议本章回收的伏笔

**Key Instructions:**
1. 分析当前故事弧线阶段，必须给出明确判断
2. 评估读者耐心状态，参考 health_report 中的紧迫度和节奏问题
3. 建议本章节奏类型必须与前一章节形成对比（避免连续同节奏）
4. 子线推进建议必须考虑 writing_strategy 中的策略参数
5. 伏笔回收建议必须优先考虑 overdue 和 critical 的伏笔
6. Generation Constraints 必须从 style_asset 和 writing_strategy 中提取
7. 不要添加新的剧情设定，只做分析和建议

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 缺少叙事诊断章节 | 校验失败 | 提示"必须包含 Narrative Diagnosis 章节" |
| 弧线阶段判断模糊 | 如"正在发展" | 提示"弧线阶段必须从 setup/rising/climax/falling/resolution 中选择一个" |
| 建议与前章节奏重复 | 如前章递进建议也递进 | 提示"建议的节奏类型必须与前一章节的节奏类型不同" |

**Test Inputs:**
- Case 1: 第1章（无前文） → Narrative Diagnosis 建议初始节奏
- Case 2: 连续3章递进 → 建议过渡蓄力节奏
- Case 3: 伏笔过期 → 建议回收

**验收标准:**
- [ ] Agent 生成包含所有必需章节的 context_pack
- [ ] Narrative Diagnosis 章节有明确的弧线阶段判断
- [ ] 节奏建议与 health_report 关联
- [ ] 格式校验通过

---

## Task 7.3: Context Service 编排层

**文件:** `novel_runtime/services/context_service.py`

**依赖:** Task 7.1, 7.2

### Contract: services.context_service.ContextService

#### `compile_context(project_id: str, chapter_number: int, chapter_goal: str) → CompileContextResult`

**Contract:**

**Input:**
- 项目 ID
- 章节号
- 本章目标（用户输入）

**Output:**
- `CompileContextResult`: `context_pack_path: str`, `health_report_path: str`, `health_issues: int`

**Behavior:**
1. 获取项目信息（含 style_id）
2. 调用 ContextAssembler.assemble() → raw_context + budget_used
3. 调用 StateHealthChecker.check() → health_report
4. 调用 ContextCompilerAgent.compile(raw_context, health_report) → context_pack
5. 保存 context_pack 到 `chapters/chapter_NNN/context_pack.md`
6. 保存 health_report 到 `chapters/chapter_NNN/state_health_report.yaml`
7. 返回结果

**Error cases:**
- 文风未设置 → `StyleNotSetError`
- 章节不存在 → `ChapterNotFoundError`

**Guarantees:**
- context_pack 的 token 数在预算内
- health_report 包含所有适用检查的结果

**验收标准:**
- [ ] 完整流程可跑通
- [ ] 文件保存正确
- [ ] health_issues 数量正确

---

## Task 7.4: Context API 端点

**文件:** `novel_runtime/api/context.py`

### API 端点

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/context/compile`
- Request body: `{"chapter_goal": "...", "style_id": "style_001"}`
- Response: `{"context_pack_path": "...", "health_report_path": "...", "health_issues": 2}`
- 可同步或异步执行

**验收标准:**
- [ ] API 端点可调用
- [ ] 返回正确路径
- [ ] health_issues 数量正确

---

## Task 7.5: 集成测试

**文件:** `tests/integration/test_context_service.py`

**测试范围:**
- test_health_checker_character_idle: 角色遗漏 → 警告
- test_health_checker_hook_overdue: 伏笔过期 → critical
- test_health_checker_all_rules: 所有8条规则 → 正确检测
- test_context_compiler_first_chapter: 第1章 → 包含初始建议
- test_context_compiler_with_health_issues: 有健康问题 → Narrative Diagnosis 建议解决
- test_context_service_full_flow: 完整流程 → context_pack + health_report
- test_context_api: HTTP 测试

**验收标准:**
- [ ] 所有集成测试通过
- [ ] Health Checker 覆盖所有8条规则
- [ ] Context Compiler 生成合法 context_pack