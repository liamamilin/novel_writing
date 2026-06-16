# Phase 20 — 多读者模拟

> 目标：支持多读者画像并发审查章节。
> 前置条件：Phase 19 完成。

## 后端

### 读者画像
- `models/reader_persona.py`：Persona 模型（name, age_group, preferences, tolerance_thresholds）
- 内置 5 个画像 YAML 文件 `prompts/reader_personas/persona_*.yaml`
- 5 个内置画像：爽文向、甜宠向、严肃文学向、新读者向、批评家向

### 端点
- `POST /api/projects/{id}/chapters/{n}/review/multi-reader` — 并发执行 N 个画像
  - body: `{persona_ids: [...] | null (all)}`
  - 返回每个画像的评分 + 评论

### 验收标准
- [ ] 5 个画像并发执行
- [ ] 每个画像返回评分和结构化评论
- [ ] 前端雷达图展示
- [ ] 测试通过
