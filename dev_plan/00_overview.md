# Novel Writing Runtime - 详细开发计划总览

## 1. 项目代码目录结构

```text
novel_runtime/                     # Python 包根目录
  __init__.py
  main.py                          # FastAPI app 入口 + lifespan
  config.py                        # Settings (pydantic-settings)

  models/                          # 全部 Pydantic 数据模型
    __init__.py
    project.py                     # Project, ProjectCreate, ProjectUpdate
    chapter.py                     # Chapter, ChapterPlan, Scene, AgentContract
    task.py                        # Task, TaskType, TaskStatus
    style.py                       # StyleAsset, StyleAssetCreate, ConditionalRule
    character.py                   # CharacterState, NarrativeRole, CharacterVoice
    hook.py                        # Hook, HookType, HookUrgency
    subplot.py                     # Subplot, SubplotArc, ConvergencePoint
    timeline.py                    # TimelineEvent, StoryTime
    strategy.py                    # WritingStrategy, PacingStrategy, HookPolicy, etc.
    state_annotations.py           # StateAnnotation, SummaryAnnotation
    fix_instructions.py            # FixInstruction
    health_report.py               # StateHealthReport, HealthIssue
    context.py                     # RawContext, ContextPack
    bible.py                       # BibleChangelog, BibleUpdateProposal, BibleUpdateItem

  storage/                         # 文件系统读写层
    __init__.py
    base.py                        # 基础文件读写工具 (read_yaml, write_yaml, read_md, write_md)
    project_storage.py             # 项目文件 CRUD
    state_storage.py               # 状态文件读写 (story_state, characters, hooks)
    chapter_storage.py             # 章节文件读写
    bible_storage.py               # Bible 文件读写
    style_storage.py               # 文风文件读写
    subplot_storage.py             # 子线文件读写
    strategy_storage.py            # 策略文件读写
    snapshot_storage.py            # Snapshot 读写 + 回滚

  db/                              # SQLite 层
    __init__.py
    database.py                   # 连接初始化 + 表创建
    project_repo.py                # 项目元信息 CRUD
    task_repo.py                   # 任务状态 CRUD

  llm/                             # LLM 调用层
    __init__.py
    provider.py                    # LLMProvider 基类 + 工厂方法
    openai_provider.py             # OpenAI Compatible 实现
    prompt_loader.py               # Prompt 模板加载 + 变量渲染
    token_counter.py               # Token 预算计算 + 截断

  agents/                          # 全部 LLM Agent
    __init__.py
    base.py                        # BaseAgent: validate + retry 逻辑
    style_analyst.py               # Style Analyst Agent
    story_architect.py             # Story Architect Agent (3-round)
    context_compiler.py            # Context Compiler Agent
    chapter_planner.py            # Chapter Planner Agent
    chapter_writer.py              # Chapter Writer Agent
    narrative_polisher.py          # Narrative Polisher Agent
    continuity_auditor.py          # Continuity Auditor Agent
    quality_auditor.py             # Quality Auditor Agent
    cross_chapter_auditor.py       # Cross-Chapter Auditor Agent
    reader_simulator.py            # Reader Simulator Agent
    state_updater.py               # State Updater Agent

  compiler/                        # 确定性编译逻辑 (非 Agent)
    __init__.py
    context_assembler.py           # Context Assembler
    state_health_checker.py        # State Health Checker
    fix_instruction_merger.py      # 审查报告 → 修复指令合并
    state_diff.py                  # draft.md vs final.md diff 检测

  services/                         # 业务逻辑编排层
    __init__.py
    project_service.py             # 项目管理编排
    style_service.py               # 文风分析编排
    bible_service.py               # Bible 生成分步编排
    context_service.py             # 上下文编译编排 (Assembler + Compiler)
    chapter_service.py             # 章节生命周期编排
    review_service.py              # 审查编排 + 修复指令生成
    state_service.py               # 状态更新编排
    subplot_service.py             # 子线管理
    hook_service.py                # 伏笔管理 + 紧迫度递增
    strategy_service.py            # 写作策略管理

  api/                              # FastAPI 路由
    __init__.py
    projects.py                    # POST/GET/PUT /api/projects
    styles.py                      # POST /api/projects/{id}/style-samples, /styles/analyze
    bible.py                       # POST /api/projects/{id}/bible/direction, /characters, /generate
    context.py                     # POST /api/projects/{id}/chapters/{ch}/context/compile
    chapters.py                    # POST /plan, /draft, /polish, /review, /fix, /approve
    state.py                       # POST /state/update, /state/rollback
    subplots.py                    # GET/POST/PUT /api/projects/{id}/subplots
    hooks.py                       # GET/POST/PUT /api/projects/{id}/hooks
    health.py                      # GET /api/projects/{id}/health

  cli/                              # CLI 命令
    __init__.py
    main.py                        # Typer 入口
    commands/
      __init__.py
      init.py                      # novel init
      style.py                     # novel style analyze
      bible.py                     # novel bible generate
      context.py                   # novel context compile
      chapter.py                   # novel chapter plan/draft/polish/review/fix/approve
      state.py                     # novel state update/rollback
      subplot.py                   # novel subplot list
      hook.py                      # novel hook list
      health.py                    # novel health check
      suggest.py                   # novel next suggest

prompts/                            # Prompt 模板 (Markdown)
  style_analysis.md
  adversarial_test.md
  bible_direction_variants.md
  bible_character_concepts.md
  bible_full_generation.md
  context_compile.md
  chapter_plan.md
  chapter_write.md
  narrative_polish.md
  continuity_review.md
  quality_review.md
  cross_chapter_review.md
  reader_simulation.md
  state_update.md
  bible_update.md

tests/                              # 测试套件
  __init__.py
  conftest.py                      # 共享 fixtures
  unit/                            # Layer 1: 不需要 LLM
    test_models/
    test_storage/
    test_compiler/
    test_validators/
  integration/                     # Layer 2: Mock LLM
    test_agents/
    test_services/
    test_api/
  e2e/                             # Layer 3: 真实 LLM
    test_full_pipeline.py
    test_five_chapters.py
  fixtures/                        # 固定测试数据
    sample_style_text.txt
    sample_bible_input.json
    sample_context_pack.md
    sample_chapter_plan.md
```

