# Novel Writing Runtime - 开发计划 v0.1

基于 Thought_content.md 规范，经过质量导向审核后的最终版。

---

# 一、核心架构

## 1.1 系统分层

```
资产层:
  Style Asset (含 Character Voice Asset)
  Novel Bible (含版本演进)
  Character State (含叙事功能维度)
  World Setting
  Subplot Registry
  Hook Registry (含紧迫度/类型/回收策略)
  Chapter History (含节奏标记)
  Timeline (含叙事时间双轨)
  Writing Strategy Config

编译层:
  Context Assembler (确定性代码: 读文件、筛选、拼装)
  Context Compiler (Agent: 叙事推理、诊断、建议)
  State Health Checker (反馈 state 质量)

生成层:
  Chapter Planner (含节奏规划 + 子线分配)
  Chapter Writer (剧情逻辑优先，附带状态标注)
  Narrative Polisher (表达效果优先: 张力、节奏、文风)

审查层:
  Continuity Auditor (事实一致性)
  Quality Auditor (可读性 + 网文节奏)
  Cross-Chapter Auditor (跨章诊断: 节奏、子线、伏笔)
  Reader Simulator (读者视角模拟)

更新层:
  State Updater (基于状态标注确认 + diff 感知)
  Bible Updater (检测 Bible 是否需要演进)
  Snapshot Manager (含回滚)
```

## 1.2 Agent 清单

| # | Agent | 层 | 类型 | 职责 |
|---|-------|----|------|------|
| 1 | Context Assembler | 编译层 | Python 代码 | 读文件、筛选、拼装原始素材 |
| 2 | Context Compiler | 编译层 | Agent | 对原始素材进行叙事推理，生成 Context Pack |
| 3 | State Health Checker | 编译层 | Python 代码 | 检测 state 异常（角色遗漏、伏笔过期等） |
| 4 | Style Analyst | 生成层 | Agent | 分析样本文本、抽取文风参数 |
| 5 | Story Architect | 生成层 | Agent | 生成 Novel Bible 全套文档 |
| 6 | Chapter Planner | 生成层 | Agent | 章节规划（含节奏规划 + 子线分配） |
| 7 | Chapter Writer | 生成层 | Agent | 生成正文草稿（附带状态标注） |
| 8 | Narrative Polisher | 生成层 | Agent | 文风重写 + 表达强化 |
| 9 | Continuity Auditor | 审查层 | Agent | 事实一致性审查 |
| 10 | Quality Auditor | 审查层 | Agent | 可读性 + 网文节奏审查 |
| 11 | Cross-Chapter Auditor | 审查层 | Agent | 跨章诊断（节奏、子线、伏笔） |
| 12 | Reader Simulator | 审查层 | Agent | 读者视角模拟 |
| 13 | State Updater | 更新层 | Agent | 基于标注确认状态变化 + 生成下一章建议 |

## 1.3 核心工作流

```text
编译上下文:
  Context Assembler(代码) → 原始素材
  Context Compiler(Agent) → Context Pack + 叙事诊断

规划本章:
  Chapter Planner → Chapter Plan (含节奏规划 + 子线分配 + Agent Contract)

生成正文:
  Chapter Writer → Draft + 状态标注
  Narrative Polisher → Styled Draft

审查修改:
  Continuity Auditor → 连续性审查报告
  Quality Auditor → 质量审查报告
  Cross-Chapter Auditor → 跨章诊断报告
  Reader Simulator → 读者体验模拟报告

  [如有问题] → 结构化修复指令 → Narrative Polisher 重写 (最多1次)

确认章节:
  用户确认 → final.md 生成

更新状态:
  State Updater: 基于 final.md + 状态标注 + 用户diff → 更新所有 state 文件
  Bible Updater: 检测是否需要 Bible 演进 → 生成 bible_update_proposal
  Snapshot Manager: 保存 snapshot + 可回滚
```

---

# 二、数据结构

## 2.1 Project

```yaml
project_id: string
project_name: string
genre: string
status: draft | active | paused | archived
default_style_id: string
current_volume_id: string
current_chapter_id: string
bible_version: int
writing_strategy_id: string          # 新增: 关联写作策略配置
created_at: datetime
updated_at: datetime
```

## 2.2 StyleAsset

```yaml
style_id: string
style_name: string
source_text_ids: list

# 叙述维度
narration: string
sentence_rhythm: string
dialogue_style: string
description_density: string

# 情绪与冲突
emotion_curve: string
conflict_pattern: string

# 章节结构
chapter_opening: string
chapter_ending: string

# 场景节奏
scene_density: string               # 每 N 字出现一次动作或冲突变化

# 禁用表达
avoid: list

# 条件文风规则 (新增: 文风随剧情变化)
conditional_rules:
  - condition: "fight_scene"
    adjustments:
      sentence_rhythm: "极短句，断点式推进"
      description_density: "动作描写为主，环境描写最小化"
  - condition: "emotional_scene"
    adjustments:
      sentence_rhythm: "中长句，铺垫后短句爆发"
      dialogue_style: "对白克制，留白多"

created_at: datetime
updated_at: datetime
```

## 2.3 Character Voice Asset (新增)

```yaml
voice_id: string
character_id: string
character_name: string

speech_patterns:
  typical_phrases: list              # 口头禅/常用表达
  sentence_length: string            # 短句/中句/长句
  vocabulary_level: string           # 用词水平: 粗犷/文雅/专业/市井
  humor_style: string                # 幽默方式: 讽刺/自嘲/冷幽默/无
  emotional_expression: string       # 情绪表达: 外露/克制/反差/压抑

internal_monologue:
  style: string                      # 内心独白风格
  frequency: string                  # 内心独白频率: 高/中/低
  depth: string                      # 独白深度: 表面感受/深层思考/哲理化

quirks:
  - context: string                  # 什么情境下
    behavior: string                  # 特殊行为或说话方式
```

## 2.4 Character State (增强)

```yaml
character_id: string
name: string
role: protagonist | antagonist | supporting | minor

# 事实状态
current_location: string
current_goal: string
current_emotion: string
known_information: list
unknown_information: list
abilities: list
secrets: list
relationships: list
last_seen_chapter: string

# 叙事功能维度 (新增)
narrative_role:
  current_function: string           # 当前叙事功能
  functions: list                    # 角色在故事中的功能列表
  arc_stage: string                  # 角色弧线阶段
  arc_stages_available: list         # 可用的弧线阶段
  last_significant_moment: string    # 上一次重大变化章节
  chapters_since_development: int    # 几章没有角色发展了
  reader_attachment_level: string   # 读者关注度: growing/stable/declining
  next_use_suggestion: string       # 建议下次如何使用此角色

# 角色声音 (新增)
voice_id: string                     # 关联 Character Voice Asset
```

## 2.5 Hook (增强)

