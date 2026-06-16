# Phase 12: State Updater + Bible Updater + Snapshot + 回滚

## 前置条件
- Phase 9 完成（Draft + State Annotations 可用）
- Phase 10-11 完成（Reviews 可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 12.1 | State Diff 检测器 | Phase 1 | 0.5天 |
| 12.2 | Snapshot Manager | Phase 1 | 1天 |
| 12.3 | State Updater Agent + Prompt | Phase 2, 9 | 2天 |
| 12.4 | Bible Updater Agent + Prompt | Phase 2, 4 | 1.5天 |
| 12.5 | State Service 编排层 | 12.1-12.4 | 1.5天 |
| 12.6 | Approve + State Update 原子操作 | 12.5 | 1天 |
| 12.7 | Rollback 机制 | 12.2 | 0.5天 |
| 12.8 | State API 端点 | 12.6 | 0.5天 |
| 12.9 | 集成测试 | 12.8 | 1天 |

依赖关系图:
```text
Phase 1 → 12.1 → 12.5 → 12.6 → 12.8 → 12.9
Phase 1 → 12.2 → 12.5
Phase 1 → 12.2 → 12.7
Phase 2+9 → 12.3 → 12.5
Phase 2+4 → 12.4 → 12.5
```

---

## Task 12.1: State Diff 检测器

**文件:** `novel_runtime/compiler/state_diff.py`

### Contract: compiler.state_diff.StateDiffer

#### `diff(draft_path: Path, final_path: Path) → StateDiff`

**Input:**
- draft_path: Chapter Writer 产出的草稿路径
- final_path: 用户确认后的最终正文路径

**Output:**
- `StateDiff`: `has_changes: bool`, `change_segments: list[dict]`, `summary: str`

**Behavior:**
1. 读取 draft.md 和 final.md
2. 计算 diff（行级别）
3. 提取变更段落:
   - `location`: 段落位置（场景号+段落号）
   - `type`: "added", "removed", "modified"
   - `content`: 变更内容
4. 生成摘要: "用户修改了 X 处，删除了 Y 处，添加了 Z 处"

**Guarantees:**
- 如果 draft.md 不存在（用户从头写），返回 has_changes=True，标记全部为用户内容
- 如果 final.md == draft.md，返回 has_changes=False

**验收标准:**
- [ ] 修改检测正确
- [ ] 删除检测正确
- [ ] 添加检测正确
- [ ] 无修改时返回 False

---

## Task 12.2: Snapshot Manager

**文件:** `novel_runtime/storage/snapshot_storage.py`

### Contract: storage.snapshot_storage.SnapshotManager

#### `create_snapshot(project_path: Path, chapter_number: int) → Path`

**Behavior:**
1. 读取当前所有状态文件: story_state.yaml, characters.yaml, hooks.yaml, subplot_registry.yaml 及各子线文件
2. 创建 `snapshots/state_after_chapter_{NNN}.yaml`
3. 将所有状态打包为一个 YAML 文件
4. 返回快照路径

**Guarantees:**
- 快照包含完整状态（可完整恢复）
- 快照文件名包含章节号

#### `restore_snapshot(project_path: Path, chapter_number: int) → None`

**Behavior:**
1. 读取 `snapshots/state_after_chapter_{NNN}.yaml`
2. 用快照内容覆盖当前所有状态文件
3. 更新 project.yaml 的 current_chapter_id

**Error cases:**
- 快照不存在 → `SnapshotNotFoundError`

#### `list_snapshots(project_path: Path) → list[int]`
- 返回所有可用的快照章节号列表

#### `delete_snapshot(project_path: Path, chapter_number: int) → bool`
- 删除指定快照

**验收标准:**
- [ ] 创建快照后状态完整保存
- [ ] 恢复快照后状态与创建时一致
- [ ] 列表和删除正确

---

## Task 12.3: State Updater Agent + Prompt

**文件:**
- `novel_runtime/agents/state_updater.py`
- `prompts/state_update.md`

### Agent: StateUpdaterAgent