---

## 2. 模块依赖图

```text
models  ←── 所有模块依赖
  ↓
storage ←── db
  ↓
llm ←── agents ←── services ←── api / cli
  ↓                ↓
compiler ←── services
```

依赖规则：
- `models` 不依赖任何其他内部模块，只依赖 `pydantic`
- `storage` 依赖 `models`，不依赖 `llm` 或 `agents`
- `compiler` 依赖 `models` 和 `storage`，不依赖 `llm` 或 `agents`
- `llm` 依赖 `models`，不依赖 `storage` 或 `agents`
- `agents` 依赖 `models`、`llm`、`storage`
- `services` 依赖 `models`、`storage`、`llm`、`agents`、`compiler`
- `api` 和 `cli` 只依赖 `services`，不直接调用 `agents` 或 `storage`
- 禁止循环依赖

---

## 3. SQLite Schema

```sql
-- 项目元信息
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    genre TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft/active/paused/archived
    default_style_id TEXT DEFAULT '',
    current_volume_id TEXT DEFAULT 'volume_001',
    current_chapter_id TEXT DEFAULT 'chapter_001',
    bible_version INTEGER DEFAULT 0,
    writing_strategy_id TEXT DEFAULT 'strategy_default',
    storage_path TEXT NOT NULL,              -- 文件系统路径
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 任务状态
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/running/success/failed/cancelled
    input_data TEXT NOT NULL,                 -- JSON
    output_data TEXT DEFAULT '{}',            -- JSON
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- 任务索引
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type ON tasks(task_type);
```

---

## 4. 测试分层策略

