# Phase 19 — 导出

> 目标：将已审批章节导出为 txt / epub / docx / markdown。
> 前置条件：Phase 18 完成。

## 后端

### 依赖
- `ebooklib>=0.18` (epub)
- `python-docx>=1.1.0` (docx)

### 端点
- `POST /api/projects/{id}/export` — 异步导出
  - body: `{format: "txt"|"epub"|"docx"|"md", chapter_range: [1, N] | null, include_title: bool}`
  - 返回 `{task_id}`
- `GET /api/projects/{id}/exports/{task_id}/download` — 下载文件

### 验收标准
- [ ] txt 导出：纯文本合并
- [ ] epub 导出：带封面 + 目录
- [ ] docx 导出：带章节标题
- [ ] markdown 导出：保留原格式
- [ ] 测试通过
