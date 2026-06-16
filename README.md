# Novel Writing Runtime

自动化网络小说写作系统 — 基于 LLM Agent 的 AI 辅助创作平台。

## 功能

- **项目管理**：创建小说项目，管理文风、Bible、角色状态
- **文风分析**：上传样本 → AI 提取文风特征 → 生成写作风格资产
- **自动写作**：Context + Plan → Draft → Review → Approve 完整流水线
- **版本管理**：草稿版本树，差异对比，版本回滚
- **多读者审稿**：5 画像评分（爽点/文笔/节奏/逻辑/代入感）
- **导出**：TXT / Markdown / EPUB / DOCX
- **活动追踪**：项目事件时间线 + 分享链接
- **SSE 流式生成**：前端实时渲染生成过程
- **57 个 REST API 端点**

## 快速开始

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env: 填入 LLM_API_KEY / NWR_LLM_BASE_URL / NWR_LLM_MODEL
```

### 2. 后端

```bash
pip install -e ".[dev]"
uvicorn novel_runtime.main:app --reload
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000`。

### 4. Docker

```bash
docker compose up -d
# 后端 :8000, 前端 :3000
```

## 测试

```bash
pytest tests/ -q                          # 122 passed
pytest tests/unit/ -q                     # 单元测试
pytest tests/integration/ -q              # 集成测试 (Mock LLM)
pytest tests/e2e/ -q                      # 端到端 (需 LLM_API_KEY)
cd frontend && npm run build              # 前端构建 (0 error)
```

## 系统架构

```
资产层 → 编译层 → 生成层 → 审查层 → 更新层
```

### 10 个 Agent

| Agent | 层 | 职责 |
|-------|----|------|
| Style Analyst | 资产层 | 提取文风特征 |
| Story Architect | 资产层 | 生成 Bible 全套文档 |
| Context Compiler | 编译层 | 叙事推理 + 诊断 |
| Chapter Planner | 生成层 | 章节规划 + 节奏分配 |
| Chapter Writer | 生成层 | 正文生成 + 状态标注 |
| Narrative Polisher | 生成层 | 文风润色 |
| Continuity Auditor | 审查层 | 事实一致性 |
| Quality Auditor | 审查层 | 可读性评分 |
| Cross-Chapter Auditor | 审查层 | 跨章诊断 |
| Reader Simulator | 审查层 | 读者视角模拟 |

### 57 API 端点

| 模块 | 端点 | 功能 |
|------|------|------|
| Projects | `+4` | CRUD + 心跳 |
| Styles | `+4` | 上传样本 / 分析 / CRUD |
| Bible | `+7` | 生成 / 更新 / 方向选择 |
| Context | `+2` | 编译上下文 / 叙事诊断 |
| Chapters | `+18` | 规划 / 草稿 / 审查 / 定稿 / SSE 流式 / 版本树 / 多读者 |
| State | `+5` | 状态更新 / 回滚 / snapshot |
| Export | `+3` | 导出任务 / 下载 |
| Subplots | `+4` | 子线 CRUD |
| Hooks | `+3` | 伏笔管理 |
| Strategy | `+2` | 写作策略 |
| Events | `+1` | 活动时间线 |
| Shared | `+3` | 分享链接只读访问 |

## 技术栈

- **后端**：Python 3.10 / FastAPI / Pydantic v2 / SQLite / YAML + Markdown
- **前端**：React 19 / TypeScript / Vite / Tailwind / Zustand / React Query
- **LLM**：OpenAI Compatible Provider（支持任意兼容 API）
- **监控**：Prometheus (5 自定义指标) + Grafana dashboard
- **部署**：Docker Compose (Nginx + uvicorn)

## 文档

- [生产部署指南](docs/DEPLOY.md)
- [开发计划](DEVELOPMENT_PLAN.md)
- [Agent 配置](AGENTS.md)

## 许可证

MIT