### Layer 1: 单元测试（不需要 LLM）

测试范围：
- 数据模型序列化/反序列化
- Storage 层读写操作
- Context Assembler 筛选逻辑
- State Health Checker 规则检测
- Token 预算截断逻辑
- Fix Instruction Merger 逻辑
- State Diff 检测逻辑
- Prompt 模板渲染
- 输出校验框架

框架: pytest + pytest-cov
运行: `pytest tests/unit/`
目标: 覆盖率 > 80%

### Layer 2: 集成测试（Mock LLM）

测试范围：
- Agent 接收 Mock LLM 输出后的处理流程
- 输出校验框架 + 重试逻辑
- Service 层编排流程
- API 端点请求/响应
- 完整章节生成流程（每步 Mock）

框架: pytest + unittest.mock
Mock 策略: 替换 `llm.provider.generate()` 返回预定义输出
运行: `pytest tests/integration/`

### Layer 3: E2E 测试（真实 LLM）

测试范围：
- 完整闭环流程
- 连续5章生成验证
- 量化验收标准

框架: pytest + 真实 LLM 调用
运行条件: 需要配置 LLM API Key
运行: `pytest tests/e2e/ -m e2e`
注意: 使用 temperature=0 提高可复现性（但 LLM 输出仍可能不完全一致）

---

## 5. 共用模式

### 5.1 错误处理

```python
# 自定义异常层次
class NovelRuntimeError(Exception): pass
class ProjectNotFoundError(NovelRuntimeError): pass
class ChapterNotFoundError(NovelRuntimeError): pass
class StyleNotSetError(NovelRuntimeError): pass
class InvalidStateTransitionError(NovelRuntimeError): pass
class LLMOutputValidationError(NovelRuntimeError): pass
class LLMCallError(NovelRuntimeError): pass
class TokenBudgetExceededError(NovelRuntimeError): pass
class SnapshotNotFoundError(NovelRuntimeError): pass

# API 错误响应格式
# HTTP 404: {"detail": "Project novel_20260616_001 not found"}
# HTTP 400: {"detail": "Style not set. Run style analysis first."}
# HTTP 409: {"detail": "Chapter chapter_023 already approved, cannot modify"}
# HTTP 500: {"detail": "LLM call failed after retry", "task_id": "task_xxx"}
```

### 5.2 日志

```python
# 使用 Python logging
# 格式: %(asctime)s - %(name)s - %(levelname)s - %(message)s
# 日志级别:
#   DEBUG: 详细数据流（文件读取内容、LLM 请求/响应）
#   INFO:  关键流程节点（Agent 开始/完成、状态更新）
#   WARNING: 可恢复问题（Token 截断、重试）
#   ERROR: 不可恢复问题（LLM 调用失败、文件写入失败）

# 每个 Agent 使用独立 logger
logger = logging.getLogger(f"novel_runtime.agents.{agent_name}")
```

### 5.3 配置管理

```python
# 环境变量 (前缀 NWR_)
NWR_LLM_PROVIDER=openai_compatible
NWR_LLM_BASE_URL=https://api.example.com/v1
NWR_LLM_MODEL=model-name
NWR_LLM_API_KEY_ENV=LLM_API_KEY
NWR_LLM_MAX_RETRIES=1
NWR_CONTEXT_TOKEN_BUDGET=8000
NWR_STORAGE_BASE_PATH=./novel_projects
NWR_LOG_LEVEL=INFO

# 也支持 config.yaml 文件
# 环境变量优先于配置文件
```

### 5.4 任务执行模式

```python
# 短任务（<30秒）: 同步执行，直接返回结果
# 长任务（>=30秒）: 异步执行，返回 task_id，前端轮询
# 判断标准: LLM 调用次数
#   1次 LLM 调用 → 同步
#   多次 LLM 调用 → 异步
# 异步使用 FastAPI BackgroundTasks，不用 Celery 等外部队列
```

---

## 6. 接口契约模板

