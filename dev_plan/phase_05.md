# Phase 5: Subplot Registry + Hook 增强 + Writing Strategy

## 前置条件
- Phase 0 完成（数据模型已定义）
- Phase 1 完成（Storage 层可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 5.1 | Subplot Storage 层 | Phase 0, 1 | 0.5天 |
| 5.2 | Hook Storage 层 (增强版) | Phase 0, 1 | 0.5天 |
| 5.3 | Strategy Storage 层 | Phase 0, 1 | 0.5天 |
| 5.4 | Subplot Service + API | 5.1 | 1天 |
| 5.5 | Hook Service + API (增强版) | 5.2 | 1天 |
| 5.6 | Strategy Service + API | 5.3 | 0.5天 |
| 5.7 | Hook 紧迫度自动递增逻辑 | 5.2, 5.5 | 0.5天 |
| 5.8 | 集成测试 | 5.4-5.7 | 0.5天 |

依赖关系图:
```text
5.1 → 5.4
5.2 → 5.5 → 5.7
5.3 → 5.6
5.4 + 5.5 + 5.6 + 5.7 → 5.8
```

---

## Task 5.1: Subplot Storage 层

**文件:** `novel_runtime/storage/subplot_storage.py`

**依赖:** Phase 0, 1

### Contract: storage.subplot_storage.SubplotStorage

#### `save_subplot(project_path: Path, subplot: Subplot) → Path`
- 保存到 `subplots/{subplot_id}.yaml`
- 同时更新 `subplots/subplot_registry.yaml` 中的注册条目

#### `load_subplot(project_path: Path, subplot_id: str) → Subplot`
- 从 `subplots/{subplot_id}.yaml` 加载

#### `list_subplots(project_path: Path, status: SubplotStatus | None = None) → list[Subplot]`
- 列举所有子线，可按状态筛选
- 读取 registry 后加载各子线文件

#### `update_subplot(project_path: Path, subplot_id: str, updates: dict) → Subplot`
- 部分更新子线字段
- 更新 `last_advanced` 和相关时间戳

#### `delete_subplot(project_path: Path, subplot_id: str) → bool`
- 删除子线文件并从 registry 移除

#### `get_active_subplots(project_path: Path) → list[Subplot]`
- 返回 status 不是 resolved/abandoned 的子线

#### `get_subplots_by_chapter_range(project_path: Path, chapter_from: int, chapter_to: int) → list[Subplot]`
- 返回 `next_suggested_chapter` 在指定范围内的子线

**验收标准:**
- [ ] 子线 CRUD 正确
- [ ] Registry 和子线文件同步
- [ ] 状态筛选正确

---

## Task 5.2: Hook Storage 层 (增强版)

**文件:** `novel_runtime/storage/state_storage.py` (扩展)

**依赖:** Phase 0, 1

### Contract: state_storage.StateStorage 新增方法

#### `add_hook(project_path: Path, hook: Hook) → Hook`
- 添加伏笔，自动生成 hook_id（格式 `H_NNN`）

#### `update_hook(project_path: Path, hook_id: str, updates: dict) → Hook`
- 部分更新伏笔字段

#### `get_hooks_by_status(project_path: Path, status: str) → list[Hook]`
- 按状态筛选

#### `get_hooks_by_type(project_path: Path, hook_type: HookType) → list[Hook]`
- 按类型筛选

#### `get_urgent_hooks(project_path: Path, current_chapter: int) → list[Hook]`
- 筛选 `urgency in [rising, critical]` 或 `reader_patience 即将耗尽` 的伏笔

#### `get_overdue_hooks(project_path: Path, current_chapter: int) → list[Hook]`
- 筛选 `source_chapter + reader_patience < current_chapter` 的伏笔

#### `get_hooks_for_chapter(project_path: Path, chapter_number: int) → dict`
- 返回: `{"can_trigger": [...], "must_not_forget": [...], "should_resolve": [...]}`
- can_trigger: open 状态 + 当前章节在 planned_payoff_range 内
- must_not_forget: open + priority=high 或 urgency=critical
- should_resolve: overdue hooks

**验收标准:**
- [ ] Hook CRUD 正确
- [ ] 按状态/类型/紧迫度筛选正确
- [ ] get_hooks_for_chapter 分类正确

---

## Task 5.3: Strategy Storage 层

**文件:** `novel_runtime/storage/strategy_storage.py`

**依赖:** Phase 0, 1

### Contract: storage.strategy_storage.StrategyStorage

#### `save_strategy(project_path: Path, strategy: WritingStrategy) → Path`
- 保存到 `strategies/writing_strategy.yaml`

#### `load_strategy(project_path: Path) → WritingStrategy`
- 加载写作策略
- 不存在时返回默认策略

#### `get_default_strategy() → WritingStrategy`
- 返回默认写作策略（都市快节奏爽文风格）

**验收标准:**
- [ ] 策略读写正确
- [ ] 不存在时返回默认值

---

## Task 5.4: Subplot Service + API

**文件:** `novel_runtime/services/subplot_service.py`, `novel_runtime/api/subplots.py`

### Contract: services.subplot_service.SubplotService

