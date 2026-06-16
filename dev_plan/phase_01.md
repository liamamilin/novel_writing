# Phase 1: 项目骨架 + Storage 层 + DB 层 + 项目管理

## 前置条件
- Phase 0 完成（数据模型、异常体系、配置管理）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 1.1 | 基础文件读写工具 (Storage Base) | Phase 0 | 1天 |
| 1.2 | 项目目录结构创建器 (Project Layout) | 1.1 | 1天 |
| 1.3 | 项目 Storage 层 | 1.1, 1.2 | 1天 |
| 1.4 | 状态文件 Storage 层 | 1.1 | 1天 |
| 1.5 | 章节 Storage 层 | 1.1 | 1天 |
| 1.6 | SQLite 数据库层 | Phase 0 | 0.5天 |
| 1.7 | 项目管理 Service | 1.3, 1.6 | 1天 |
| 1.8 | 项目管理 API 端点 | 1.7 | 1天 |

依赖关系图:
```text
1.1 → 1.2 → 1.3 → 1.7 → 1.8
1.1 → 1.4 ──────→ 1.7
1.1 → 1.5 ──────→ 1.7
1.6 ─────────────→ 1.7
```

---

## Task 1.1: 基础文件读写工具 (Storage Base)

**文件:**
- `novel_runtime/storage/__init__.py`
- `novel_runtime/storage/base.py`

**依赖:** Phase 0 (models)

### Contract: storage.base.read_yaml

**Input:**
- `file_path: Path` — YAML 文件路径

**Output:**
- `dict` — 解析后的 YAML 内容

**Guarantees:**
- 文件不存在时抛出 `FileNotFoundError`
- YAML 解析失败时抛出 `ValueError` 并包含文件路径

**Error cases:**
- `FileNotFoundError` → 文件不存在
- `ValueError` → YAML 格式错误

### Contract: storage.base.write_yaml

**Input:**
- `file_path: Path`
- `data: dict`
- `overwrite: bool = False`

**Output:**
- `Path` — 写入的文件路径

**Guarantees:**
- 父目录不存在时自动创建
- `overwrite=False` 且文件已存在时抛出 `FileExistsError`
- YAML 写入使用 ruamel.yaml 保持可读格式（块样式，中文不转义）

**Error cases:**
- `FileExistsError` → overwrite=False 且文件存在
- `PermissionError` → 目录不可写

### Contract: storage.base.read_md

**Input:**
- `file_path: Path`

**Output:**
- `str` — Markdown 文件内容

**Guarantees:**
- 文件不存在时抛出 `FileNotFoundError`

### Contract: storage.base.write_md

**Input:**
- `file_path: Path`
- `content: str`
- `overwrite: bool = False`

**Output:**
- `Path`

**Guarantees:**
- 父目录不存在时自动创建
- `overwrite=False` 且文件已存在时抛出 `FileExistsError`

### Contract: storage.base.read_yaml_model

**Input:**
- `file_path: Path`
- `model_class: Type[BaseModel]` — Pydantic 模型类

**Output:**
- `BaseModel` 实例 — 反序列化后的 Pydantic 对象

**Guarantees:**
- YAML 内容与模型字段不匹配时抛出 `ValueError` 并列出缺失/多余字段

### Contract: storage.base.write_yaml_model

**Input:**
- `file_path: Path`
- `model: BaseModel`
- `overwrite: bool = False`

**Output:**
- `Path`

**Guarantees:**
- Pydantic 模型先 `.model_dump()` 再写入 YAML

### Contract: storage.base.list_files

**Input:**
- `directory: Path`
- `pattern: str = "*.yaml"` — glob 模式

**Output:**
- `list[Path]`

**Guarantees:**
- 目录不存在时返回空列表（不抛异常）
- 结果按文件名字排序

### Contract: storage.base.delete_file

**Input:**
- `file_path: Path`

**Output:**
- `bool` — 是否成功删除

**Guarantees:**
- 文件不存在时返回 False（不抛异常）

