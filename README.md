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
- **63 个 REST API 端点（59 REST + 4 文档）**

## 前置要求

| 组件 | 版本要求 | 用途 |
|------|---------|------|
| Python | >= 3.10 | 后端运行 |
| Node.js | >= 18 | 前端构建 |
| LLM API | OpenAI 兼容端点 | 所有 AI 功能依赖 |

## 快速开始

### 1. 配置 LLM

需要准备一个 OpenAI 兼容的 API 端点。例如 [OpenAI](https://platform.openai.com/api-keys) 或 [DeepSeek](https://platform.deepseek.com/api_keys)：

```bash
cp .env.example .env
# 编辑 .env，填入你的 LLM 密钥和端点
# 示例（OpenAI）:
#   LLM_API_KEY=sk-proj-xxxxx
#   NWR_LLM_BASE_URL=https://api.openai.com/v1
#   NWR_LLM_MODEL=gpt-4o-mini
```

### 2. 启动后端

```bash
pip install -e ".[dev]"
uvicorn novel_runtime.main:app --reload
```

验证配置：
```bash
curl http://localhost:8000/health | python3 -m json.tool
# 输出中 "checks.llm.status" 应为 "ok" 或 "degraded"
# 如果为 degraded，查看 detail 字段排查
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000`。点"+ 新建项目"进入四步向导。

### 4. Docker 一键启动

```bash
docker compose up -d
# 后端 :8000, 前端 :3000
```

## 测试

```bash
pytest tests/ -q                          # 122+ passed（基线 122）
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

### 63 API 端点（59 REST + 4 文档）

| 模块 | 端点数 | 核心功能 |
|------|--------|---------|
| Projects | 5 | CRUD + 删除 |
| Styles | 6 | 分析 / analyze-sync / 样本 / CRUD / 测试段落 |
| Tasks | 1 | 异步任务状态查询 |
| Bible | 7 | 方向选择 / 角色 / 生成 / 更新 / 版本 |
| Context | 1 | 编译上下文 |
| Chapters | 15 | 规划 / 草稿 / SSE 流式 / 润色 / 审查(含reviews) / 多读者 / 定稿 / 版本树 / 内容读写 |
| State | 2 | 回滚 / snapshot |
| Export | 2 | 导出任务 / 下载 |
| Subplots | 5 | 子线 CRUD + 删除 + 建议 |
| Hooks | 6 | 伏笔 CRUD + 触发 / 回收 |
| Strategy | 3 | 读写 + 重置 |
| Events | 1 | 时间线 |
| Share | 1 | 生成分享链接 |
| Shared | 3 | 只读访问（豁免认证） |
| System | 2 | 健康检查（含 LLM 延迟探测）/ 监控指标 |

## 技术栈

- **后端**：Python 3.10 / FastAPI / Pydantic v2 / SQLite / YAML + Markdown
- **前端**：React 19 / TypeScript / Vite / Tailwind / Zustand / React Query
- **LLM**：OpenAI Compatible Provider（支持任意兼容 API）
- **监控**：Prometheus (5 自定义指标) + Grafana dashboard + 告警规则
- **部署**：Docker Compose (Nginx + uvicorn)

## 文档

- [生产部署指南](docs/DEPLOY.md) — Docker / systemd / 监控 / 备份 / 安全
- [开发计划](DEVELOPMENT_PLAN.md) — 完整架构规范
- [Agent 配置](AGENTS.md) — CLI / 测试 / 坑点

## 许可证

MIT