```yaml
hook_id: string
content: string
source_chapter: string
status: open | triggered | resolved | abandoned
priority: low | medium | high

# 类型维度 (新增)
type: mystery | tension | promise | emotional | power

# 读者耐心 (新增)
reader_patience: int                  # 读者可容忍的章节数
urgency: stable | rising | critical    # 紧迫度趋势
urgency_increase_rate: 0.5            # 每章紧迫度自动递增量

# 回收策略 (新增)
payoff_type: escalation | reversal | revelation | convergence
planned_payoff_range: string
actual_payoff_chapter: string

# 关联 (新增)
related_subplots: list
related_characters: list
foreshadow_density: string           # low/medium/high: 本章是否需要再暗示

# 元数据
notes: string
```

## 2.6 Subplot (新增)

```yaml
subplot_id: string
name: string
type: main_plot | character_arc | ongoing_conflict | mystery | romance
status: setup | escalating | climax | resolving | resolved

arc:
  setup_chapter: string
  current_stage: string
  planned_climax_range: string
  resolution_chapter: string

involved_characters: list
related_hooks: list
last_advanced: string
chapters_since_advance: int

interleave_plan:
  min_gap_between_advances: int       # 推进此子线至少间隔几章
  max_gap_between_advances: int       # 超过几章不推进就告警
  next_suggested_chapter: string      # 建议下次推进的章节

convergence_points:
  - with: string                      # 另一条子线 ID
    planned_chapter_range: string
    type: causal | thematic | character  # 汇合方式
```

## 2.7 Chapter (增强)

```yaml
chapter_id: string
chapter_number: int
title: string
status: planned | drafted | reviewed | approved | locked

# 文件路径
plan_path: string
draft_path: string
styled_draft_path: string
final_path: string
review_continuity_path: string
review_quality_path: string
review_cross_chapter_path: string      # 新增
review_reader_sim_path: string         # 新增
context_pack_path: string

# 节奏标记 (新增)
rhythm_type: escalation | explosion | pressure | resonance | transition_charge
tension_level: int                     # 1-10
satisfaction_level: int                 # 1-10
reader_hook_strength: int              # 1-10

# 子线推进记录 (新增)
subplots_advanced:
  - subplot_id: string
    advancement_type: string

subplots_idle:
  - subplot_id: string
    chapters_idle: int
    needs_attention: bool

# 摘要
summary: string

created_at: datetime
updated_at: datetime
```

## 2.8 Timeline Event (增强)

```yaml
event_id: string
chapter_id: string

# 叙事时间 vs 阅读时间 (新增)
story_time:
  start: string
  end: string
  duration: string

reading_duration: string              # 占了多少章篇幅
pacing_ratio: fast | normal | slow    # 叙事节奏比

location: string
characters: list
event_summary: string
state_change: string
```

## 2.9 Writing Strategy Config (新增)

```yaml
strategy_id: string
name: string
description: string

chapter_length:
  target: 3000
  min: 2500
  max: 3500

pacing_strategy:
  type: variable_rhythm               # variable_rhythm / steady
  tension_curve: sawtooth             # sawtooth / wave / escalating
  cooldown_after_climax: 1            # 大高潮后几章回落

subplot_policy:
  max_simultaneous: 3                  # 同时推进的子线上限
  min_advance_frequency: 4             # 子线最长几章不推进就告警
  convergence_strategy: planned        # planned / organic

hook_policy:
  max_open_hooks: 8                    # 同时开放的伏笔上限
  min_resolution_rate: 0.3             # 每10章至少回收30%的伏笔
  urgency_escalation: true             # 伏笔紧迫度是否自动递增

character_policy:
  max_scenes_without_protagonist: 1    # 最多几章没有主角
  character_development_frequency: 3    # 角色几章必须有发展
  new_character_introduction_rate: 5   # 每几章引入一个新角色
```

## 2.10 Chapter Plan (增强)

```markdown
# Chapter Plan

## Agent Contract
from: "chapter_planner"
to: "chapter_writer"
promises:
  - "3个场景全部覆盖"
  - "scene_2 包含主角与赵坤的正面冲突"
  - "结尾包含神秘势力的暗示"
constraints:
  - "不得跳过scene_2"
  - "scene_3必须以反转结尾"
  - "总字数2800-3200"

## Chapter Goal
本章目标:

## Reader Promise
本章给读者的期待:

## Rhythm Plan (新增)
本章节奏类型: 递进型 / 爆发型 / 压迫型 / 回响型 / 过渡蓄力型
本章在卷中的节奏角色: 铺垫 / 升级 / 高潮 / 回落 / 转折
与前一章的节奏关系: 延续加速 / 反差调节 / 并行推进
爽点投放时机: 场景2中期 / 场景3结尾
压力累积时机: 场景1全段 / 场景2前半

## Subplot Allocation (新增)
本章推进的子线:
  - subplot_id: "subplot_faction_war"
    advancement_type: "escalation"
    planned_content: "赵坤公开质疑主角"

本章暂缓的子线:
  - subplot_id: "subplot_romance"
    reason: "上一章刚推进，本章给读者消化空间"

## Conflict
主要冲突:

## Scene List

### Scene 1
地点:
出场人物:
场景功能:
冲突:
转折:
输出结果:
预期字数:

### Scene 2
地点:
出场人物:
场景功能:
冲突:
转折:
输出结果:
预期字数:

## Ending Hook
结尾钩子:
```

## 2.11 State Annotations (新增: Chapter Writer 并行产出)

```yaml
# 与章节正文并行产出的状态标注
chapter_id: "chapter_023"

annotations:
  - location: "scene_2_paragraph_5"
    type: "character_state_change"
    character: "林雪"
    change: "从信任转为怀疑"
    trigger: "发现主角隐瞒鉴定方法"
    narrative_impact: "增加后续冲突可能性"

  - location: "scene_3_paragraph_12"
    type: "new_hook"
    hook_id: "H012"
    content: "神秘人要求调查主角来历"
    hook_type: "mystery"
    reader_patience: 8

  - location: "scene_1_paragraph_3"
    type: "subplot_advance"
    subplot_id: "subplot_faction_war"
    advancement: "赵坤公开质疑主角"
    next_stage: "open_conflict"

  - location: "scene_3_end"
    type: "character_development"
    character: "主角"
    development: "首次公开展示鉴定能力"
    arc_progression: "从隐藏到部分暴露"

summary_annotations:
  - type: "resolved_hook"
    hook_id: "H007"
    resolution: "古物真实价值被揭示"
  - type: "new_world_info"
    info: "云海拍卖会背后存在隐藏势力"
  - type: "relationship_change"
    from: "主角"
    to: "林雪"
    change: "建立初步信任"
```

## 2.12 Fix Instructions (新增: Reviewer 输出的结构化修复指令)

