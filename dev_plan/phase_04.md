# Phase 4: Novel Bible 渐进式生成 + Bible 版本管理

## 前置条件
- Phase 0-3 完成（数据模型、Storage、LLM、文风资产）
- Phase 5 数据模型可先行定义（Subplot, Hook, Strategy）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 4.1 | Bible Storage 层 | Phase 1 | 0.5天 |
| 4.2 | Story Architect Agent — Round 1 (方向变体) | Phase 2 | 2天 |
| 4.3 | Story Architect Agent — Round 2 (角色概念) | 4.2 | 1.5天 |
| 4.4 | Story Architect Agent — Round 3 (完整 Bible) | 4.3 | 2天 |
| 4.5 | Writing Strategy 初始生成 | 4.4 | 0.5天 |
| 4.6 | Subplot Registry 初始生成 | 4.4 | 0.5天 |
| 4.7 | Bible 版本管理 | 4.1 | 1天 |
| 4.8 | Bible Service 编排层 | 4.2-4.7 | 1天 |
| 4.9 | Bible API 端点 | 4.8 | 0.5天 |
| 4.10 | Bible 集成测试 | 4.9 | 1天 |

依赖关系图:
```text
4.1 ──────────────────────────→ 4.8 → 4.9 → 4.10
4.2 → 4.3 → 4.4 → 4.5 ──────→ 4.8
4.2 → 4.3 → 4.4 → 4.6 ──────→ 4.8
4.1 ──────────────→ 4.7 ────→ 4.8
```

---

## Task 4.1: Bible Storage 层

**文件:** `novel_runtime/storage/bible_storage.py`

**依赖:** Phase 1

### Contract: storage.bible_storage.BibleStorage

#### `save_bible_file(project_path: Path, filename: str, content: str) → Path`
- 写入 `bible/{filename}` (md 文件)
- filename 枚举: `novel_bible.md`, `world_setting.md`, `character_profiles.md`, `volume_plan.md`, `chapter_plan.md`

#### `load_bible_file(project_path: Path, filename: str) → str`
- 读取 `bible/{filename}`
- 不存在时抛出 `FileNotFoundError`

#### `save_bible_changelog(project_path: Path, changelog: BibleChangelog) → Path`
- 写入 `bible/bible_changelog.yaml`

#### `load_bible_changelog(project_path: Path) → BibleChangelog`
- 读取 changelog，不存在时返回空列表

#### `add_changelog_entry(project_path: Path, chapter: str, changes: list[str]) → BibleChangelogEntry`
- 追加一条 changelog，版本号自动 +1
- 返回新 entry

#### `list_bible_files(project_path: Path) → list[str]`
- 列举 bible 目录下所有文件名

**验收标准:**
- [ ] Bible 文件读写正确
- [ ] Changelog 版本号自动递增
- [ ] 不存在的文件正确报错

---

## Task 4.2: Story Architect Agent — Round 1 (方向变体)

**文件:**
- `novel_runtime/agents/story_architect.py`
- `prompts/bible_direction_variants.md`

**依赖:** Phase 2

### Agent: StoryArchitectAgent

**继承:** BaseAgent

#### `generate_direction_variants(idea: str, genre: str, target_reader: str, core_selling_point: str) → list[DirectionVariant]`

**Contract:**

**Input:**
- 创意描述、类型、目标读者、核心卖点

**Output:**
- `DirectionVariant`: `variant_id: int`, `name: str`, `core_selling_point: str`, `pacing_style: str`, `character_type: str`, `world_setting: str`, `summary: str`
- 生成 3 个方向变体，从不同角度切入同一创意

**Behavior:**
1. 加载 Prompt 模板 `bible_direction_variants`
2. 渲染变量: `{idea}`, `{genre}`, `{target_reader}`, `{core_selling_point}`
3. 调用 LLM
4. 解析输出为 3 个 DirectionVariant
5. 校验每个变体包含必需字段

**Validator:** YAMLValidator，必需字段: variants (list), 每个变体含 name, core_selling_point, pacing_style, character_type, world_setting, summary

### Prompt Design: bible_direction_variants.md

**Input Specification:**
- `{{idea}}`: 用户创意描述
- `{{genre}}`: 小说类型
- `{{target_reader}}`: 目标读者
- `{{core_selling_point}}`: 核心卖点

**Output Specification:**
- YAML 格式，包含 `variants` 列表（3 个变体）
- 每个变体包含: name, core_selling_point, pacing_style, character_type, world_setting, summary

**Key Instructions:**
1. 三个变体必须从不同角度切入: 一个偏爽文节奏、一个偏剧情推进、一个偏人物成长
2. 每个变体的核心卖点必须有明显区别
3. 节奏风格要明确（快餐/慢热/渐强等）
4. 主角类型要不同（天才型/努力型/逆袭型等）
5. 世界观设定要有差异

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 只生成1-2个变体 | variants 少于3个 | 提示"请生成恰好3个方向变体" |
| 变体之间太相似 | 差异不明显 | 提示"三个变体必须有明显的风格/节奏/卖点差异" |
| 缺少必需字段 | 校验失败 | 提示缺少的具体字段 |

