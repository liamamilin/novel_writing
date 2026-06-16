# Phase 18 — 版本树 / 多 draft 比较

> 目标：每章支持多个 draft 版本，可切换、比较、晋升。
> 前置条件：Phase 17 完成。

## 后端

### Chapter Storage 改造
- `chapter_storage.py`：新增 `list_drafts()`, `save_draft_version()`, `load_draft_version()`
- 目录结构：`chapters/chapter_003/drafts/draft_v1.md`, `draft_v2.md`
- `Chapter` 模型新增 `active_draft_id: int = 0`，`draft_count: int = 0`

### 新增端点
- `GET /api/projects/{id}/chapters/{n}/drafts` — 列出所有 draft 版本
- `POST /api/projects/{id}/chapters/{n}/drafts/{vid}/promote` — 晋升版本为当前

### 验收标准
- [ ] 多次 draft 生成产生 `draft_v1.md`, `draft_v2.md`...
- [ ] 可切换当前激活版本
- [ ] 前端版本下拉列表
- [ ] 双版本 diff 模式
- [ ] 测试通过