```yaml
fix_instructions:
  - fix_id: "FIX_001"
    type: "continuity_violation"
    severity: "critical"
    location: "scene_2_paragraph_3"
    problem: "林雪在第20章已经知道主角身份，这里不应该表现惊讶"
    action: "replace"                     # replace / insert / delete / rewrite
    original_text: "林雪瞪大了眼睛，满脸不可思议：'你……你居然是……'"
    suggested_fix: "林雪目光微沉，压低声音：'你还要瞒到什么时候？'"
    constraint: "保持后续对话逻辑不变"

  - fix_id: "FIX_002"
    type: "pacing_issue"
    severity: "moderate"
    location: "scene_1"
    problem: "场景1纯对话长达800字，缺少冲突推进"
    action: "rewrite"
    original_text: "(场景1全文)"
    suggested_fix: "压缩对话至400字，增加一次动作冲突"
    constraint: "保留关键信息，加入肢体冲突描述"
```

## 2.13 Context Pack (增强)

```markdown
# Chapter Context Pack

## Project Info
项目名称:
小说类型:
当前卷:
当前章节:

## Style Asset
当前文风:
叙述视角:
句子节奏:
对白风格:
场景文风调整规则: (条件文风规则，按场景类型匹配)

## Character Voices (新增)
本章出场角色的声音特征:
  - 角色名: 林雪
    说话风格: ...
    口头禅: ...

## Global Story Context
小说核心卖点:
主线目标:
当前卷目标:

## Narrative Diagnosis (新增: 由 Context Compiler Agent 生成)
当前故事弧线阶段:
读者耐心评估:
建议本章节奏类型:
建议本章推进的子线:
建议本章回收的伏笔:

## Subplot Status (新增)
活跃子线列表:
每条子线上次推进章节:
每条子线推进建议:

## Recent Chapters
最近3章摘要:
最近3章节奏类型:
最近3章张力曲线:

## Current State
当前地点:
当前时间:
当前冲突:
当前主角状态:

## Character State
本章相关人物:
每个人物当前目标:
每个人物已知信息:
每个人物未知信息:
每个人物叙事功能:
人物关系变化:
角色声音提示:

## Hooks
本章可触发伏笔:
本章禁止遗忘伏笔:
即将回收伏笔:
过期未回收伏笔告警:

## Chapter Goal
本章必须完成:
本章可以推进:
本章禁止破坏:

## Generation Constraints
字数范围:
节奏要求:
爽点要求:
结尾钩子要求:
角色声音约束:
子线推进约束:

## Writing Strategy
节奏策略:
子线策略:
伏笔策略:
角色策略:
```

## 2.14 State Health Report (新增)

```yaml
report_id: "shr_023"
chapter_id: "chapter_023"
generated_at: datetime

issues:
  - type: "character_idle"
    character_id: "character_lin_xue"
    description: "林雪已5章没有实质性发展"
    severity: "warning"
    suggestion: "在接下来的2章内给予角色发展机会"

  - type: "hook_overdue"
    hook_id: "H005"
    description: "伏笔H005已超出计划回收范围3章"
    severity: "critical"
    suggestion: "在最近2章内回收或推进此伏笔"

  - type: "rhythm_repetition"
    description: "连续3章为递进型节奏"
    severity: "warning"
    suggestion: "下一章建议使用反差节奏"

  - type: "subplot_neglect"
    subplot_id: "subplot_romance"
    description: "感情线已6章未推进"
    severity: "warning"
    suggestion: "下一章需要推进此子线"
```

---

# 三、文件目录结构

```text
novel_project/
  project.yaml

  style_assets/
    style_001.yaml
    style_002.yaml
    character_voices/                    # 新增
      voice_protagonist.yaml
      voice_lin_xue.yaml

  source_texts/
    sample_001.txt
    sample_002.txt

  bible/
    novel_bible.md
    world_setting.md
    character_profiles.md
    volume_plan.md
    chapter_plan.md
    bible_changelog.yaml                 # 新增: Bible 版本演进记录

  strategies/                            # 新增
    writing_strategy.yaml

  chapters/
    chapter_001/
      context_pack.md
      chapter_plan.md
      draft.md
      styled_draft.md
      state_annotations.yaml             # 新增
      final.md
      review_continuity.md
      review_quality.md
      review_cross_chapter.md            # 新增
      review_reader_sim.md              # 新增
      fix_instructions.yaml              # 新增

  subplots/                              # 新增
    subplot_registry.yaml
    subplot_faction_war.yaml
    subplot_romance.yaml

  states/
    story_state.yaml                     # 合并: global_state + timeline
    characters.yaml                      # 合并: character_state + relationship
    hooks.yaml

  snapshots/
    state_after_chapter_001.yaml
    state_after_chapter_002.yaml

  prompts/
    style_analysis.md
    novel_bible_generation.md
    context_compile.md
    chapter_plan.md
    chapter_write.md
    narrative_polish.md                  # 替代 style_rewrite
    continuity_review.md
    quality_review.md
    cross_chapter_review.md              # 新增
    reader_simulation.md                 # 新增
    state_update.md
    bible_update.md                      # 新增
```

---

# 四、Agent 详细设计

## 4.1 Context Assembler（确定性代码）

类型: Python 代码（非 Agent）

输入:
```text
project_id
chapter_id
chapter_goal
style_id
```

处理逻辑:
```python
def assemble_context(project_id, chapter_id, chapter_goal, style_id):
    # 1. 读取 project.yaml
    # 2. 读取 story_state.yaml (全局状态 + 时间线)
    # 3. 读取 characters.yaml (筛选本章相关角色)
    # 4. 读取 hooks.yaml (筛选本章相关伏笔)
    # 5. 读取 subplot_registry.yaml (筛选活跃子线)
    # 6. 读取最近3章摘要
    # 7. 读取 style_asset.yaml
    # 8. 读取相关 character_voice.yaml
    # 9. 读取 writing_strategy.yaml
    # 10. 读取最近3章 review_cross_chapter.md (如有)
    # 11. 运行 State Health Checker
    # 12. Token 预算分配与截断
    # 13. 拼装 raw_context.md
```

Token 预算分配:
```yaml
context_budget:
  total: 8000                            # 留给上下文的 token 预算
  allocation:
    style_and_voices: 800
    story_context: 600
    recent_chapters: 1500                  # 最近3章摘要
    current_state: 600
    character_state: 1200
    hooks: 400
    subplots: 400
    chapter_goal: 300
    narrative_diagnosis: 500
    generation_constraints: 400
    writing_strategy: 300
    health_report: 400

  priority_order:                         # 超预算时按优先级截断
    - style_and_voices                     # 最高优先级
    - chapter_goal
    - current_state
    - character_state
    - recent_chapters
    - hooks
    - subplots
    - story_context
    - narrative_diagnosis
    - writing_strategy
    - health_report
    - generation_constraints               # 最低优先级

  summarization_strategy:                  # 超预算时的降级策略
    recent_chapters:
      3_chapters: "完整摘要"
      2_chapters: "最近2章完整 + 更早1章极简"
      1_chapters: "最近1章完整 + 2章极简"
    character_state:
      full: "出场角色完整状态"
      reduced: "只保留出场角色的核心状态"
      minimal: "只保留出场角色的目标+位置"
```

