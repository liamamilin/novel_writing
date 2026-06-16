# Phase 0: 架构基础 + 全部数据模型 + 测试框架

## 前置条件
无

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 0.1 | 项目初始化 + 依赖管理 | 无 | 0.5天 |
| 0.2 | 全部数据模型定义 | 0.1 | 2天 |
| 0.3 | 测试框架搭建 | 0.1 | 0.5天 |
| 0.4 | 自定义异常体系 | 0.1 | 0.5天 |
| 0.5 | 配置管理 | 0.1 | 0.5天 |

依赖关系图:
```text
0.1 → 0.2
0.1 → 0.3
0.1 → 0.4
0.1 → 0.5
(0.2, 0.3, 0.4, 0.5 可并行)
```

---

## Task 0.1: 项目初始化 + 依赖管理

**文件:**
- `novel_runtime/__init__.py`
- `novel_runtime/main.py`
- `pyproject.toml`

**依赖:** 无

### Contract: novel_runtime.main

**Input:** 无（FastAPI app lifespan 启动参数）

**Output:**
- `app`: FastAPI 实例，启动后监听端口
- `GET /health` 返回 `{"status": "ok", "version": "0.1.0"}`

**Guarantees:**
- 应用启动时自动创建 `STORAGE_BASE_PATH` 目录
- 应用启动时自动初始化 SQLite 数据库（创建表）
- 应用配置从环境变量读取，有合理默认值

**Error cases:**
- `STORAGE_BASE_PATH` 不可写 → 启动失败，日志输出明确路径问题
- SQLite 数据库文件不可创建 → 启动失败

**Dependencies:** 无

### pyproject.toml 核心依赖

```text
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
pyyaml>=6.0
tiktoken>=0.5.0
httpx>=0.25.0
typer>=0.9.0
rich>=13.0.0
python-slugify>=8.0.0
```

**验收标准:**
- [ ] `uvicorn novel_runtime.main:app` 启动成功
- [ ] `GET /health` 返回 200
- [ ] 指定目录下自动创建 SQLite 数据库文件
- [ ] 配置项可通过环境变量覆盖

**测试用例:**
- test_health_check: `GET /health` → 200 + version
- test_config_from_env: 设置 `NWR_STORAGE_BASE_PATH` → Settings 正确读取
- test_database_init: 启动后 SQLite 文件存在且正确建表

---

## Task 0.2: 全部数据模型定义

**文件:**
- `novel_runtime/models/__init__.py`
- `novel_runtime/models/project.py`
- `novel_runtime/models/chapter.py`
- `novel_runtime/models/task.py`
- `novel_runtime/models/style.py`
- `novel_runtime/models/character.py`
- `novel_runtime/models/hook.py`
- `novel_runtime/models/subplot.py`
- `novel_runtime/models/timeline.py`
- `novel_runtime/models/strategy.py`
- `novel_runtime/models/state_annotations.py`
- `novel_runtime/models/fix_instructions.py`
- `novel_runtime/models/health_report.py`
- `novel_runtime/models/context.py`
- `novel_runtime/models/bible.py`

**依赖:** Task 0.1

### Contract: models.project

**ProjectCreate:**
- Input fields: `project_name: str`, `genre: str`, `idea: str`, `target_reader: str = ""`, `core_selling_point: str = ""`, `target_style: str = ""`
- Validation: `project_name` 非空且长度 1-100, `genre` 非空
- Output: 可序列化为 JSON 的 Pydantic model

**Project:**
- 自动生成 `project_id` 格式 `novel_YYYYMMDD_XXXXX`
- `status: Literal["draft","active","paused","archived"] = "draft"`
- `bible_version: int = 0`
- `writing_strategy_id: str = "strategy_default"`
- timestamps 自动填充

**ProjectUpdate:**
- 所有字段 Optional
- 只有传入字段被更新
- `updated_at` 自动更新

### Contract: models.chapter

**Chapter:**
- `chapter_id` 格式 `chapter_NNN`
- `status: Literal["planned","drafted","reviewed","approved","locked"]`
- 节奏字段: `rhythm_type`, `tension_level: int`, `satisfaction_level: int`, `reader_hook_strength: int`
- 子线推进字段: `subplots_advanced: list[dict]`, `subplots_idle: list[dict]`
- 文件路径字段: `plan_path`, `draft_path`, `styled_draft_path`, `final_path`, 各 review 路径
- `summary: str = ""`

