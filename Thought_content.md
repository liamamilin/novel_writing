下面是 5 轮审核后的结论：**方向成立，但需要把“自动写小说”收敛成“小说持续生产运行时系统”**。真正的核心不是一次生成多少字，而是每一章都能完成：

```text
编译上下文 → 规划本章 → 生成正文 → 审查修改 → 确认章节 → 更新状态 → 进入下一章
```

5 轮审核后的关键修正是：

1. **产品定位修正**：从“自动写整本小说”改成“自动化小说边写工具”，避免质量失控。
2. **流程修正**：每章必须有人工确认节点，不允许生成后直接污染全局状态。
3. **上下文修正**：不要把所有历史正文塞给模型，要生成 `Chapter Context Pack`。
4. **Agent 修正**：写作、审查、状态更新必须分离，不能让同一个 Agent 同时创作和自证正确。
5. **工程修正**：MVP 先用 Markdown/YAML/SQLite 跑通，不急着做复杂平台化。

下面是开发用 specification。

# 自动化小说边写工具 Development Specification v0.1

## 1. 产品名称

**Novel Writing Runtime**
中文名：**自动化小说边写运行时**

## 2. 产品定位

本工具是一个面向网络小说创作的 AI 辅助写作系统。

它的核心目标不是一次性自动生成完整小说，而是帮助作者长期、稳定、连续地完成小说创作过程。

系统需要管理：

* 文风资产 Style Asset
* 小说启动文档 Novel Bible
* 角色状态 Character State
* 世界观设定 World Setting
* 历史章节 Chapter History
* 当前剧情状态 Current State
* 伏笔与钩子 Hooks
* 本章上下文 Chapter Context
* 章节生成 Chapter Generation
* 章节审查 Chapter Review
* 状态更新 State Update

系统的基本原则是：

> 每次写作前，先编译上下文；每次确认章节后，立刻更新状态。

---

# 3. 核心目标

## 3.1 第一目标

帮助用户持续写网络小说。

系统需要做到：

```text
用户提供创意、方向、设定、偏好
系统帮助整理小说启动文档
系统根据上下文生成章节规划
系统生成章节正文
系统审查章节质量
用户确认后系统更新小说状态
系统基于新状态继续生成下一章
```

## 3.2 第二目标

把小说创作过程资产化。

资产包括：

```text
文风资产
角色资产
世界观资产
章节资产
伏笔资产
剧情状态资产
审查报告资产
上下文包资产
```

## 3.3 第三目标

让小说可以长期写下去。

系统要解决以下问题：

```text
剧情跑偏
人物状态混乱
设定前后矛盾
伏笔遗忘
章节节奏失控
文风不稳定
历史上下文过长
大模型遗忘前文
```

---

# 4. 非目标

MVP 阶段暂时不做以下能力：

```text
不做多平台自动发布
不做付费阅读平台对接
不做复杂版权管理
不做多人协作
不做完整商业数据分析
不做爆款预测
不做自动生成整本书后直接发布
```

MVP 的目标是先跑通小说持续生成闭环。

---

# 5. 用户角色

## 5.1 作者 Author

主要使用者。

作者负责：

```text
创建小说项目
上传文风样本
确认小说方向
确认章节规划
修改或确认章节正文
决定是否进入下一章
```

## 5.2 系统 System

系统负责：

```text
整理创作资产
生成上下文包
规划章节
生成正文
审查章节
抽取状态
更新资产
提供下一章建议
```

---

# 6. 核心工作流

## 6.1 小说项目创建流程

```text
用户创建项目
输入小说类型、核心创意、目标读者、目标风格
系统生成初版 Novel Bible
用户修改或确认 Novel Bible
系统生成前10章规划
系统生成第1章详细规划
项目进入可写作状态
```

输出文件：

```text
novel_bible.md
world_setting.md
character_profiles.md
volume_plan.md
chapter_plan.md
```

---

## 6.2 文风资产生成流程

```text
用户上传样本文本
系统分析样本文本
系统抽取文风参数
系统生成 style_asset.yaml
系统基于文风资产生成测试段落
用户校准文风
系统保存最终文风资产
```

文风资产不保存为“模仿某个作者”，而保存为抽象写作参数。

示例：