#### `update(final_text: str, annotations: StateAnnotationsFile, diff: StateDiff, characters: list[CharacterState], story_state: dict, hooks: list[Hook], subplots: list[Subplot]) → StateUpdateResult`

**Contract:**

**Input:**
- final_text: 用户确认后的最终正文
- annotations: Chapter Writer 产出的状态标注
- diff: draft vs final 的差异
- characters: 当前角色状态列表
- story_state: 当前全局状态
- hooks: 当前伏笔列表
- subplots: 当前子线列表

**Output:**
- `StateUpdateResult`: 包含:
  - `summary: str` — 章节摘要
  - `character_updates: list[dict]` — 角色状态更新
  - `relationship_updates: list[dict]` — 关系变化
  - `timeline_update: dict` — 时间线更新
  - `new_hooks: list[dict]` — 新增伏笔
  - `triggered_hooks: list[str]` — 触发的伏笔 ID
  - `resolved_hooks: list[dict]` — 回收的伏笔
  - `world_updates: list[str]` — 世界观新增
  - `subplot_advances: list[dict]` — 子线推进
  - `ability_changes: list[dict]` — 能力变化
  - `next_chapter_suggestions: list[str]` — 下一章建议
  - `bible_update_needed: bool` — 是否需要 Bible 更新
  - `bible_update_reasons: list[str]` — Bible 更新原因

**Behavior:**
1. 加载 Prompt 模板 `state_update`
2. 渲染变量: `{final_text}`, `{annotations}`, `{diff_summary}`, `{current_state}`
3. 调用 LLM
4. 解析输出为结构化 YAML
5. 校验输出包含必需字段
6. 返回结果

**关键逻辑:**
- 优先采用 state_annotations 中的标注
- diff 中标记的用户修改优先级高于 AI 标注
- 对标注之外的状态变化，LLM 推理补充

### Prompt Design: state_update.md

**Key Instructions:**
1. 以 state_annotations 为锚点，确认每个标注是否与最终文本一致
2. 对于 diff 中标记的用户修改，优先采纳用户意图
3. 对于没有标注但发生了的状态变化（如用户在最终文本中添加了内容），推理补充
4. 严格区分"角色知道了"和"读者知道了"——角色不知道的信息不能出现在角色的 known_information 中
5. 伏笔状态只允许三种变更: open→triggered, open→resolved, 新增 open
6. 子线推进必须指定具体 advancement 内容
7. next_chapter_suggestions 必须基于当前状态给出，至少3个建议
8. bible_update_needed 只在有重大设定变化时为 true

---

## Task 12.4: Bible Updater Agent + Prompt

**文件:**
- `novel_runtime/services/bible_update_service.py` (部分确定性逻辑 + Agent)
- `prompts/bible_update.md`

### Agent: BibleUpdater

#### `detect_update_need(state_update_result: StateUpdateResult, current_bible: dict[str, str]) → BibleUpdateProposal`

**Contract:**

**Input:**
- state_update_result: State Updater 的输出
- current_bible: 当前 Bible 文件内容

**Output:**
- `BibleUpdateProposal`: 包含一个或多个 BibleUpdateItem

**Behavior:**
1. 检查 state_update_result 中的 world_updates
2. 检查是否有新角色出现（characters 列表中有新 ID）
3. 检查是否有重大设定变化
4. 如需要更新，生成 BibleUpdateProposal
5. 如不需要，返回空 proposal

### Prompt Design: bible_update.md

**Key Instructions:**
1. 只在确实需要更新 Bible 时生成提案
2. 明确指出哪个文件的哪个部分需要更新
3. 给出具体的更新内容
4. 给出更新原因（来自哪个章节的哪个变化）
5. 不要做不必要的更新——小的信息变化应该进 state 而不是 Bible

---

## Task 12.5: State Service 编排层

**文件:** `novel_runtime/services/state_service.py`

### Contract: services.state_service.StateService

#### `update_state(project_id: str, chapter_number: int) → StateUpdateResult`