**Scene:**
- `scene_number: int`, `location`, `characters: list[str]`, `scene_function`, `conflict`, `turning_point`, `output`, `target_word_count: int`

**AgentContract:**
- `from_agent: str`, `to_agent: str`, `promises: list[str]`, `constraints: list[str]`

### Contract: models.task

**TaskType:** Enum
- `style_analysis`, `bible_generation`, `bible_direction`, `bible_character`, `context_compile`, `chapter_plan`, `chapter_draft`, `narrative_polish`, `continuity_review`, `quality_review`, `cross_chapter_review`, `reader_simulation`, `fix_and_repolish`, `state_update`, `bible_update`

**TaskStatus:** Enum - `pending`, `running`, `success`, `failed`, `cancelled`

**Task:**
- `task_id` 自动生成
- `input_data: dict = {}`, `output_data: dict = {}`
- timestamps 自动填充

### Contract: models.style

**StyleAssetCreate:**
- `style_name: str`, `sample_ids: list[str]`

**ConditionalRule:**
- `condition: Literal["fight_scene","emotional_scene","dialogue_scene","exposition_scene","climax_scene"]`
- `adjustments: dict[str, str]`

**StyleAsset:**
- `style_id` 自动生成
- 叙述维度: `narration`, `sentence_rhythm`, `dialogue_style`, `description_density`
- 情绪冲突: `emotion_curve`, `conflict_pattern`
- 章节结构: `chapter_opening`, `chapter_ending`
- 场景节奏: `scene_density`
- 禁用表达: `avoid: list[str]`
- 条件文风: `conditional_rules: list[ConditionalRule]`

**CharacterVoice:**
- `voice_id`, `character_id`, `character_name`
- `speech_patterns`: typical_phrases, sentence_length, vocabulary_level, humor_style, emotional_expression
- `internal_monologue`: style, frequency, depth
- `quirks: list[dict]` (context, behavior)

### Contract: models.character

**CharacterState:**
- 事实状态: `character_id`, `name`, `role`, `current_location`, `current_goal`, `current_emotion`, `known_information`, `unknown_information`, `abilities`, `secrets`, `relationships`, `last_seen_chapter`
- 叙事功能子对象 `narrative_role`: `current_function`, `functions: list[str]`, `arc_stage`, `arc_stages_available: list[str]`, `last_significant_moment`, `chapters_since_development: int`, `reader_attachment_level`, `next_use_suggestion`
- `voice_id: str = ""`

### Contract: models.hook

**HookType:** Enum - `mystery`, `tension`, `promise`, `emotional`, `power`

**HookUrgency:** Enum - `stable`, `rising`, `critical`

**Hook:**
- 基本信息: `hook_id`, `content`, `source_chapter`, `status`, `priority`
- 类型维度: `type: HookType`, `reader_patience: int`, `urgency: HookUrgency`, `urgency_increase_rate: float = 0.5`
- 回收策略: `payoff_type`, `planned_payoff_range`, `actual_payoff_chapter`
- 关联: `related_subplots: list[str]`, `related_characters: list[str]`, `foreshadow_density`

### Contract: models.subplot

**SubplotStatus:** Enum - `setup`, `escalating`, `climax`, `resolving`, `resolved`

**SubplotType:** Enum - `main_plot`, `character_arc`, `ongoing_conflict`, `mystery`, `romance`

**ConvergencePoint:** `with_subplot: str`, `planned_chapter_range: str`, `convergence_type: Literal["causal","thematic","character"]`

**Subplot:**
- `subplot_id`, `name`, `type`, `status`
- 弧线信息子对象 `arc`: `setup_chapter`, `current_stage`, `planned_climax_range`, `resolution_chapter`
- `involved_characters: list[str]`, `related_hooks: list[str]`, `last_advanced`, `chapters_since_advance: int`
- 交错计划子对象 `interleave_plan`: `min_gap_between_advances`, `max_gap_between_advances`, `next_suggested_chapter`
- `convergence_points: list[ConvergencePoint]`

### Contract: models.timeline

**StoryTime:** `start: str`, `end: str`, `duration: str`

**TimelineEvent:**
- `event_id`, `chapter_id`, `story_time: StoryTime`, `reading_duration: str`, `pacing_ratio: Literal["fast","normal","slow"]`
- `location`, `characters: list[str]`, `event_summary`, `state_change`