```yaml
style_id: "style_urban_fast_001"
style_name: "都市快节奏爽文"
narration: "第三人称贴身视角"
sentence_rhythm: "短句为主，中等长度句子辅助"
dialogue_style: "对白直接，冲突感强"
emotion_curve: "压迫感 -> 反击 -> 爽感释放"
scene_density: "每300-500字出现一次动作或冲突变化"
chapter_opening: "用冲突、异常事件或人物压力开场"
chapter_ending: "用反转、威胁或新信息收尾"
avoid:
  - "大段设定说明"
  - "连续心理独白"
  - "重复口癖"
  - "过度形容"
```

---

## 6.3 单章生成流程

```text
用户选择当前章节
用户输入或选择本章目标
系统编译 Chapter Context Pack
系统生成章节剧情骨架
系统生成场景列表
系统生成正文草稿
系统按文风资产重写
系统生成章节审查报告
用户修改或确认
确认后进入状态更新流程
```

---

## 6.4 状态更新流程

```text
用户确认章节
系统读取最终章节正文
系统抽取章节摘要
系统更新角色状态
系统更新时间线
系统更新伏笔状态
系统更新世界观新增信息
系统生成下一章建议
系统保存 State Snapshot
```

只有用户确认后的章节才允许更新全局状态。

---

# 7. 系统模块

## 7.1 Project Manager 项目管理模块

负责小说项目的创建、读取、保存、归档。

功能：

```text
创建项目
读取项目
列出项目
更新项目元信息
保存项目配置
归档项目
```

核心字段：

```yaml
project_id: "novel_20260616_xxxxx"
project_name: "小说项目名称"
genre: "都市 / 玄幻 / 修仙 / 科幻 / 无限流 / 悬疑"
status: "drafting"
created_at: "2026-06-16"
updated_at: "2026-06-16"
default_style_id: "style_001"
current_chapter_id: "chapter_001"
```

---

## 7.2 Style Asset Manager 文风资产管理模块

负责文风学习、文风保存、文风调用。

功能：

```text
上传样本文本
分析样本文本
生成文风资产
保存文风资产
列出文风资产
选择文风资产
基于文风资产重写文本
```

文风分析输出：

```text
叙述视角
句式节奏
对白风格
描写密度
情绪曲线
冲突推进方式
章节开头方式
章节结尾方式
常见表达模式
禁用表达模式
```

约束：

```text
系统抽象文风特征，不复制原文表达。
系统避免生成可识别的原文复刻。
系统优先学习通用叙事参数、节奏参数、结构参数。
```

---

## 7.3 Novel Bible Manager 小说启动文档模块

负责生成和维护小说基础设计文档。

Novel Bible 包含：

```text
小说一句话卖点
目标读者
小说类型
核心爽点
主角设定
主角初始处境
主角长期目标
主角阶段目标
主角能力系统
主要反派
核心冲突
世界规则
主要人物关系
第一卷目标
前10章规划
前50章粗略路线
```

输出文件：

```text
bible/novel_bible.md
bible/world_setting.md
bible/character_profiles.md
bible/volume_plan.md
bible/chapter_plan.md
```

---

## 7.4 Context Compiler 上下文编译器

这是系统核心模块。

它负责在生成章节前，把所有相关资产编译成本章可用的上下文包。

输入：

```text
Novel Bible
World Setting
Style Asset
Current State
Character State
Recent Chapter Summaries
Hooks
Timeline
User Chapter Goal
```

输出：

```text
Chapter Context Pack
```

Context Pack 内容：

```markdown
# Chapter Context Pack

## Project Info
项目名称：
小说类型：
当前卷：
当前章节：

## Style Asset
当前文风：
叙述视角：
句子节奏：
对白风格：
章节结尾要求：

## Global Story Context
小说核心卖点：
主线目标：
当前卷目标：

## Recent Chapters
最近3章摘要：

## Current State
当前地点：
当前时间：
当前冲突：
当前主角状态：

## Character State
本章相关人物：
每个人物当前目标：
每个人物已知信息：
每个人物未知信息：
人物关系变化：

## Hooks
本章可触发伏笔：
本章禁止遗忘伏笔：
即将回收伏笔：

## Chapter Goal
本章必须完成：
本章可以推进：
本章禁止破坏：

## Generation Constraints
字数范围：
节奏要求：
爽点要求：
结尾钩子要求：
```

规则：

```text
默认读取最近3章摘要
默认读取当前卷目标
默认读取本章相关角色
默认读取未解决高优先级伏笔
默认读取当前文风资产
不默认读取全部正文
不把无关设定塞入上下文包
```