输出:
```text
raw_context.md
state_health_report.yaml
```

---

## 4.2 Context Compiler（Agent）

类型: LLM Agent

输入:
```text
raw_context.md
state_health_report.yaml
```

输出:
```text
context_pack.md (含叙事诊断章节)
```

职责:
```text
分析当前故事弧线阶段
评估读者耐心状态
建议本章节奏类型
建议本章推进的子线
建议本章回收的伏笔
诊断跨章节奏问题
基于 writing_strategy 校准生成约束
```

---

## 4.3 State Health Checker（确定性代码）

类型: Python 代码（非 Agent）

检查规则:
```text
角色遗漏: 任何角色超过 N 章没有发展 (writing_strategy.character_policy.character_development_frequency)
伏笔过期: 任何伏笔超过 planned_payoff_range 未回收
伏笔过载: 当前 open 状态伏笔超过 max_open_hooks
子线遗忘: 任何活跃子线超过 max_gap_between_advances 未推进
子线过载: 同时推进的子线超过 max_simultaneous
主角缺席: 连续超过 max_scenes_without_protagonist 章没有主角
节奏重复: 连续 N 章同节奏类型
新角色过密: 每 N 章引入超过 1 个新角色
```

输出: `state_health_report.yaml`

---

## 4.4 Style Analyst（Agent）

与原 spec 相同，增加:
```text
对抗测试: 生成一个故意偏离文风的段落，验证文风资产能否识别偏离
如果识别失败，调整文风资产直到能准确识别
```

---

## 4.5 Story Architect（Agent）

增强：渐进式生成

Round 1:
```text
输入: 用户核心创意
输出: 3个方向变体 (不同卖点/节奏/风格组合)
用户选择或混搭
```

Round 2:
```text
输入: 选定方向
输出: 详细角色概念 + Character Voice Asset 初稿
用户调整角色设定
```

Round 3:
```text
输入: 确定的方向和角色
输出: 完整 Novel Bible + 前10章规划 + Subplot Registry 初版
```

---

## 4.6 Chapter Planner（Agent）

增强: 节奏规划 + 子线分配 + Agent Contract

输入:
```text
context_pack.md
```

输出:
```text
chapter_plan.md (含 Rhythm Plan + Subplot Allocation + Agent Contract)
```

---

## 4.7 Chapter Writer（Agent）

增强: 附带状态标注

输入:
```text
context_pack.md
chapter_plan.md
style_asset.yaml
character_voices.yaml (本章相关角色)
```

输出:
```text
draft.md
state_annotations.yaml (并行产出)
```

生成规则（在原 spec 基础上增加）:
```text
严格按照场景列表生成
严格遵循 Agent Contract 的 promises 和 constraints
每个场景标注产出的状态变化
生成正文的同时生成结构化的状态标注
保持每个角色的声音一致性
根据条件文风规则调整不同场景的写法
每个场景都要产生状态变化
结尾必须保留下一章驱动力
```

---

## 4.8 Narrative Polisher（Agent）

替代原 Style Rewriter，职责扩展:

输入:
```text
draft.md
state_annotations.yaml
style_asset.yaml
chapter_plan.md (含节奏要求)
character_voices.yaml
```

输出:
```text
styled_draft.md
```

Polisher 动作 (在原文风重写基础上增加):
```text
强化场景张力
优化情绪曲线缓急
增强对白冲突感
调整节奏快慢交替
确保角色声音区分度
删除不符合文风的表达
保持剧情事实不变 (硬约束)
```

硬约束 (同原 spec):
```text
不得改变剧情事实
不得新增重大设定
不得改变人物动机
不得改变伏笔状态
```

---

## 4.9 Continuity Auditor（Agent）

与原 spec 相同。

---

## 4.10 Quality Auditor（Agent）

与原 spec 相同，增加量化评分:

```yaml
score:
  opening: 7              # 1-10
  conflict: 8
  pacing: 6
  satisfaction: 7
  style: 8
  ending_hook: 9

  # 新增: 与前章比较
  compared_to_previous:
    tension_change: "上升"
    pacing_change: "加快"
    style_consistency: "一致"

main_problems: [...]
rewrite_suggestions: [...]
```

---

## 4.11 Cross-Chapter Auditor（新增 Agent）

输入:
```text
styled_draft.md
最近3-5章的 chapter_plan.md
最近3-5章的 review 报告
story_state.yaml
hooks.yaml
subplot_registry.yaml
writing_strategy.yaml
```

输出:
```text
review_cross_chapter.md
```

审查维度:
```text
节奏连续性: 最近N章的节奏变化是否合理
子线推进: 各子线是否按策略推进
伏笔管理: 开放伏笔数量是否过载/过少
角色发展: 主要角色是否有持续发展
读者体验预测: 读者是否会产生疲劳/困惑/无聊
策略合规性: 是否违反 writing_strategy 中的各项策略
```

报告格式:
```markdown
# Cross-Chapter Review Report

## Rhythm Analysis
最近5章节奏类型: [铺, 升, 升, 升, 爆]
诊断: 连续3章升级型节奏，建议下一章过渡蓄力。
风险: 读者疲劳。

## Subplot Status
活跃子线: 3/3 (上限)
感情线: 4章未推进 (告警)
势力线: 本章推进 (正常)

## Hook Status
开放伏笔: 6/8
过期未回收: H003, H005
建议: 本章应回收H003或至少推进

## Character Development
主角: 连续2章有发展 (正常)
林雪: 5章无发展 (告警)

## Strategy Compliance
字数范围: 符合
节奏策略: 违反 (连续3章同类型)
伏笔策略: 接近上限 (6/8开放)
```

---

## 4.12 Reader Simulator（新增 Agent）

输入:
```text
styled_draft.md
style_asset.yaml
最近1章摘要
目标读者画像
writing_strategy.yaml
```

输出:
```text
review_reader_sim.md
```

模拟维度:
```text
兴奋点预测: 哪里读者会兴奋
无聊点预测: 哪里读者可能跳读
困惑点预测: 哪里读者可能不理解
弃书风险预测: 哪里读者可能弃书
下一章期待预测: 读者看完后最想看什么
对主角的共情程度: 上升/平稳/下降
爽感释放满意度: 是否充分
```