### Contract: models.strategy

**WritingStrategy:**
- `strategy_id`, `name`, `description`
- `chapter_length` 子对象: `target: int = 3000`, `min: int = 2500`, `max: int = 3500`
- `pacing_strategy` 子对象: `type`, `tension_curve`, `cooldown_after_climax: int = 1`
- `subplot_policy` 子对象: `max_simultaneous: int = 3`, `min_advance_frequency: int = 4`, `convergence_strategy`
- `hook_policy` 子对象: `max_open_hooks: int = 8`, `min_resolution_rate: float = 0.3`, `urgency_escalation: bool = True`
- `character_policy` 子对象: `max_scenes_without_protagonist: int = 1`, `character_development_frequency: int = 3`, `new_character_introduction_rate: int = 5`

### Contract: models.state_annotations

**StateAnnotation:**
- `location: str` (如 "scene_2_paragraph_5")
- `type: Literal["character_state_change","new_hook","resolved_hook","subplot_advance","subplot_resolve","character_development","new_world_info","relationship_change","location_change","ability_change"]`
- `character: str = ""`, `change: str`, `trigger: str = ""`, `narrative_impact: str = ""`
- 类型特定字段（hook_id, hook_type, reader_patience, subplot_id, advancement, next_stage, arc_progression 等均为 Optional）

**SummaryAnnotation:**
- `type: Literal["resolved_hook","new_hook","new_world_info","relationship_change","ability_change","location_change"]`
- 类型特定字段均为 Optional

**StateAnnotationsFile:**
- `chapter_id: str`, `annotations: list[StateAnnotation]`, `summary_annotations: list[SummaryAnnotation]`

### Contract: models.fix_instructions

**FixAction:** Enum - `replace`, `insert`, `delete`, `rewrite`

**FixInstruction:**
- `fix_id: str`, `type: str`, `severity: Literal["critical","moderate","low"]`
- `location: str`, `problem: str`, `action: FixAction`
- `original_text: str`, `suggested_fix: str`, `constraint: str = ""`

**FixInstructionsFile:**
- `fix_instructions: list[FixInstruction]`

### Contract: models.health_report

**HealthIssueSeverity:** Enum - `critical`, `warning`, `info`

**HealthIssue:**
- `type: str`, `severity: HealthIssueSeverity`, `description: str`, `suggestion: str`
- 类型特定字段均为 Optional: `character_id`, `hook_id`, `subplot_id`

**StateHealthReport:**
- `report_id` 自动生成, `chapter_id: str`, `generated_at: datetime`
- `issues: list[HealthIssue]`

### Contract: models.context

**RawContext:**
- `project_id: str`, `chapter_id: str`
- 各部分内容字符串: `style_and_voices_content`, `story_context_content`, `recent_chapters_content`, `current_state_content`, `character_state_content`, `hooks_content`, `subplots_content`, `chapter_goal_content`, `writing_strategy_content`, `health_report_content`
- Token 统计: `total_tokens: int`, `budget_used: dict[str, int]`

**ContextPack:**
- `project_id: str`, `chapter_id: str`, `content: str` (完整 Markdown)

### Contract: models.bible

**BibleUpdateItem:**
- `file: Literal["novel_bible.md","world_setting.md","character_profiles.md","volume_plan.md","chapter_plan.md"]`
- `section: str`, `change: str`, `reason: str = ""`

**BibleUpdateProposal:**
- `proposal_id` 自动生成, `project_id: str`, `trigger_chapter: str`
- `items: list[BibleUpdateItem]`, `status: Literal["pending","approved","rejected"] = "pending"`

**BibleChangelogEntry:**
- `version: int`, `chapter: str`, `changes: list[str]`, `timestamp: datetime`

**BibleChangelog:**
- `entries: list[BibleChangelogEntry]`

---

## Task 0.3: 测试框架搭建