---

## 7.5 Chapter Planner 章节规划模块

负责把本章目标变成章节结构。

输入：

```text
Chapter Context Pack
```

输出：

```text
章节目标
章节冲突
场景列表
场景功能
场景转折
章节结尾
```

章节规划格式：

```markdown
# Chapter Plan

## Chapter Goal
本章目标：

## Reader Promise
本章给读者的期待：

## Conflict
主要冲突：

## Scene List

### Scene 1
地点：
出场人物：
场景功能：
冲突：
转折：
输出结果：

### Scene 2
地点：
出场人物：
场景功能：
冲突：
转折：
输出结果：

## Ending Hook
结尾钩子：
```

---

## 7.6 Chapter Writer 章节正文生成模块

负责根据章节规划生成正文。

输入：

```text
Chapter Context Pack
Chapter Plan
Style Asset
```

输出：

```text
Chapter Draft
```

生成规则：

```text
严格按照场景列表生成
保持人物信息边界
保持当前时间线一致
不提前暴露未公开秘密
不跳过关键冲突
每个场景都要产生状态变化
结尾必须保留下一章驱动力
```

---

## 7.7 Style Rewriter 文风重写模块

负责把章节草稿调整到选定文风资产。

输入：

```text
Chapter Draft
Style Asset
```

输出：

```text
Styled Chapter Draft
```

重写动作：

```text
调整句子节奏
调整对白密度
调整描写比例
调整情绪曲线
强化文风特征
删除不符合文风的表达
保持剧情事实不变
```

硬约束：

```text
不得改变剧情事实
不得新增重大设定
不得改变人物动机
不得改变伏笔状态
```

---

## 7.8 Continuity Auditor 连续性审查模块

负责检查章节是否破坏既有状态。

输入：

```text
Styled Chapter Draft
Chapter Context Pack
Character State
Timeline
Hooks
World Setting
```

输出：

```text
Continuity Review Report
```

审查维度：

```text
人物状态一致性
时间线一致性
地点一致性
能力体系一致性
人物已知信息边界
伏笔状态一致性
世界规则一致性
章节目标完成度
```

报告格式：

```markdown
# Continuity Review Report

## Summary
整体判断：

## Issues

### Issue 1
问题类型：
问题位置：
问题说明：
修改动作：

### Issue 2
问题类型：
问题位置：
问题说明：
修改动作：

## Pass Conditions
需要修正后通过的条件：
```

---

## 7.9 Quality Auditor 章节质量审查模块

负责检查章节是否好看、是否有网络小说节奏。

输入：

```text
Styled Chapter Draft
Chapter Plan
Style Asset
```

输出：

```text
Quality Review Report
```

审查维度：

```text
开头吸引力
冲突强度
爽点释放
节奏推进
对白有效性
信息密度
场景变化
人物行为目的
结尾钩子
文风一致性
```

报告格式：

```markdown
# Quality Review Report

## Score
开头：
冲突：
节奏：
爽点：
文风：
结尾：

## Main Problems
问题：
修改动作：

## Rewrite Suggestions
具体修改建议：
```

---

## 7.10 State Updater 状态更新模块

负责从用户确认后的最终章节中抽取状态变化。

输入：

```text
Final Chapter Text
Previous State
Hooks
Timeline
Character State
```

输出：

```text
Updated State Snapshot
```

更新内容：

```text
章节摘要
角色状态
人物关系
时间线
地点变化
新增设定
新增伏笔
触发伏笔
回收伏笔
主角能力变化
敌对关系变化
下一章建议
```

状态更新格式：

```yaml
chapter_id: "chapter_023"
title: "拍卖会上的异变"

summary: >
  主角在拍卖会上识破被低估的古物，引发众人震惊。
  反派当众质疑失败，神秘势力开始注意主角。

character_updates:
  protagonist:
    location: "云海拍卖会"
    current_goal: "隐藏实力并获得古物"
    exposed_abilities:
      - "部分鉴定能力"
    relationship_changes:
      - target: "林雪"
        change: "建立初步信任"
      - target: "赵坤"
        change: "敌意增强"

new_hooks:
  - hook_id: "H012"
    content: "神秘人要求调查主角来历"
    source_chapter: "chapter_023"
    priority: "high"
    planned_payoff_range: "chapter_030_to_035"

resolved_hooks:
  - hook_id: "H007"
    resolution: "古物真实价值被揭示"

world_updates:
  - "云海拍卖会背后存在隐藏势力"

next_chapter_suggestions:
  - "神秘人派人试探主角"
  - "赵坤进行第一次报复"
  - "林雪邀请主角私下见面"
```