每个模块/函数的接口契约遵循以下格式：

```markdown
### [模块名].[类/函数名]

**Contract:**
- Input: 参数类型 + 描述
- Output: 返回类型 + 描述
- Guarantees: 执行保证（如: 返回值 token count <= budget）
- Error cases: 异常类型 + 触发条件
- Dependencies: 依赖的其他模块

**Behavior:**
- 核心行为描述
- 边界情况处理

**Examples:**
- 示例输入 → 示例输出
```

---

## 7. Phase 依赖图

```text
Phase 0: 架构基础 + 全部数据模型 + 测试框架
    ↓
Phase 1: 项目骨架 + Storage + DB + 项目管理
    ↓
Phase 2: LLM 调用层 + Prompt + 输出校验
    ↓
┌──────────┬──────────┬──────────┐
│ Phase 3  │ Phase 4  │ Phase 5  │
│ (文风)    │ (Bible)   │ (Subplot) │
└──────────┴──────────┴──────────┘
              ↓ (Phase 4 需要 Phase 5 的数据结构)
    Phase 6: Context Assembler + Token 预算
              ↓
    Phase 7: Context Compiler + State Health Checker
              ↓
    Phase 8: Chapter Planner
              ↓
    Phase 9: Chapter Writer + Narrative Polisher
              ↓
        ┌────────────┐
        ↓            ↓
    Phase 10     Phase 11
    (Continuity  (Cross-Chapter
     + Quality)   + Reader Sim)
        └────────────┘
              ↓
    Phase 12: State Updater + Bible Updater + Snapshot + Rollback
              ↓
    Phase 13: 闭环测试 + 验收
              ↓
    Phase 14: CLI
              ↓
    Phase 15: Web UI
```

Phase 3/4/5 可并行开发，但 Phase 4 (Bible 生成) 依赖 Phase 5 的数据结构定义（Subplot Registry, Writing Strategy, Hook）。
实际执行建议：Phase 5 先于 Phase 4，或至少 Phase 5 的数据模型和 Storage 层先于 Phase 4 的 Agent。

---

## 8. 接口契约文档规范

每个 Phase 文件中，Task 的接口契约格式：

```markdown
### Contract: [模块].[类/函数]

**Input:**
- `param_name`: `type` — 描述

**Output:**
- `return_type` — 描述

**Guarantees:**
- 保证1
- 保证2

**Error cases:**
- `ErrorType` → 触发条件 + 处理

**Dependencies:**
- 依赖的其他 Task 或模块
```

---

## 9. Prompt Design Section 规范

每个包含 Agent 的 Phase，增加 Prompt Design Section：

```markdown
## Prompt Design: [Agent Name]

### Input Specification
- 输入1: 格式描述
- 输入2: 格式描述

### Output Specification
- 输出1: 格式模板（精确到字段和缩进）
- 输出2: 格式模板

### Key Instructions (必须包含的指令)
1. 指令1: 具体要求
2. 指令2: 具体要求

### Failure Modes (常见失败及应对)
| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| ... | ... | ... |

### Test Inputs (固定测试用例)
- Case 1: 输入描述 → 预期输出要点
- Case 2: 输入描述 → 预期输出要点
```

---

## 10. 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 异步支持、自动 API 文档、Pydantic 集成 |
| CLI 框架 | Typer | 类型安全、与 FastAPI 共享模型 |
| 数据模型 | Pydantic v2 | 验证、序列化、类型安全 |
| 序列化格式 | YAML + Markdown | 人类可读、git 友好 |
| 索引/元数据 | SQLite | 轻量、无需额外服务、单文件 |
| LLM 调用 | OpenAI Compatible | 最大兼容性 |
| 异步任务 | FastAPI BackgroundTasks | MVP 不需要 Celery |
| Token 计数 | tiktoken | OpenAI 兼容 |
| 测试框架 | pytest | Python 生态标准 |
| 前端框架 | React + Vite + TypeScript | 高效开发、类型安全 |