报告格式:
```markdown
# Reader Simulation Report

## Target Reader Profile
类型偏好: 快节奏打脸升级
耐心水平: 中等
爽感需求: 高

## Engagement Prediction
兴奋点:
  - scene_2中间: 主角展示鉴定能力 -> 预期兴奋度 8/10
  - scene_3结尾: 神秘势力出现 -> 预期兴奋度 7/10

无聊点:
  - scene_1前200字: 设定铺垫略长 -> 建议压缩到100字

困惑点: 无

弃书风险: 低 (3/10)

## Reader Expectation After This Chapter
最期待: 神秘势力后续
次期待: 赵坤的报复
担心: 主角身份暴露后果

## Emotional Arc Prediction
开头: 好奇(5) -> 中段: 兴奋(8) -> 结尾: 紧张期待(7)
弧线健康度: 良好
```

---

## 4.13 State Updater（Agent）

增强: 基于标注确认 + diff 感知

输入:
```text
final.md
state_annotations.yaml (Chapter Writer 产出的标注)
draft.md (用于 diff)
characters.yaml (当前角色状态)
story_state.yaml (当前全局状态)
hooks.yaml (当前伏笔)
subplot_registry.yaml (当前子线)
```

处理逻辑:
```text
1. 读取 final.md
2. 读取 state_annotations (Chapter Writer 的标注)
3. diff draft.md vs final.md (检测用户修改)
4. 优先采用用户修改的重大剧情变化
5. 用 state_annotations 的标注为锚点，确认状态变化
6. 对于标注之外的状态变化，用 LLM 推理补充
7. 更新所有 state 文件
8. 检测是否需要 Bible 更新
9. 生成 snapshot
```

输出:
```text
updated story_state.yaml
updated characters.yaml
updated hooks.yaml
updated subplot_registry.yaml
state_after_chapter_XXX.yaml (snapshot)
bible_update_proposal.md (如需要)
next_chapter_suggestions.yaml
```

---

# 五、关键流程

## 5.1 项目创建流程（渐进式）

```text
Round 1:
  用户输入核心创意 + 类型 + 目标读者
  Story Architect 生成3个方向变体
  用户选择或混搭

Round 2:
  基于选定方向生成详细角色概念
  同时生成 Character Voice Asset 初稿
  用户调整角色设定和声音

Round 3:
  基于确认的方向和角色
  生成完整 Novel Bible 全套文档
  生成 Writing Strategy Config 初版
  生成 Subplot Registry 初版
  生成前10章粗略规划
  用户确认

输出文件:
  bible/novel_bible.md
  bible/world_setting.md
  bible/character_profiles.md
  bible/volume_plan.md
  bible/chapter_plan.md
  bible/bible_changelog.yaml (version: 1)
  style_assets/style_001.yaml (如已有)
  style_assets/character_voices/
  strategies/writing_strategy.yaml
  subplots/subplot_registry.yaml
```

---

## 5.2 单章生成流程（含回写机制）

```text
Step 1: 编译上下文
  Context Assembler(代码) → raw_context.md + state_health_report.yaml
  Context Compiler(Agent) → context_pack.md (含叙事诊断)

Step 2: 规划本章
  Chapter Planner → chapter_plan.md (含节奏规划 + 子线分配 + Agent Contract)
  用户确认规划 (可选)

Step 3: 生成正文
  Chapter Writer → draft.md + state_annotations.yaml

Step 4: 文风润色
  Narrative Polisher → styled_draft.md

Step 5: 审查
  Continuity Auditor → review_continuity.md
  Quality Auditor → review_quality.md
  Cross-Chapter Auditor → review_cross_chapter.md
  Reader Simulator → review_reader_sim.md

Step 6: 修复 (如有问题)
  生成 fix_instructions.yaml (结构化修复指令)
  Narrative Polisher 重新润色 (最多1次)
  用户确认最终章节

Step 7: 确认章节
  用户确认 → 保存 final.md
  整章目录设为只读

Step 8: 更新状态
  State Updater: 基于 final.md + state_annotations 确认状态变化
  更新所有 state 文件
  生成 snapshot
  Bible Updater: 检测是否需要 Bible 演进
  生成 next_chapter_suggestions.yaml
```

---

## 5.3 状态更新流程（增强）

```text
用户确认章节
  ↓
读取 final.md + state_annotations.yaml
  ↓
diff final.md vs draft.md → 检测用户修改
  ↓
状态确认 (基于 state_annotations):
  - 章节摘要
  - 角色状态变化
  - 人物关系变化
  - 时间线更新
  - 地点变化
  - 新增设定
  - 伏笔更新 (新增/触发/回收)
  - 子线推进
  - 主角能力变化
  ↓
对于标注之外的变化，LLM 推理补充
  ↓
用户修改的剧情点优先级高于 AI 标注
  ↓
写入 state 文件
  ↓
生成 snapshot (可回滚)
  ↓
Bible Updater 检测:
  是否需要更新 world_setting?
  是否需要更新 character_profiles?
  是否需要新增角色?
  → 如需要，生成 bible_update_proposal.md
  → 用户确认后更新 Bible + 版本号+1
  ↓
生成下一章建议
  ↓
State Health Checker 检查:
  角色遗漏告警
  伏笔过载告警
  子线遗忘告警
  节奏重复告警
  → 写入 state_health_report.yaml
  ↓
完成
```

---

## 5.4 章节确认后冻结机制

```text
章节确认后:
  - chapter_XXX/ 整个目录设为只读
  - 生成 final.md
  - 如需查看历史上下文，查看 snapshot 而非原始文件
  - 如需修改已确认章节，必须:
    1. 创建修改提案
    2. 从对应 snapshot 回滚状态
    3. 重新确认
```

---

# 六、API Specification

## 6.1 Project API

### Create Project

`POST /api/projects`

Request:
```json
{
  "project_name": "都市修仙项目",
  "genre": "都市修仙",
  "idea": "一个被家族抛弃的年轻人意外获得古老传承，在现代都市中崛起。",
  "target_reader": "喜欢快节奏打脸升级的读者",
  "core_selling_point": "现代都市中的修仙逆袭"
}
```

Response:
```json
{
  "project_id": "novel_20260616_001",
  "status": "created",
  "next_step": "提供3个方向变体，请选择"
}
```

### Select Direction (Round 1)

`POST /api/projects/{project_id}/bible/direction`

Request:
```json
{
  "selected_direction": 1,
  "modifications": "希望主角性格更果断"
}
```

### Confirm Characters (Round 2)

`POST /api/projects/{project_id}/bible/characters`

Request:
```json
{
  "character_adjustments": { "...": "..." }
}
```

### Generate Bible (Round 3)

`POST /api/projects/{project_id}/bible/generate`

Response:
```json
{
  "bible_path": "bible/novel_bible.md",
  "chapter_plan_path": "bible/chapter_plan.md",
  "bible_version": 1
}
```

---