---

# 8. 数据结构

## 8.1 Project

```yaml
project_id: string
project_name: string
genre: string
status: draft | active | paused | archived
default_style_id: string
current_volume_id: string
current_chapter_id: string
created_at: datetime
updated_at: datetime
```

---

## 8.2 StyleAsset

```yaml
style_id: string
style_name: string
source_text_ids: list
narration: string
sentence_rhythm: string
dialogue_style: string
description_density: string
emotion_curve: string
conflict_pattern: string
chapter_opening: string
chapter_ending: string
avoid: list
created_at: datetime
updated_at: datetime
```

---

## 8.3 Chapter

```yaml
chapter_id: string
chapter_number: int
title: string
status: planned | drafted | reviewed | approved | locked
plan_path: string
draft_path: string
final_path: string
review_path: string
context_pack_path: string
summary: string
created_at: datetime
updated_at: datetime
```

---

## 8.4 CharacterState

```yaml
character_id: string
name: string
role: protagonist | antagonist | supporting | minor
current_location: string
current_goal: string
current_emotion: string
known_information: list
unknown_information: list
abilities: list
secrets: list
relationships: list
last_seen_chapter: string
next_use_suggestion: string
```

---

## 8.5 Hook

```yaml
hook_id: string
content: string
source_chapter: string
status: open | triggered | resolved | abandoned
priority: low | medium | high
related_characters: list
planned_payoff_range: string
actual_payoff_chapter: string
notes: string
```

---

## 8.6 TimelineEvent

```yaml
event_id: string
chapter_id: string
story_time: string
location: string
characters: list
event_summary: string
state_change: string
```

---

# 9. 文件目录结构

MVP 阶段采用文件资产库。

```text
novel_project/
  project.yaml

  style_assets/
    style_001.yaml
    style_002.yaml

  source_texts/
    sample_001.txt
    sample_002.txt

  bible/
    novel_bible.md
    world_setting.md
    character_profiles.md
    volume_plan.md
    chapter_plan.md

  chapters/
    chapter_001/
      context_pack.md
      chapter_plan.md
      draft.md
      styled_draft.md
      final.md
      review_continuity.md
      review_quality.md

    chapter_002/
      context_pack.md
      chapter_plan.md
      draft.md
      styled_draft.md
      final.md
      review_continuity.md
      review_quality.md

  states/
    global_state.yaml
    character_state.yaml
    timeline.yaml
    hooks.yaml
    relationship_state.yaml

  snapshots/
    state_after_chapter_001.yaml
    state_after_chapter_002.yaml

  prompts/
    style_analysis.md
    novel_bible_generation.md
    context_compile.md
    chapter_plan.md
    chapter_write.md
    style_rewrite.md
    continuity_review.md
    quality_review.md
    state_update.md
```

---

# 10. API Specification

## 10.1 Project API

### Create Project

`POST /api/projects`

Request:

```json
{
  "project_name": "都市修仙项目",
  "genre": "都市修仙",
  "idea": "一个被家族抛弃的年轻人意外获得古老传承，在现代都市中崛起。",
  "target_style": "快节奏爽文"
}
```

Response:

```json
{
  "project_id": "novel_20260616_001",
  "status": "created"
}
```

---

### Get Project

`GET /api/projects/{project_id}`

Response:

```json
{
  "project_id": "novel_20260616_001",
  "project_name": "都市修仙项目",
  "genre": "都市修仙",
  "current_chapter_id": "chapter_001",
  "status": "active"
}
```

---

## 10.2 Style API

### Upload Style Sample

`POST /api/projects/{project_id}/style-samples`

Request:

```json
{
  "sample_name": "样本文风1",
  "text": "样本文本内容"
}
```

Response:

```json
{
  "sample_id": "sample_001",
  "status": "uploaded"
}
```

---

### Analyze Style

`POST /api/projects/{project_id}/styles/analyze`

Request:

```json
{
  "sample_ids": ["sample_001", "sample_002"],
  "style_name": "都市快节奏爽文"
}
```

Response:

```json
{
  "style_id": "style_001",
  "style_asset_path": "style_assets/style_001.yaml"
}
```

