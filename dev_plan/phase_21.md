# Phase 21 — 协作历史

> 目标：项目操作日志 + 只读分享。
> 前置条件：Phase 20 完成。

## 后端

### 事件日志
- `models/event.py`：Event 模型（event_id, project_id, action, actor, timestamp, details）
- `storage/event_storage.py`：`events.jsonl` append-only 文件
- 所有 Service 层操作记录事件（create_project, generate_draft, approve_chapter, etc.）

### 端点
- `GET /api/projects/{id}/events?limit=50&offset=0` — 事件时间线
- `POST /api/projects/{id}/share` — 生成只读分享链接
- `GET /api/shared/{token}` — 只读访问（限 GET 路由）

### 前端
- 右上"活动" Drawer 展示事件流
- 项目设置"生成分享链接"按钮

### 验收标准
- [ ] 每次操作记录 event
- [ ] 事件时间线 API 分页
- [ ] 只读分享链接可访问（限 GET）
- [ ] 测试通过