**Behavior:**
1. 读取 final.md
2. 读取 state_annotations.yaml
3. 读取 draft.md（用于 diff）
4. 计算 draft vs final diff (StateDiffer)
5. 读取当前 characters.yaml, story_state.yaml, hooks.yaml, subplots
6. 调用 StateUpdaterAgent.update()
7. 根据更新结果写入各个状态文件
8. 调用 StateHealthChecker.check()
9. 调用 SnapshotManager.create_snapshot()
10. 检查是否需要 Bible 更新 → 生成 BibleUpdateProposal
11. 生成 next_chapter_suggestions.yaml
12. 返回完整更新结果

**Error cases:**
- 章节未 approved → `InvalidStateTransitionError`
- final.md 不存在 → `FileNotFoundError`

#### `rollback_state(project_id: str, target_chapter: int) → None`

**Behavior:**
1. 调用 SnapshotManager.restore_snapshot(target_chapter)
2. 更新 project.yaml 的 current_chapter_id

**验收标准:**
- [ ] 状态更新流程完整
- [ ] 快照创建正确
- [ ] Bible 更新检测正确
- [ ] 回滚功能正确

---

## Task 12.6: Approve + State Update 原子操作

**文件:** `novel_runtime/services/chapter_service.py` (扩展), `novel_runtime/services/state_service.py`

### Contract: 原子操作

#### `approve_and_update(project_id: str, chapter_number: int, final_text: str) → ApproveResult`

**Behavior:**
1. 保存 final.md
2. 冻结章节目录（设为只读）
3. 更新章节状态为 approved
4. 调用 StateService.update_state()
5. 如果状态更新失败:
   a. 解冻章节目录
   b. 恢复章节状态为 reviewed
   c. 删除已保存的 final.md
   d. 抛出错误

**Guarantees:**
- 步骤2-4是原子操作：要么全部成功，要么全部回滚
- 状态更新失败不污染全局状态

**验收标准:**
- [ ] 成功时状态正确更新
- [ ] 失败时状态完全回滚
- [ ] 冻结后文件不可写

---

## Task 12.7: Rollback 机制

**文件:** `novel_runtime/storage/snapshot_storage.py` (已在 Task 12.2)

**Contract:**
- 已在 Task 12.2 定义
- `restore_snapshot` 已实现
- 补充: 回滚后需要更新 project.yaml 的 current_chapter_id

**验收标准:**
- [ ] 回滚后状态与快照时一致
- [ ] project.yaml 更新正确

---

## Task 12.8: State API 端点

**文件:** `novel_runtime/api/state.py`, `novel_runtime/api/chapters.py` (扩展)

### API 端点

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/approve`
- Request: `{"final_text": "..."}`
- Response: `{"chapter_id": "...", "status": "approved", "frozen": true}`
- 触发 StateService.update_state()

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/state/update`
- Response: `{"snapshot_path": "...", "updated_files": [...], "health_issues": 2, "next_suggestions_path": "..."}`
- 可单独调用（如手动触发）

#### `POST /api/projects/{project_id}/state/rollback`
- Request: `{"target_chapter": 22}`
- Response: `{"restored_to_chapter": 22}`

#### `GET /api/projects/{project_id}/bible/update-proposal`
- Response: `{"proposal": {...}}` 或 `{"proposal": null}`

#### `POST /api/projects/{project_id}/bible/update`
- Request: `{"updates": [...]}`
- Response: `{"bible_version": 3, "updated_files": [...]}`

**验收标准:**
- [ ] Approve + State Update 原子操作
- [ ] 回滚操作正确
- [ ] Bible 更新流程正确

---

## Task 12.9: 集成测试

**测试范围:**
- test_state_diff: 检测 draft vs final 差异
- test_snapshot_create_restore: 创建快照 → 恢复 → 状态一致
- test_state_update_full: 完整状态更新流程
- test_bible_update_detection: 检测 Bible 更新需求
- test_bible_version_increment: Bible 版本号递增
- test_approve_rollback: approve 失败 → 状态回滚
- test_rollback_state: 回滚到之前章节
- test_state_api: HTTP 测试
- test_bible_update_api: Bible 更新 API 测试

**验收标准:**
- [ ] 所有集成测试通过
- [ ] 状态更新流程完整
- [ ] 原子操作正确
- [ ] 回滚正确恢复状态