---

## 10.3 Bible API

### Generate Novel Bible

`POST /api/projects/{project_id}/bible/generate`

Request:

```json
{
  "idea": "一个被家族抛弃的年轻人意外获得古老传承，在现代都市中崛起。",
  "genre": "都市修仙",
  "target_reader": "喜欢快节奏打脸升级的读者",
  "core_selling_point": "现代都市中的修仙逆袭"
}
```

Response:

```json
{
  "bible_path": "bible/novel_bible.md",
  "chapter_plan_path": "bible/chapter_plan.md"
}
```

---

## 10.4 Context API

### Compile Chapter Context

`POST /api/projects/{project_id}/chapters/{chapter_id}/context/compile`

Request:

```json
{
  "chapter_goal": "主角第一次公开展示鉴定能力，但不能完全暴露底牌。",
  "style_id": "style_001"
}
```

Response:

```json
{
  "context_pack_path": "chapters/chapter_023/context_pack.md"
}
```

---

## 10.5 Chapter API

### Generate Chapter Plan

`POST /api/projects/{project_id}/chapters/{chapter_id}/plan`

Request:

```json
{
  "context_pack_path": "chapters/chapter_023/context_pack.md"
}
```

Response:

```json
{
  "chapter_plan_path": "chapters/chapter_023/chapter_plan.md"
}
```

---

### Generate Chapter Draft

`POST /api/projects/{project_id}/chapters/{chapter_id}/draft`

Request:

```json
{
  "context_pack_path": "chapters/chapter_023/context_pack.md",
  "chapter_plan_path": "chapters/chapter_023/chapter_plan.md",
  "target_word_count": 3000
}
```

Response:

```json
{
  "draft_path": "chapters/chapter_023/draft.md"
}
```

---

### Rewrite With Style

`POST /api/projects/{project_id}/chapters/{chapter_id}/style-rewrite`

Request:

```json
{
  "draft_path": "chapters/chapter_023/draft.md",
  "style_id": "style_001"
}
```

Response:

```json
{
  "styled_draft_path": "chapters/chapter_023/styled_draft.md"
}
```

---

### Review Chapter

`POST /api/projects/{project_id}/chapters/{chapter_id}/review`

Request:

```json
{
  "chapter_text_path": "chapters/chapter_023/styled_draft.md",
  "review_types": ["continuity", "quality"]
}
```

Response:

```json
{
  "continuity_review_path": "chapters/chapter_023/review_continuity.md",
  "quality_review_path": "chapters/chapter_023/review_quality.md"
}
```