**验收标准:**
- [ ] YAML 读写正确处理中文（不转义）
- [ ] Markdown 读写保持原格式
- [ ] 父目录自动创建
- [ ] overwrite 控制正确
- [ ] Pydantic 模型序列化/反序列化往返一致

**测试用例:**
- test_yaml_roundtrip: dict → 写入 → 读取 → 比较
- test_yaml_model_roundtrip: Pydantic model → 写入 → 读取 → 比较
- test_md_roundtrip: str → 写入 → 读取 → 比较
- test_overwrite_false: 写入两次 overwrite=False → 第二次抛 FileExistsError
- test_overwrite_true: 写入两次 overwrite=True → 第二次成功
- test_chinese_yaml: 中文内容 → 写入 → 读取 → 保留中文
- test_auto_mkdir: 深层路径 → 写入成功

---

## Task 1.2: 项目目录结构创建器 (Project Layout)

**文件:**
- `novel_runtime/storage/project_layout.py`

**依赖:** Task 1.1

### Contract: storage.project_layout.create_project_layout

**Input:**
- `project_path: Path` — 项目根目录路径

**Output:**
- `dict[str, Path]` — 创建的目录和文件路径映射

**Guarantees:**
- 创建完整的项目目录结构:
  ```
  {project_path}/
    project.yaml
    style_assets/          (空目录)
    source_texts/          (空目录)
    bible/                 (空目录)
    strategies/            (空目录)
    chapters/              (空目录)
    subplots/
      subplot_registry.yaml (初始空注册表)
    states/
      story_state.yaml     (初始空状态)
      characters.yaml      (初始空列表)
      hooks.yaml           (初始空列表)
    snapshots/             (空目录)
    prompts/               (空目录)
  ```
- `project.yaml` 包含初始项目元信息（project_id, name, genre, status=draft, bible_version=0）
- `states/story_state.yaml` 包含初始全局状态结构
- `states/characters.yaml` 包含空 `characters: []`
- `states/hooks.yaml` 包含空 `hooks: []`
- `subplots/subplot_registry.yaml` 包含空 `subplots: []`
- 已存在的目录/文件不报错（幂等）

**Error cases:**
- 路径不可写 → `PermissionError`

### Contract: storage.project_layout.validate_project_layout

**Input:**
- `project_path: Path`

**Output:**
- `bool` — 目录结构是否完整合法

**Guarantees:**
- 检查所有必需目录和文件存在
- `project.yaml` 可解析为 Project model

**Error cases:**
- 目录不完整 → 返回 False
- project.yaml 格式错误 → 返回 False

**验收标准:**
- [ ] 创建项目目录后所有必要目录和文件存在
- [ ] 初始状态文件格式正确
- [ ] 幂等：对已存在目录再次调用不报错
- [ ] 验证函数正确检测合法/非法目录

**测试用例:**
- test_create_layout: 创建目录 → 检查所有路径存在
- test_create_layout_idempotent: 创建两次 → 不报错，文件内容不变
- test_validate_valid: 创建后验证 → True
- test_validate_missing_dir: 删除 subdir → 验证 → False
- test_initial_state_files: story_state.yaml 可解析为模型

---

## Task 1.3: 项目 Storage 层

**文件:**
- `novel_runtime/storage/project_storage.py`

**依赖:** Task 1.1, 1.2

### Contract: storage.project_storage.ProjectStorage

**方法清单:**

#### `load_project(project_path: Path) → Project`
- 读取 `project.yaml` 并反序列化为 Project model
- 文件不存在时抛出 `ProjectNotFoundError`

#### `save_project(project_path: Path, project: Project) → Path`
- 将 Project model 序列化并写入 `project.yaml`
- overwrite=True（项目更新时总是覆盖）
- 同时更新 `updated_at`