**Test Inputs:**
- Case 1: 都市修仙创意 → 3个变体包含不同节奏和卖点
- Case 2: 悬疑推理创意 → 变体偏重不同解谜方式

**验收标准:**
- [ ] 生成3个方向变体
- [ ] 每个变体包含所有必需字段
- [ ] 变体之间有显著差异

---

## Task 4.3: Story Architect Agent — Round 2 (角色概念)

**文件:** `prompts/bible_character_concepts.md`

**依赖:** Task 4.2

### Agent: StoryArchitectAgent 新增方法

#### `generate_character_concepts(selected_direction: DirectionVariant, idea: str) → CharacterConceptResult`

**Contract:**

**Input:**
- 选定的方向变体 + 原始创意

**Output:**
- `CharacterConceptResult`: `protagonist: CharacterConcept`, `key_characters: list[CharacterConcept]`, `voice_assets: list[CharacterVoice]`
- `CharacterConcept`: `name`, `role`, `personality`, `motivation`, `arc_direction`, `key_traits`
- 为主角和3-5个关键角色生成概念 + Character Voice Asset 初稿

**Behavior:**
1. 加载 Prompt 模板 `bible_character_concepts`
2. 渲染变量: `{direction_name}`, `{direction_summary}`, `{idea}`
3. 调用 LLM
4. 解析输出为角色概念列表
5. 为每个角色生成初步的 CharacterVoice

### Prompt Design: bible_character_concepts.md

**Key Instructions:**
1. 主角必须有明确的成长弧线和内在矛盾
2. 关键角色（3-5个）必须有互补或对立的叙事功能
3. 每个角色的说话风格必须有明显区分
4. 角色之间必须有潜在的冲突或合作关系
5. 角色的口头禅和语言习惯要独特

---

## Task 4.4: Story Architect Agent — Round 3 (完整 Bible)

**文件:** `prompts/bible_full_generation.md`

**依赖:** Task 4.3

### Agent: StoryArchitectAgent 新增方法

#### `generate_full_bible(direction: DirectionVariant, characters: list[CharacterConcept], idea: str, genre: str) → BibleGenerationResult`

**Contract:**

**Input:**
- 选定方向、角色概念、原始创意、类型

**Output:**
- `BibleGenerationResult`: 包含 5 个文件内容:
  - `novel_bible: str` — novel_bible.md 内容
  - `world_setting: str` — world_setting.md 内容
  - `character_profiles: str` — character_profiles.md 内容
  - `volume_plan: str` — volume_plan.md 内容
  - `chapter_plan: str` — chapter_plan.md 内容（前10章详细规划）

**Behavior:**
1. 加载 Prompt 模板 `bible_full_generation`
2. 渲染变量: 方向、角色、创意
3. 调用 LLM（可能需要多次调用生成不同文件）
4. 解析输出为 5 个文件内容
5. 校验每个文件包含必需章节

**Validator:** MarkdownValidator，必需章节:
- novel_bible: 核心卖点, 主角设定, 主线目标, 核心冲突, 世界规则
- world_setting: 地理, 势力, 能力体系, 历史背景
- character_profiles: 主角 + 关键角色的详细设定
- volume_plan: 第一卷目标, 前50章路线
- chapter_plan: 前10章的详细规划

### Prompt Design: bible_full_generation.md

**Key Instructions:**
1. novel_bible 必须包含一句话卖点和目标读者定位
2. world_setting 必须与类型匹配（都市/玄幻/修仙等）
3. character_profiles 必须包含每个角色的叙事功能
4. volume_plan 必须有明确的弧线结构
5. chapter_plan 前3章必须详细到场景级别
6. 所有设定必须内部一致（不出现矛盾）
7. 前10章的节奏必须有变化（不能全是同一种节奏）

---

## Task 4.5: Writing Strategy 初始生成

**文件:** `novel_runtime/services/bible_service.py` (部分)

**依赖:** Task 4.4

### Contract: services.bible_service.generate_initial_strategy

**Function:**
- `generate_initial_strategy(genre: str, pacing_style: str, novel_bible: str) → WritingStrategy`

**Behavior:**
- 基于 genre 和 pacing_style 生成默认的 WritingStrategy
- 都市爽文: 短节奏、高爽点密度、快节奏
- 慢热型: 长节奏、低爽点密度、渐进式
- 根据方向变体的 pacing_style 参数调整

**Output:**
- 带有合理默认值的 WritingStrategy model

**验收标准:**
- [ ] 不同类型生成不同策略参数
- [ ] 所有字段有合理默认值

---

## Task 4.6: Subplot Registry 初始生成

**文件:** `novel_runtime/services/bible_service.py` (部分)

**依赖:** Task 4.4

### Contract: services.bible_service.generate_initial_subplots