---

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
  "status": "approved"
}
```

---

### Update State After Chapter

`POST /api/projects/{project_id}/chapters/{chapter_id}/state/update`

Request:

```json
{
  "final_chapter_path": "chapters/chapter_023/final.md"
}
```

Response:

```json
{
  "snapshot_path": "snapshots/state_after_chapter_023.yaml",
  "updated_files": [
    "states/character_state.yaml",
    "states/timeline.yaml",
    "states/hooks.yaml",
    "states/global_state.yaml"
  ]
}
```

---

# 11. Agent 设计

## 11.1 Style Analyst Agent

职责：

```text
分析样本文本
抽取文风参数
生成文风资产
生成测试段落
```

输入：

```text
样本文本
目标文风名称
```

输出：

```text
style_asset.yaml
style_analysis_report.md
```

---

## 11.2 Story Architect Agent

职责：

```text
根据用户创意生成 Novel Bible
生成角色设定
生成世界观设定
生成前10章规划
```

输入：

```text
小说创意
类型
目标读者
核心爽点
```

输出：

```text
novel_bible.md
character_profiles.md
world_setting.md
chapter_plan.md
```

---

## 11.3 Context Compiler Agent

职责：

```text
读取项目资产
筛选本章相关上下文
生成 Chapter Context Pack
```

输入：

```text
project_id
chapter_id
chapter_goal
style_id
```

输出：

```text
context_pack.md
```

---

## 11.4 Chapter Planner Agent

职责：

```text
把本章目标拆成章节结构
生成场景列表
设计冲突推进
设计结尾钩子
```

输入：

```text
context_pack.md
```

输出：

```text
chapter_plan.md
```

---

## 11.5 Chapter Writer Agent

职责：

```text
根据章节规划生成正文草稿
保持剧情事实一致
保持人物行为目的清晰
```

输入：

```text
context_pack.md
chapter_plan.md
style_asset.yaml
```

输出：

```text
draft.md
```

---

## 11.6 Style Rewriter Agent

职责：

```text
按照文风资产重写草稿
只改表达，不改剧情事实
```

输入：

```text
draft.md
style_asset.yaml
```

输出：

```text
styled_draft.md
```

---

## 11.7 Continuity Auditor Agent

职责：

```text
审查前后矛盾
审查人物状态
审查世界规则
审查伏笔状态
```

输入：

```text
styled_draft.md
context_pack.md
states/
```

输出：

```text
review_continuity.md
```

---

## 11.8 Quality Auditor Agent

职责：

```text
审查章节可读性
审查爽点
审查节奏
审查开头和结尾
审查对白有效性
```

输入：

```text
styled_draft.md
chapter_plan.md
style_asset.yaml
```

输出：

```text
review_quality.md
```

---

## 11.9 State Updater Agent

职责：

```text
从最终章节抽取状态变化
更新角色状态
更新时间线
更新伏笔
生成下一章建议
```

输入：

```text
final.md
previous_state
```

输出：

```text
state_after_chapter_xxx.yaml
updated states/
```

---

# 12. UI Specification

## 12.1 页面结构

推荐三栏布局。

```text
左侧：项目资产区
中间：章节编辑区
右侧：AI 操作区
```

---

## 12.2 左侧：项目资产区

显示：

```text
小说启动文档
文风资产
角色表
世界观设定
章节列表
伏笔表
时间线
审查报告
状态快照
```

操作：

```text
打开文件
编辑文件
选择当前文风
选择当前章节
查看状态快照
```

---

## 12.3 中间：章节编辑区

显示当前章节。

状态：

```text
未规划
已规划
草稿中
已生成
已审查
已确认
已锁定
```

操作：

```text
编辑正文
保存草稿
查看章节规划
查看审查报告
确认最终章节
```

---

## 12.4 右侧：AI 操作区

按钮：

```text
生成小说启动文档
分析文风资产
编译本章上下文
生成本章规划
生成章节草稿
按文风重写
审查连续性
审查章节质量
确认并更新状态
生成下一章建议
```

---

# 13. MVP 开发范围

## 13.1 MVP 必须实现

第一版只实现以下能力：

```text
项目创建
文风资产生成
小说启动文档生成
本章上下文编译
章节规划生成
章节草稿生成
章节审查
章节确认
状态更新
```

---

## 13.2 MVP 技术建议

后端：

```text
Python
FastAPI
SQLite
YAML / Markdown 文件资产
LLM Provider Adapter
```

前端：

```text
React
普通三栏布局
Markdown 编辑器
文件树
操作按钮
```

存储：

```text
Markdown 保存正文和报告
YAML 保存结构化状态
SQLite 保存索引、项目元信息、任务状态
```

---

## 13.3 MVP 不做

```text
复杂权限系统
多人协作
在线发布
高级检索
向量数据库
商业数据分析
读者评论分析
```

---

# 14. LLM Provider Adapter

系统需要抽象模型调用层。

接口：

```python
class LLMProvider:
    def generate(self, prompt: str, context: dict) -> str:
        pass
```

支持：

```text
OpenAI-compatible API
本地 Ollama
DeepSeek API
Qwen API
Claude API
```

配置示例：

```yaml
llm:
  provider: "openai_compatible"
  base_url: "https://api.example.com/v1"
  model: "model-name"
  api_key_env: "LLM_API_KEY"