## 6.2 Style API

### Upload Style Sample

`POST /api/projects/{project_id}/style-samples`

(同原 spec)

### Analyze Style

`POST /api/projects/{project_id}/styles/analyze`

(同原 spec，增加对抗测试环节)

Response:
```json
{
  "style_id": "style_001",
  "style_asset_path": "style_assets/style_001.yaml",
  "adversarial_test_passed": true
}
```

---

## 6.3 Context API

### Compile Chapter Context

`POST /api/projects/{project_id}/chapters/{chapter_id}/context/compile`

Response:
```json
{
  "context_pack_path": "chapters/chapter_023/context_pack.md",
  "state_health_report_path": "chapters/chapter_023/state_health_report_note.md",
  "health_issues": 2
}
```

---

## 6.4 Chapter API

### Generate Chapter Plan

`POST /api/projects/{project_id}/chapters/{chapter_id}/plan`

(同原 spec，输出含节奏规划 + 子线分配 + Agent Contract)

### Generate Chapter Draft

`POST /api/projects/{project_id}/chapters/{chapter_id}/draft`

Response:
```json
{
  "draft_path": "chapters/chapter_023/draft.md",
  "state_annotations_path": "chapters/chapter_023/state_annotations.yaml"
}
```

### Style Rewrite → Narrative Polish

`POST /api/projects/{project_id}/chapters/{chapter_id}/polish`

Request:
```json
{
  "draft_path": "chapters/chapter_023/draft.md",
  "style_id": "style_001"
}
```

### Review Chapter

`POST /api/projects/{project_id}/chapters/{chapter_id}/review`

Request:
```json
{
  "chapter_text_path": "chapters/chapter_023/styled_draft.md",
  "review_types": ["continuity", "quality", "cross_chapter", "reader_sim"]
}
```

Response:
```json
{
  "continuity_review_path": "chapters/chapter_023/review_continuity.md",
  "quality_review_path": "chapters/chapter_023/review_quality.md",
  "cross_chapter_review_path": "chapters/chapter_023/review_cross_chapter.md",
  "reader_sim_review_path": "chapters/chapter_023/review_reader_sim.md",
  "fix_instructions_path": "chapters/chapter_023/fix_instructions.yaml"
}
```

### Fix and Repolish (最多1次)

`POST /api/projects/{project_id}/chapters/{chapter_id}/fix`

Request:
```json
{
  "fix_instructions_path": "chapters/chapter_023/fix_instructions.yaml"
}
```

### Approve Chapter

`POST /api/projects/{project_id}/chapters/{chapter_id}/approve`

Request:
```json
{
  "final_text": "用户确认后的最终章节正文"
}
```

Response:
```json
{
  "chapter_id": "chapter_023",
  "status": "approved",
  "frozen": true
}
```

### Update State After Chapter (自动触发)

`POST /api/projects/{project_id}/chapters/{chapter_id}/state/update`

(与 approve 联动，原子操作)

Response:
```json
{
  "snapshot_path": "snapshots/state_after_chapter_023.yaml",
  "updated_files": [
    "states/story_state.yaml",
    "states/characters.yaml",
    "states/hooks.yaml",
    "subplots/subplot_registry.yaml"
  ],
  "bible_update_proposal": "bible/bible_update_proposal.md",
  "health_issues": 1,
  "next_suggestions_path": "chapters/chapter_024/next_suggestions.yaml"
}
```

### Rollback State

`POST /api/projects/{project_id}/state/rollback`

Request:
```json
{
  "target_chapter": 22
}
```

---

## 6.5 Bible Update API

### Propose Bible Update

`GET /api/projects/{project_id}/bible/update-proposal`

### Confirm Bible Update

`POST /api/projects/{project_id}/bible/update`

Request:
```json
{
  "updates": [
    {
      "file": "world_setting.md",
      "section": "势力设定",
      "change": "新增隐藏势力'暗阁'"
    }
  ]
}
```

Response:
```json
{
  "bible_version": 3,
  "updated_files": ["bible/world_setting.md"]
}
```

---

## 6.6 Subplot API (新增)

### List Subplots

`GET /api/projects/{project_id}/subplots`

### Create Subplot

`POST /api/projects/{project_id}/subplots`

### Update Subplot

`PUT /api/projects/{project_id}/subplots/{subplot_id}`

### Suggest Chapter Subplot Allocation

`GET /api/projects/{project_id}/chapters/{chapter_id}/subplot-suggestions`

---

# 七、约束规则

## 7.1 章节生成约束

```text
生成正文前必须存在 Context Pack
生成正文前必须存在 Chapter Plan
生成正文前必须存在 State Health Report
正文生成必须绑定 Style Asset
正文生成不得跳过章节规划
Chapter Writer 必须产出 state_annotations
Narrative Polisher 不得改变剧情事实
修复重写最多1次
```

## 7.2 状态更新约束

```text
只有 approved 状态的章节可以触发状态更新
Approve + State Update 必须原子操作
draft 状态的章节不得更新全局状态
reviewed 状态的章节不得自动更新全局状态
状态更新必须生成 snapshot
状态更新失败时不得覆盖旧状态
状态更新优先采用 state_annotations
用户修改的剧情点优先级高于 AI 标注
```

## 7.3 文风约束

```text
文风资产保存抽象特征
不保存大段原文作为生成模板
Narrative Polisher 不得改变剧情事实
Narrative Polisher 不得新增重大设定
Narrative Polisher 不得改变人物动机
 Narrative Polisher 不得改变伏笔状态
条件文风规则按场景类型匹配
每个角色必须有独立声音资产
```

## 7.4 上下文约束

```text
Context Assembler 按优先级筛选
Context Compiler 在 Assembler 产出上进行叙事推理
默认包含最近3章摘要
默认包含本章相关角色
默认包含当前卷目标
默认包含高优先级未解决伏笔
默认不包含全部历史正文
Token 预算分配按固定比例
超过预算时按优先级截断
截断时启用降级策略
```

## 7.5 审查约束

```text
每次章节审查必须包含4个维度: 连续性 + 质量 + 跨章 + 读者模拟
跨章审查至少回看3章
Reader Simulator 必须输出弃书风险评分
结构化修复指令由审查报告合并生成
修复重写后不再重复审查 (信任修复指令的执行)
```

## 7.6 Agent Contract 约束

```text
Chapter Planner 输出必须包含 Agent Contract
Chapter Writer 必须自检 Agent Contract
Agent Contract 不满足时必须记录原因
下游 Agent 发现上游 Contract 未满足时，在输出中标记
```

## 7.7 Bible 版本约束

```text
Bible 更新必须通过 bible_update_proposal
Bible 版本号每次更新 +1
Bible 更新必须记录 changelog
每次状态更新后检测 Bible 是否需要演进
```

---

# 八、质量验收标准