#### `create_chapter_dir(project_path: Path, chapter_number: int) → Path`
- 创建 `chapters/chapter_NNN/` 目录
- 在目录中创建空文件：`context_pack.md`, `chapter_plan.md`, `draft.md`, `styled_draft.md`, `final.md`, `state_annotations.yaml`, `review_continuity.md`, `review_quality.md`, `review_cross_chapter.md`, `review_reader_sim.md`, `fix_instructions.yaml`
- 返回章节目录路径

#### `load_chapter(project_path: Path, chapter_number: int) → Chapter`
- 读取 `chapters/chapter_NNN/chapter.yaml` 并反序列化为 Chapter model
- 章节不存在时抛出 `ChapterNotFoundError`

#### `save_chapter(project_path: Path, chapter: Chapter) → Path`
- 将 Chapter model 写入 `chapters/chapter_NNN/chapter.yaml`

#### `update_chapter_status(project_path: Path, chapter_number: int, new_status: str) → Chapter`
- 状态流转规则:
  - `planned` → `drafted`
  - `drafted` → `reviewed`
  - `reviewed` → `approved`
  - `approved` → `locked`
  - 其他转换抛出 `InvalidStateTransitionError`
- 更新 `updated_at`

#### `list_chapters(project_path: Path) → list[Chapter]`
- 扫描 `chapters/` 目录，列出所有章节
- 按章节号排序

**验收标准:**
- [ ] 项目读写正确
- [ ] 章节目录创建包含所有必要文件
- [ ] 章节状态流转遵循规则
- [ ] 列出章节按编号排序

**测试用例:**
- test_project_roundtrip: Project → 保存 → 读取 → 比较
- test_create_chapter_dir: 创建章节目录 → 所有文件存在
- test_chapter_roundtrip: Chapter → 保存 → 读取 → 比较
- test_status_transition_planned_to_drafted: planned → drafted → 成功
- test_status_transition_invalid: planned → approved → InvalidStateTransitionError
- test_list_chapters: 创建3章 → 列出 → 3个结果，按序排列

---

## Task 1.4: 状态文件 Storage 层

**文件:**
- `novel_runtime/storage/state_storage.py`

**依赖:** Task 1.1

### Contract: storage.state_storage.StateStorage

**方法清单:**

#### `load_story_state(project_path: Path) → dict`
- 读取 `states/story_state.yaml`
- 返回全局状态字典

#### `save_story_state(project_path: Path, state: dict) → Path`
- 写入全局状态

#### `load_characters(project_path: Path) → list[CharacterState]`
- 读取 `states/characters.yaml`
- 返回角色状态列表

#### `save_characters(project_path: Path, characters: list[CharacterState]) → Path`
- 写入角色状态列表

#### `get_character_by_id(project_path: Path, character_id: str) → CharacterState | None`
- 按角色 ID 查找

#### `get_characters_by_chapter(project_path: Path, chapter_id: str) → list[CharacterState]`
- 找出 `last_seen_chapter` 在指定章节附近的角色（当前章节 ± 2 章）

#### `load_hooks(project_path: Path) → list[Hook]`
- 读取 `states/hooks.yaml`

#### `save_hooks(project_path: Path, hooks: list[Hook]) → Path`
- 写入伏笔列表

#### `get_open_hooks(project_path: Path) → list[Hook]`
- 筛选 status=open 的伏笔

#### `get_urgent_hooks(project_path: Path, chapter_number: int) → list[Hook]`
- 筛选需要在本章关注的高优先级或紧迫度 rising/critical 的伏笔

#### `load_subplots(project_path: Path) → list[Subplot]`
- 读取 `subplots/subplot_registry.yaml` + 各子线文件

#### `save_subplots(project_path: Path, subplots: list[Subplot]) → Path`
- 写入子线注册表 + 各子线文件

#### `load_timeline(project_path: Path) → list[TimelineEvent]`
- 从 `states/story_state.yaml` 中读取时间线部分

#### `save_timeline(project_path: Path, events: list[TimelineEvent]) → Path`
- 写入时间线到全局状态文件