**Function:**
- `generate_initial_subplots(chapter_plan: str, character_profiles: str) → list[Subplot]`

**Behavior:**
- 从 chapter_plan 和 character_profiles 中提取主要子线
- 生成主线 + 2-3 条初始子线
- 设置 interleave_plan 参数

**验收标准:**
- [ ] 生成至少主线 + 2条子线
- [ ] 每条子线有完整的字段

---

## Task 4.7: Bible 版本管理

**文件:** `novel_runtime/storage/bible_storage.py` (已在 Task 4.1)

**扩展:**

### Contract: bible_storage.BibleStorage 新增方法

#### `update_bible_file(project_path: Path, filename: str, content: str, reason: str, chapter: str) → None`
- 更新 Bible 文件
- 自动追加 changelog entry，版本号 +1
- 更新 project.bible_version

#### `get_bible_version(project_path: Path) → int`
- 返回当前 Bible 版本号
- 从 changelog 最后一条读取

#### `get_bible_diff(project_path: Path, from_version: int, to_version: int) → list[BibleChangelogEntry]`
- 返回两个版本之间的变更记录

#### `freeze_bible_version(project_path: Path, version: int) → Path`
- 在 `snapshots/bible_v{version}/` 下保存当前 Bible 所有文件的快照
- 用于回滚

**验收标准:**
- [ ] 版本号自动递增
- [ ] Changelog 正确追加
- [ ] 快照创建完整

---

## Task 4.8: Bible Service 编排层

**文件:** `novel_runtime/services/bible_service.py`

**依赖:** Task 4.1-4.7

### Contract: services.bible_service.BibleService

#### `generate_direction_variants(project_id: str) → list[DirectionVariant]`
- 从项目信息读取创意、类型等
- 调用 Agent 生成方向变体
- 返回变体列表

#### `select_direction(project_id: str, variant_id: int, modifications: str = "") → DirectionVariant`
- 记录用户选择
- 如有 modifications，记录修改
- 返回选定变体

#### `generate_character_concepts(project_id: str, modifications: dict | None = None) → CharacterConceptResult`
- 基于选定方向生成角色概念
- 返回角色 + Voice Assets

#### `confirm_characters(project_id: str, character_adjustments: dict) → None`
- 记录用户对角色的调整

#### `generate_bible(project_id: str) → BibleGenerationResult`
- 调用 Agent 生成完整 Bible
- 保存所有 5 个文件到 bible/ 目录
- 生成初始 Writing Strategy 和 Subplot Registry
- 更新 project.bible_version = 1
- 创建第一版 Bible changelog entry
- 创建 Bible v1 快照

#### `get_bible(project_id: str) → dict[str, str]`
- 返回所有 Bible 文件内容

#### `get_bible_version(project_id: str) → int`
- 返回当前版本号

**验收标准:**
- [ ] 渐进式3轮流程可跑通
- [ ] Bible 文件保存正确
- [ ] 初始 Strategy 和 Subplot 生成正确
- [ ] 版本号自动管理

---

## Task 4.9: Bible API 端点

**文件:** `novel_runtime/api/bible.py`

### API 端点

#### `POST /api/projects/{project_id}/bible/direction`
- Request: `{"idea": "...", "genre": "都市修仙", "target_reader": "...", "core_selling_point": "..."}`
- Response: `{"variants": [...], "task_id": "..."}`

#### `POST /api/projects/{project_id}/bible/select-direction`
- Request: `{"variant_id": 1, "modifications": "希望主角更果断"}`
- Response: `{"selected_direction": {...}}`

#### `POST /api/projects/{project_id}/bible/characters`
- Request: `{"character_adjustments": {...}}`
- Response: `{"characters": [...], "voice_assets": [...]}`

#### `POST /api/projects/{project_id}/bible/generate`
- Response: `{"bible_files": {...}, "bible_version": 1, "task_id": "..."}`

#### `GET /api/projects/{project_id}/bible`
- Response: `{"novel_bible": "...", "world_setting": "...", ...}`

#### `GET /api/projects/{project_id}/bible/version`
- Response: `{"version": 1, "changelog": [...]}`

**验收标准:**
- [ ] 所有端点可通过 HTTP 测试
- [ ] 3轮渐进式流程 API 级别跑通

---

## Task 4.10: Bible 集成测试

**文件:** `tests/integration/test_bible_service.py`, `tests/integration/test_bible_api.py`

**测试范围:**

### Service 层
- test_direction_variants: 生成3个方向变体
- test_character_concepts: 生成角色概念 + Voice
- test_full_bible_generation: 完整3轮流程
- test_bible_versioning: 版本号递增 + changelog

### API 层
- test_api_direction: POST 方向变体 → 返回3个变体
- test_api_generate: POST 生成 → 任务创建
- test_api_version: GET 版本号 → 正确

**验收标准:**
- [ ] 所有集成测试通过
- [ ] 3轮流程端到端跑通（Mock LLM）