**文件:**
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`
- `tests/fixtures/__init__.py`

**依赖:** Task 0.1

### Contract: tests.conftest

**Fixtures:**
- `tmp_project`: 创建临时项目目录，yield 路径，teardown 时清理
- `mock_llm_provider`: 返回可配置返回内容的 Mock LLM Provider
- `sample_project`: 创建包含完整状态文件的测试项目（至少 3 章历史）
- `db_session`: 创建临时 SQLite 数据库连接，teardown 时删除文件

**Guarantees:**
- 临时资源在测试结束后自动清理
- fixtures 之间互相独立
- `mock_llm_provider` 默认返回空字符串，可配置不同类型输出

**Dependencies:** models (Task 0.2), storage (Phase 1)

**验收标准:**
- [ ] `pytest tests/unit/` 可运行
- [ ] conftest.py 中 fixture 可被引用
- [ ] 临时目录在测试结束后自动清理

**测试用例:**
- test_fixture_tmp_project: 使用 tmp_project fixture → 目录存在且可写
- test_fixture_sample_project: 使用 sample_project fixture → 项目目录结构完整
- test_fixture_mock_llm: 配置 mock 返回值 → 调用返回配置内容

---

## Task 0.4: 自定义异常体系

**文件:**
- `novel_runtime/exceptions.py`

**依赖:** Task 0.1

### Contract: exceptions

**异常层次:**
```
NovelRuntimeError (base)
├── ProjectNotFoundError
├── ChapterNotFoundError
├── StyleNotSetError
├── InvalidStateTransitionError
├── LLMOutputValidationError
├── LLMCallError
├── TokenBudgetExceededError
├── SnapshotNotFoundError
├── BibleVersionConflictError
├── AgentContractViolationError
└── StateHealthCriticalError
```

**Guarantees:**
- 所有异常继承自 `NovelRuntimeError`
- 每个异常有 `message: str` 属性
- API 层自动映射异常为 HTTP 状态码:
  - `ProjectNotFoundError` → 404
  - `ChapterNotFoundError` → 404
  - `StyleNotSetError` → 400
  - `InvalidStateTransitionError` → 409
  - `LLMCallError` → 502
  - `LLMOutputValidationError` → 500
  - `TokenBudgetExceededError` → 400
  - `StateHealthCriticalError` → 500

**Error cases:**
- 未注册的异常类型 → 默认 500 Internal Server Error

**验收标准:**
- [ ] 所有异常可实例化并携带消息
- [ ] FastAPI exception_handler 正确映射状态码
- [ ] 未知异常返回 500

**测试用例:**
- test_exception_hierarchy: 每个异常是 NovelRuntimeError 子类
- test_exception_handler_not_found: 抛出 ProjectNotFoundError → API 返回 404
- test_exception_handler_conflict: 抛出 InvalidStateTransitionError → API 返回 409
- test_exception_handler_unexpected: 抛出 RuntimeError → API 返回 500

---

## Task 0.5: 配置管理

**文件:**
- `novel_runtime/config.py`

**依赖:** Task 0.1

### Contract: config.Settings

**Input:** 环境变量 (前缀 `NWR_`) 或 config.yaml 文件

**Output:** Settings 实例（Pydantic BaseSettings）

**Fields:**
- LLM 配置: `llm_provider`, `llm_base_url`, `llm_model`, `llm_api_key_env`, `llm_max_retries`, `llm_temperature`, `llm_max_tokens`
- 上下文配置: `context_token_budget`, `context_budget_allocation: dict`, `context_priority_order: list[str]`
- 存储配置: `storage_base_path`, `db_path`
- 日志配置: `log_level`
- 业务配置: `max_fix_iterations`, `chapter_status_flow: dict`

**Defaults:**
- `llm_provider = "openai_compatible"`
- `context_token_budget = 8000`
- `storage_base_path = "./novel_projects"`
- `max_fix_iterations = 1`
- `log_level = "INFO"`

**Guarantees:**
- 环境变量优先于默认值
- 未配置的必填项（如 `llm_base_url`）在首次 LLM 调用时才报错，不在启动时校验
- `context_budget_allocation` 有合理默认比例分配
- `context_priority_order` 有合理默认优先级排序

**Error cases:**
- `NWR_LLM_API_KEY` 环境变量指向的 key 不存在 → 首次 LLM 调用时抛出 LLMCallError
- `storage_base_path` 不可写 → Task 0.1 启动时已检查

**验收标准:**
- [ ] 默认值可正常创建 Settings 实例
- [ ] 环境变量可覆盖默认值
- [ ] 配置可序列化为 dict

**测试用例:**
- test_default_settings: 默认 Settings 实例化成功
- test_env_override: 设置 `NWR_LLM_MODEL` → Settings.llm_model 被覆盖
- test_budget_defaults: 默认 budget allocation 各项之和 <= total
- test_priority_order: 默认 priority order 包含所有必要部分