**验收标准:**
- [ ] 状态文件读写正确
- [ ] 角色按 ID 和章节筛选正确
- [ ] 伏笔按状态和紧迫度筛选正确
- [ ] 子线文件读写正确（注册表 + 各子线文件）

**测试用例:**
- test_story_state_roundtrip: dict → 写入 → 读取 → 比较
- test_characters_roundtrip: list → 写入 → 读取 → 比较
- test_get_character_by_id: 写入3个角色 → 按 ID 查找 → 正确
- test_hooks_filter: 写入5个伏笔（3 open, 1 resolved, 1 abandoned）→ get_open_hooks → 3个
- test_urgent_hooks: 写入不同紧迫度伏笔 → 按 chapter_number 筛选 → 正确

---

## Task 1.5: 章节 Storage 层

**文件:**
- `novel_runtime/storage/chapter_storage.py`

**依赖:** Task 1.1

### Contract: storage.chapter_storage.ChapterStorage

**方法清单:**

#### `save_chapter_file(project_path: Path, chapter_number: int, file_type: str, content: str) → Path`
- `file_type` 枚举: `context_pack`, `plan`, `draft`, `styled_draft`, `final`, `state_annotations`, `review_continuity`, `review_quality`, `review_cross_chapter`, `review_reader_sim`, `fix_instructions`
- 根据文件类型确定扩展名 (.md 或 .yaml)
- 如果章节目录不存在，先创建

#### `load_chapter_file(project_path: Path, chapter_number: int, file_type: str) → str`
- 读取章节文件内容
- 文件不存在时抛出 `FileNotFoundError`

#### `chapter_file_exists(project_path: Path, chapter_number: int, file_type: str) → bool`
- 检查章节文件是否存在

#### `freeze_chapter(project_path: Path, chapter_number: int) → None`
- 将章节目录下所有文件设为只读（chmod 444）
- 已批准章节调用此方法

#### `unfreeze_chapter(project_path: Path, chapter_number: int) → None`
- 恢复章节目录读写权限（用于回滚场景）

**验收标准:**
- [ ] 各类型章节文件读写正确
- [ ] 文件类型到扩展名映射正确
- [ ] freeze 后文件不可写
- [ ] unfreeze 后文件可写

**测试用例:**
- test_save_load_draft: 写入 draft → 读取 → 内容一致
- test_save_load_yaml: 写入 state_annotations → 读取 → 内容一致
- test_file_exists: 写入后检查 → True，未写入检查 → False
- test_freeze: freeze 后 → 写入操作抛出 PermissionError
- test_unfreeze: unfreeze 后 → 写入操作成功

---

## Task 1.6: SQLite 数据库层

**文件:**
- `novel_runtime/db/__init__.py`
- `novel_runtime/db/database.py`
- `novel_runtime/db/project_repo.py`
- `novel_runtime/db/task_repo.py`

**依赖:** Phase 0 (models, config)

### Contract: db.database.Database

**Input:** `db_path: str` (SQLite 文件路径)

**Guarantees:**
- 初始化时创建 `projects` 和 `tasks` 表（如果不存在）
- 提供连接池管理
- 支持 async 上下文管理器

**方法:**

#### `init_db() → None`
- 创建表: projects（字段见 overview 的 Schema）和 tasks
- 表已存在时不报错（幂等）

#### `get_connection() → Connection`
- 返回数据库连接

### Contract: db.project_repo.ProjectRepo

**方法清单:**

#### `create(project: Project) → Project`
- 插入项目记录

#### `get_by_id(project_id: str) → Project | None`
- 按项目 ID 查询

#### `list_projects(status: str | None = None) → list[Project]`
- 列出所有项目，可按状态筛选

#### `update(project: Project) → Project`
- 更新项目记录，自动更新 `updated_at`

#### `delete(project_id: str) → bool`
- 删除项目记录

### Contract: db.task_repo.TaskRepo

**方法清单:**

#### `create(task: Task) → Task`
- 创建任务记录

#### `get_by_id(task_id: str) → Task | None`