## 8.1 功能验收

MVP 完成时，系统需要支持:

```text
创建一个小说项目 (渐进式3轮)
上传样本文本并生成文风资产 (含对抗测试)
生成小说启动文档 (含 Writing Strategy + Subplot Registry)
编译第1章上下文 (含叙事诊断 + 状态健康报告)
生成第1章规划 (含节奏规划 + 子线分配 + Agent Contract)
生成第1章正文 (含状态标注)
文风润色 (Narrative Polish)
审查第1章 (4维度审查 + 结构化修复指令)
修复重写 (最多1次)
用户确认第1章
系统更新角色、时间线、伏笔、子线、全局状态
系统检测 Bible 是否需要演进
系统生成下一章建议
编译第2章上下文 (基于更新后的状态)
```

## 8.2 连续性验收

连续生成 5 章后，系统需要满足:

| 指标 | 标准 |
|------|------|
| 角色状态矛盾率 | < 5% |
| 时间线跳跃错误 | 0 |
| 已埋伏笔遗忘率 | < 10% |
| 信息边界违规 | 0 |
| 子线遗忘 (超过策略阈值未推进) | 0 |
| 角色发展遗漏 (连续N章无发展) | 0 |

## 8.3 写作质量验收

| 指标 | 标准 |
|------|------|
| 每章有明确冲突 | 100% |
| 每章结尾有继续阅读驱动力 | 100% |
| 连续3章无爽点 | 0 次 |
| 对白与叙述比例偏离文风资产定义 | < 15% |
| 角色声音区分度 | 可辨识 |
| 读者模拟器评分 | > 7/10 |
| 弃书风险评分 | < 4/10 |

## 8.4 节奏验收

| 指标 | 标准 |
|------|------|
| 连续2章同节奏类型 | 0 次 |
| 子线遗忘 (超过策略阈值) | 0 次 |
| 主角连续2章无实质进展 | 0 次 |
| 伏笔过载 (超过策略上限) | 0 次 |

---

# 九、开发计划

## 总体: 15 Phase (不压缩工期，保证质量)

```
Phase 1:  项目骨架 + 项目管理模块
Phase 2:  LLM 调用层 + Prompt 体系 + 输出校验框架
Phase 3:  文风资产 + Character Voice Asset + 对抗测试
Phase 4:  Novel Bible 渐进式生成 + Bible 版本管理
Phase 5:  Subplot Registry + Hook 增强 + Writing Strategy Config
Phase 6:  Context Assembler (代码) + Token 预算管理
Phase 7:  Context Compiler (Agent) + State Health Checker (代码)
Phase 8:  Chapter Planner (含节奏规划 + 子线分配 + Agent Contract)
Phase 9:  Chapter Writer (含状态标注) + Narrative Polisher
Phase 10: Continuity Auditor + Quality Auditor
Phase 11: Cross-Chapter Auditor + Reader Simulator
Phase 12: State Updater (标注确认式 + diff 感知) + Bible Updater + Snapshot + 回滚
Phase 13: 闭环测试 + 连续5章验证 + 量化验收
Phase 14: CLI 完善
Phase 15: Web UI
```

---

### Phase 1: 项目骨架 + 项目管理模块

实现:
```text
FastAPI 项目初始化
项目目录结构自动创建
project.yaml CRUD
文件资产管理 (读写 Markdown/YAML)
SQLite 索引 (项目元信息、任务状态)
```

验收标准:
```text
创建项目后自动生成完整目录结构
可以对项目进行 CRUD 操作
```

---

### Phase 2: LLM 调用层 + Prompt 体系 + 输出校验框架

实现:
```text
LLM Provider Adapter (OpenAI Compatible)
Prompt Template Loader
输出校验框架:
  - 格式校验 (YAML/Markdown 解析)
  - 必填字段校验
  - 失败重试 (带错误信息重试1次)
  - 仍然失败则标记任务 failed + 保留原始输出
异步任务 (用 FastAPI BackgroundTasks，不用复杂队列)
```

验收标准:
```text
可以调用 LLM 并把结果保存到指定文件
输出格式不对时可以自动重试1次
任务状态可查询
```

---

### Phase 3: 文风资产 + Character Voice Asset + 对抗测试

实现:
```text
Style Analyst Agent + prompt
Character Voice Asset 数据结构
文风资产生成流程
文风对抗测试:
  - 生成偏离文风的段落
  - 验证文风资产能否识别偏离
  - 调整直到通过
Style API
```

验收标准:
```text
上传样本后可以生成完整的 style_asset.yaml
对抗测试通过 (能识别故意偏离的文风)
生成测试段落与样本风格一致
```

---

### Phase 4: Novel Bible 渐进式生成 + Bible 版本管理

实现:
```text
Story Architect Agent + prompt
渐进式3轮生成流程:
  - Round 1: 方向变体
  - Round 2: 角色概念 + Voice Asset
  - Round 3: 完整 Bible
Bible 版本管理 (changelog)
Bible API
Writing Strategy Config 初始生成
Subplot Registry 初始生成
```

验收标准:
```text
3轮渐进式生成流程可跑通
Bible 内容完整且有质量
Bible 版本记录可追溯
```

---

### Phase 5: Subplot Registry + Hook 增强 + Writing Strategy Config

实现:
```text
Subplot 数据结构 + CRUD
Hook 增强 (类型、紧迫度、回收策略、读者耐心)
Writing Strategy Config 数据结构 + CRUD
Subplot API
Hook API (增强版)
```

验收标准:
```text
子线可以创建、更新、查询
伏笔可以按类型、紧迫度、状态筛选
Writing Strategy Config 可读写
```

---

### Phase 6: Context Assembler (代码) + Token 预算管理

实现:
```text
Context Assembler Python 代码:
  - 读取所有 state/asset 文件
  - 按优先级筛选
  - Token 预算分配
  - 超预算截断 + 降级策略
  - 拼装 raw_context.md
Token 预算配置
Context API
```

验收标准:
```text
给定 chapter_id 可以自动拼装 raw_context.md
Token 预算分配合理
超出预算时按优先级截断
```

---

### Phase 7: Context Compiler (Agent) + State Health Checker (代码)

实现:
```text
Context Compiler Agent + prompt
  - 叙事推理
  - 诊断
  - 建议
State Health Checker Python 代码:
  - 所有检查规则
  - 生成 state_health_report.yaml
Context Compile API
```

验收标准:
```text
raw_context + health_report 可以编译成完整的 context_pack.md
context_pack.md 包含叙事诊断章节
state_health_report 正确检测各类异常
```

---

### Phase 8: Chapter Planner (含节奏规划 + 子线分配 + Agent Contract)

实现:
```text
Chapter Planner Agent + prompt
节奏规划逻辑
子线分配逻辑
Agent Contract 生成
Chapter Plan API
```