#### `create_subplot(project_id: str, name: str, type: SubplotType, involved_characters: list[str]) → Subplot`
- 创建子线

#### `update_subplot(project_id: str, subplot_id: str, updates: dict) → Subplot`
- 更新子线

#### `advance_subplot(project_id: str, subplot_id: str, advancement: str, chapter_id: str) → Subplot`
- 推进子线：更新 status, last_advanced, chapters_since_advance

#### `suggest_subplot_allocation(project_id: str, chapter_number: int) → dict`
- 基于Writing Strategy的subplot_policy建议本章应推进哪些子线
- 考虑: max_simultaneous, min_advance_frequency
- 返回: `{"should_advance": [...], "should_idle": [...], "at_risk": [...]}`

#### `list_subplots(project_id: str, status: SubplotStatus | None = None) → list[Subplot]`

### API 端点

#### `GET /api/projects/{project_id}/subplots`
#### `POST /api/projects/{project_id}/subplots`
#### `PUT /api/projects/{project_id}/subplots/{subplot_id}`
#### `GET /api/projects/{project_id}/chapters/{chapter_number}/subplot-suggestions`

**验收标准:**
- [ ] 子线 CRUD 正确
- [ ] 子线分配建议合理
- [ ] API 端点可用

---

## Task 5.5: Hook Service + API (增强版)

**文件:** `novel_runtime/services/hook_service.py`, `novel_runtime/api/hooks.py`

### Contract: services.hook_service.HookService

#### `add_hook(project_id: str, content: str, source_chapter: str, type: HookType, priority: str = "medium", reader_patience: int = 8, related_characters: list[str] | None = None) → Hook`

#### `update_hook(project_id: str, hook_id: str, updates: dict) → Hook`

#### `trigger_hook(project_id: str, hook_id: str, chapter: str) → Hook`
- 将 hook 状态从 open 改为 triggered

#### `resolve_hook(project_id: str, hook_id: str, resolution: str, chapter: str) → Hook`
- 将 hook 状态改为 resolved，设置 actual_payoff_chapter

#### `get_chapter_hooks(project_id: str, chapter_number: int) → dict`
- 调用 StateStorage.get_hooks_for_chapter

#### `list_hooks(project_id: str, status: str | None = None, type: HookType | None = None, priority: str | None = None) → list[Hook]`

### API 端点

#### `GET /api/projects/{project_id}/hooks`
- Query params: status, type, priority
#### `POST /api/projects/{project_id}/hooks`
#### `PUT /api/projects/{project_id}/hooks/{hook_id}`
#### `GET /api/projects/{project_id}/chapters/{chapter_number}/hooks`

**验收标准:**
- [ ] Hook CRUD 正确
- [ ] 状态流转正确 (open → triggered → resolved)
- [ ] 筛选正确

---

## Task 5.6: Strategy Service + API

**文件:** `novel_runtime/services/strategy_service.py`

### Contract: services.strategy_service.StrategyService

#### `get_strategy(project_id: str) → WritingStrategy`

#### `update_strategy(project_id: str, updates: dict) → WritingStrategy`

#### `reset_strategy(project_id: str) → WritingStrategy`
- 重置为默认策略

(API 端点可直接用 GET/PUT /api/projects/{project_id}/strategy)

**验收标准:**
- [ ] 策略读写正确
- [ ] 默认策略合理

---

## Task 5.7: Hook 紧迫度自动递增逻辑

**文件:** `novel_runtime/services/hook_service.py` (扩展)

### Contract: HookService.escalate_urgency

#### `escalate_urgency(project_id: str, current_chapter: int) → list[Hook]`
- 遍历所有 open 和 triggered 的 hook
- 对每个 hook: `urgency_increase_rate` 累加到紧迫度分数
- 如果 `source_chapter + reader_patience <= current_chapter`，将 urgency 设为 critical
- 如果 `source_chapter + reader_patience * 0.7 <= current_chapter`，将 urgency 设为 rising
- 返回所有被更新的 hook

**Behavior:**
- 每次状态更新时自动调用
- 紧迫度递增基于 writing_strategy.hook_policy.urgency_escalation

**验收标准:**
- [ ] 紧迫度随章节正确递增
- [ ] 到达临界值时自动升级

**测试用例:**
- test_urgency_stable: 新伏笔（2章前埋下）→ urgency 不变
- test_urgency_rising: 伏笔埋下6章前，patience=8 → urgency 变为 rising
- test_urgency_critical: 伏笔埋下8章前，patience=8 → urgency 变为 critical
- test_urgency_escalation_disabled: writing_strategy.hook_policy.urgency_escalation=False → 不递增

---

## Task 5.8: 集成测试

**文件:** `tests/integration/test_subplot_service.py`, `tests/integration/test_hook_service.py`

**测试范围:**
- test_subplot_crud: 创建、更新、推进、查询子线
- test_subplot_allocation_suggestion: 基于策略建议子线分配
- test_hook_crud: 创建、更新、触发、回收伏笔
- test_hook_urgency_escalation: 紧迫度递增
- test_hook_chapter_filter: 获取章节相关伏笔
- test_strategy_crud: 读写写作策略

**验收标准:**
- [ ] 所有集成测试通过