#### `list_by_project(project_id: str, status: TaskStatus | None = None) → list[Task]`
- 按项目 ID 列出任务，可按状态筛选

#### `update_status(task_id: str, status: TaskStatus, output_data: dict | None = None, error: str | None = None) → Task`
- 更新任务状态和结果

**验收标准:**
- [ ] 数据库初始化创建正确表结构
- [ ] Project CRUD 正确
- [ ] Task CRUD 正确
- [ ] 列表查询支持状态筛选

**测试用例:**
- test_create_and_get_project: 创建项目 → 按 ID 查询 → 字段一致
- test_list_projects_with_filter: 创建3个项目(不同状态) → 按状态筛选 → 2个
- test_task_lifecycle: 创建任务 → pending → running → success → 状态正确
- test_task_with_error: 创建任务 → pending → running → failed → error 字段有值

---

## Task 1.7: 项目管理 Service

**文件:**
- `novel_runtime/services/__init__.py`
- `novel_runtime/services/project_service.py`

**依赖:** Task 1.3, 1.4, 1.5, 1.6

### Contract: services.project_service.ProjectService

**方法清单:**

#### `create_project(name: str, genre: str, idea: str, target_reader: str = "", core_selling_point: str = "", target_style: str = "") → Project`
- 生成 project_id
- 创建 Project model
- 创建项目目录结构
- 保存 project.yaml
- 插入 SQLite 记录
- 返回 Project

**Guarantees:**
- 项目 ID 唯一（基于时间戳 + 随机）
- 目录结构完整

**Error cases:**
- 项目名已存在 → `ValueError`

#### `get_project(project_id: str) → Project`
- 从 SQLite 查询项目
- 项目不存在时抛出 `ProjectNotFoundError`

#### `list_projects(status: str | None = None) → list[Project]`

#### `update_project(project_id: str, **updates) → Project`
- 更新项目字段
- 自动更新 `updated_at`
- 同步到文件和数据库

#### `create_chapter(project_id: str, chapter_number: int) → Chapter`
- 创建章节目录和文件
- 创建 Chapter model
- 保存到文件

#### `get_chapter(project_id: str, chapter_number: int) → Chapter`
- 读取章节信息

#### `advance_chapter_status(project_id: str, chapter_number: int) → Chapter`
- 推进章节状态到下一个合法状态

#### `get_project_path(project_id: str) → Path`
- 返回项目文件系统路径

**验收标准:**
- [ ] 创建项目后目录结构完整
- [ ] SQLite 和文件系统同步
- [ ] 章节创建包含所有必要文件

**测试用例:**
- test_create_project: 创建项目 → 目录存在 + 数据库有记录
- test_get_project: 创建后查询 → 字段正确
- test_create_chapter: 创建章节 → 目录和文件存在
- test_advance_chapter: planned → drafted → reviewed → 成功

---

## Task 1.8: 项目管理 API 端点

**文件:**
- `novel_runtime/api/__init__.py`
- `novel_runtime/api/projects.py`

**依赖:** Task 1.7

### API 端点

#### `POST /api/projects`
- Request body: `ProjectCreate` model
- Response: `{"project_id": "...", "status": "draft"}`
- 调用 `ProjectService.create_project`
- 创建项目目录结构

#### `GET /api/projects/{project_id}`
- Response: Project model
- 调用 `ProjectService.get_project`

#### `GET /api/projects`
- Query params: `status: str | None`
- Response: `list[Project]`

#### `PUT /api/projects/{project_id}`
- Request body: `ProjectUpdate` model
- Response: 更新后的 Project model

**验收标准:**
- [ ] 所有端点可通过 HTTP 测试
- [ ] 错误情况返回正确状态码
- [ ] 创建项目后 GET 可查到

**测试用例:**
- test_api_create_project: POST → 201 + project_id
- test_api_get_project: GET → Project
- test_api_list_projects: GET → list
- test_api_update_project: PUT → 更新后字段
- test_api_project_not_found: GET 不存在的 ID → 404