```

---

# 15. 任务执行机制

长任务需要异步执行。

任务类型：

```text
style_analysis
bible_generation
context_compile
chapter_plan
chapter_draft
style_rewrite
continuity_review
quality_review
state_update
```

任务状态：

```text
pending
running
success
failed
cancelled
```

任务表字段：

```yaml
task_id: string
project_id: string
task_type: string
status: string
input: json
output: json
error: string
created_at: datetime
updated_at: datetime
```

---

# 16. 关键约束

## 16.1 章节生成约束

```text
生成正文前必须存在 Context Pack
生成正文前必须存在 Chapter Plan
正文生成必须绑定 Style Asset
正文生成不得跳过章节规划
```

---

## 16.2 状态更新约束

```text
只有 approved 状态的章节可以触发状态更新
draft 状态的章节不得更新全局状态
reviewed 状态的章节不得自动更新全局状态
状态更新必须生成 snapshot
状态更新失败时不得覆盖旧状态
```

---

## 16.3 文风约束

```text
文风资产保存抽象特征
不保存大段原文作为生成模板
文风重写不得改变剧情事实
文风重写不得新增重大设定
```

---

## 16.4 上下文约束

```text
Context Pack 只包含本章需要的信息
默认包含最近3章摘要
默认包含本章相关角色
默认包含当前卷目标
默认包含高优先级未解决伏笔
默认不包含全部历史正文
```

---

# 17. 质量验收标准

## 17.1 功能验收

MVP 完成时，系统需要支持：

```text
创建一个小说项目
上传样本文本并生成文风资产
生成小说启动文档
生成第1章上下文包
生成第1章章节规划
生成第1章正文草稿
生成章节审查报告
用户确认第1章
系统更新角色、时间线、伏笔、全局状态
系统生成第2章建议
```

---

## 17.2 连续性验收

连续生成 5 章后，系统需要满足：

```text
主角状态没有明显矛盾
主要人物关系没有混乱
时间线没有跳跃错误
已埋伏笔被记录
新增设定进入 world/state
每章都有摘要
每章都有状态快照
```

---

## 17.3 写作质量验收

生成章节需要满足：

```text
开头有明确吸引力
本章有明确冲突
人物行为有目的
场景之间有推进
结尾有继续阅读驱动力
文风与 Style Asset 基本一致
```

---

# 18. 推荐开发顺序

## Phase 1：文件资产骨架

实现：

```text
项目目录创建
project.yaml
bible/ 目录
chapters/ 目录
states/ 目录
style_assets/ 目录
```

完成标准：

```text
创建项目后自动生成完整目录结构
```

---

## Phase 2：LLM 调用层

实现：

```text
LLM Provider Adapter
Prompt Template Loader
任务执行器
结果保存器
```

完成标准：

```text
系统可以调用模型并把结果保存到指定文件
```

---

## Phase 3：文风资产

实现：

```text
上传样本文本
分析文风
生成 style_asset.yaml
生成测试段落
```

完成标准：

```text
用户可以选择一个文风资产用于章节生成
```

---

## Phase 4：Novel Bible

实现：

```text
根据用户创意生成 novel_bible.md
生成 character_profiles.md
生成 world_setting.md
生成 chapter_plan.md
```

完成标准：

```text
项目具备可写作的基础设定
```

---

## Phase 5：章节生产流水线

实现：

```text
编译 Context Pack
生成 Chapter Plan
生成 Draft
执行 Style Rewrite
生成 Review Report
```

完成标准：

```text
系统可以完成一章从规划到审查的完整流程
```

---

## Phase 6：状态更新

实现：

```text
章节确认
状态抽取
更新 character_state.yaml
更新 timeline.yaml
更新 hooks.yaml
生成 snapshot
生成下一章建议
```

完成标准：

```text
确认第1章后，系统可以基于更新后的状态继续生成第2章
```

---

# 19. 第一版核心命令

可以先做 CLI，再做 Web UI。

CLI 命令建议：

```bash
novel init
novel style analyze
novel bible generate
novel context compile --chapter 1
novel chapter plan --chapter 1
novel chapter draft --chapter 1
novel chapter review --chapter 1
novel chapter approve --chapter 1
novel state update --chapter 1
novel next suggest
```

CLI 跑通后，再接 Web UI。

---

# 20. 最小闭环定义

本项目第一版真正完成的标志不是页面多漂亮，而是跑通下面这个闭环：

```text
创建项目
→ 生成文风资产
→ 生成小说启动文档
→ 编译第1章上下文
→ 生成第1章规划
→ 生成第1章正文
→ 审查第1章
→ 用户确认第1章
→ 更新项目状态
→ 编译第2章上下文
```

只要这个闭环稳定，系统就具备继续扩展的基础。

---

# 21. 总结

Novel Writing Runtime 的核心不是“让大模型多写字”，而是让大模型在一个受控的小说生产系统里持续工作。

系统的根本结构是：

```text
资产层：文风、设定、角色、伏笔、章节、时间线
编译层：把资产编译成本章上下文
生成层：规划章节、生成正文、文风重写
审查层：检查连续性、节奏、爽点、文风
更新层：确认章节后抽取状态并更新资产
```

第一版只要把这个结构跑通，就已经是一个真正可开发、可迭代、可产品化的自动化小说边写工具。