验收标准:
```text
给定 context_pack 可以生成完整的 chapter_plan.md
chapter_plan 包含节奏规划、子线分配、Agent Contract
节奏规划与前章节奏形成合理搭配
子线分配符合 Writing Strategy 中的策略
```

---

### Phase 9: Chapter Writer (含状态标注) + Narrative Polisher

实现:
```text
Chapter Writer Agent + prompt (含状态标注)
Narrative Polisher Agent + prompt (含条件文风规则)
Chapter Draft API
Narrative Polish API
```

验收标准:
```text
给定 context_pack + chapter_plan + style_asset 可以生成 draft.md
draft.md 同时产出 state_annotations.yaml
state_annotations 覆盖所有关键状态变化
Narrative Polisher 润色后不改变剧情事实
Narrative Polisher 润色后文风与 style_asset 一致
```

---

### Phase 10: Continuity Auditor + Quality Auditor

实现:
```text
Continuity Auditor Agent + prompt
Quality Auditor Agent + prompt (含量化评分 + 前章比较)
Review API
结构化修复指令生成
Fix API
```

验收标准:
```text
可以检测连续性违规
可以给出 1-10 量化评分
修复指令结构化、可执行
```

---

### Phase 11: Cross-Chapter Auditor + Reader Simulator

实现:
```text
Cross-Chapter Auditor Agent + prompt
Reader Simulator Agent + prompt
4维度审查聚合
Review API 扩展
```

验收标准:
```text
跨章诊断能检测节奏重复、子线遗忘、伏笔过载
Reader Simulator 能预测读者体验 (兴奋点、无聊点、弃书风险)
4维度审查报告聚合后可生成结构化修复指令
```

---

### Phase 12: State Updater + Bible Updater + Snapshot + 回滚

实现:
```text
State Updater Agent + prompt (标注确认式 + diff 感知)
Bible Updater 检测逻辑
Bible Update Proposal 生成
Snapshot Manager
回滚机制
Approve + State Update 原子操作
State Update API
Bible Update API
Snapshot API
Rollback API
```

验收标准:
```text
基于 state_annotations 和 diff 可以正确更新所有 state 文件
Bible 检测可以在需要时生成 update_proposal
回滚可以恢复到任意章节的 snapshot
Approve + State Update 原子操作 (一起成功或一起失败)
```

---

### Phase 13: 闭环测试 + 连续5章验证 + 量化验收

实现:
```text
端到端闭环测试:
  创建项目 → 文风 → Bible → 第1章全流程 → 确认 → 状态更新 → 第2章
连续5章生成测试
量化验收标准测试
Prompt 调优
错误处理 + 边界情况
```

验收标准:
```text
闭环跑通无报错
连续5章: 角色状态无矛盾、时间线无跳跃、伏笔被记录、子线被推进
量化验收标准全部达标
```

---

### Phase 14: CLI 完善

实现:
```text
novel init
novel style analyze
novel bible generate
novel context compile --chapter N
novel chapter plan --chapter N
novel chapter draft --chapter N
novel chapter polish --chapter N
novel chapter review --chapter N
novel chapter fix --chapter N
novel chapter approve --chapter N
novel state update --chapter N
novel state rollback --chapter N
novel next suggest
novel bible update --chapter N
novel subplot list
novel hook list
novel health check
```

验收标准:
```text
所有 CLI 命令可用
每一步的输入输出正确
错误信息清晰
```

---

### Phase 15: Web UI

实现:
```text
React 项目 (Vite + TypeScript)
三栏布局
项目创建 (渐进式3轮)
资产浏览
章节编辑 (Markdown编辑器)
章节状态流转
AI 操作面板
审查报告展示 (4维度)
状态快照查看 + Diff
Bible 版本管理
Subplot 管理
Hook 管理
Writing Strategy 配置
```

验收标准:
```text
所有后端 API 都有对应 UI
渐进式 Bible 生成交互完整
章节全流程可以纯 UI 操作
审查报告清晰可读
```

---

# 十、技术栈

## 后端

```text
Python 3.11+
FastAPI
SQLite (项目元信息、任务状态)
YAML (结构化状态)
Markdown (正文、报告、Prompt)
Pydantic (数据校验)
```

## 前端

```text
React 18+
TypeScript
Vite
Markdown 编辑器 (如 Milkdown 或 Editor.js)
文件树组件
```

## 存储

```text
Markdown 保存正文和报告
YAML 保存结构化状态
SQLite 保存索引、项目元信息、任务状态
文件系统保存所有资产 (git 友好)
```

## LLM

```text
LLM Provider Adapter (OpenAI Compatible 优先)
配置:
  provider: "openai_compatible"
  base_url: "https://api.example.com/v1"
  model: "model-name"
  api_key_env: "LLM_API_KEY"
后续适配: Ollama / DeepSeek / Qwen / Claude
```

---

# 十一、风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 输出格式不稳定 | Agent 解析失败 | 输出校验框架 + 重试 + 降级处理 |
| LLM 输出质量不稳定 | 章节质量不达标 | Prompt 模板版本化 + A/B 测试 + 量化评分 |
| 状态标注遗漏 | State Updater 漏掉变化 | 标注确认 + LLM 推理补充 + 用户 diff 优先 |
| Token 预算不足 | 上下文丢失关键信息 | 优先级截断 + 降级策略 + 叙事推理弥补 |
| 修复重写无限循环 | 资源浪费 | 最多1次修复重写 |
| Bible 与故事演进脱节 | 设定矛盾 | Bible Updater 自动检测 + 版本演进 |
| 子线管理过于复杂 | Prompt 过长 | 子线按优先级筛选 + 只包含本章相关的 |
| 跨章审查误差累积 | 多章后诊断不准 | 每5章做一次全局回顾 |
| Agent Contract 未满足 | 下游 Agent 产出异常 | 自检机制 + 标记未满足项 |
| 读者模拟器评分不准 | 无法可靠评估 | 辅助参考维度，不做唯一判据 |

---

# 十二、最小闭环定义

本项目第一版真正完成的标志:

```text
创建项目 (渐进式3轮)
→ 生成文风资产 (含对抗测试)
→ 生成小说启动文档 (含 Writing Strategy + Subplot Registry)
→ 编译第1章上下文 (含叙事诊断 + 状态健康报告)
→ 生成第1章规划 (含节奏规划 + 子线分配 + Agent Contract)
→ 生成第1章正文 (含状态标注)
→ 文风润色
→ 4维度审查 (连续性 + 质量 + 跨章 + 读者模拟)
→ 修复重写 (如需要)
→ 用户确认第1章
→ 状态更新 (标注确认式 + diff感知)
→ Bible 演进检测
→ 编译第2章上下文
→ 连续5章验证通过量化验收标准
```

只要这个闭环稳定，系统就具备继续扩展的基础。