# Novel Writing Runtime — 生产部署指南

## 架构总览

```
                 ┌──────────────┐
                 │  Nginx (SSL) │
                 │  :443        │
                 └──────┬───────┘
                        │
              ┌─────────┴──────────┐
              │                    │
     ┌────────▼────────┐  ┌───────▼────────┐
     │  Backend        │  │  Frontend       │
     │  uvicorn :8000  │  │  nginx :80      │
     │  FastAPI        │  │  SPA            │
     └────────┬────────┘  └────────────────┘
              │
     ┌────────▼────────┐
     │  SQLite         │
     │  nwr.db         │
     └─────────────────┘
```

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | >= 3.10 |
| Node.js | >= 20 (仅构建前端) |
| 磁盘 | > 1GB（取决于生成章节数） |

## 配置

所有配置通过环境变量或 `.env` 文件设置：

### 必需

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM API Key | `sk-...` |
| `NWR_LLM_BASE_URL` | LLM 端点 URL | `https://api.openai.com/v1` |
| `NWR_LLM_MODEL` | LLM 模型名 | `gpt-4` / `deepseek-v4-flash` |

### 可选

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NWR_STORAGE_BASE_PATH` | `./novel_projects` | 项目文件存储目录 |
| `NWR_DB_PATH` | `{storage}/nwr.db` | SQLite 数据库路径 |
| `NWR_LOG_LEVEL` | `INFO` | 日志级别 |
| `NWR_LOG_FORMAT` | `text` | 日志格式 (`text` / `json`) |
| `NWR_LOG_FILE` | (空) | 日志文件路径 (空=stderr) |
| `NWR_AUTH_TOKEN` | (空) | Bearer token (空=禁用) |
| `NWR_LLM_CACHE_ENABLED` | `false` | LLM 响应缓存 |
| `NWR_LLM_CACHE_TTL` | `86400` | 缓存 TTL（秒） |
| `NWR_LLM_MAX_RETRIES` | `1` | 失败最大重试次数 |
| `NWR_LLM_TEMPERATURE` | `0.7` | 生成温度 |
| `NWR_LLM_MAX_TOKENS` | `4096` | 最大输出 token |
| `NWR_RATE_LIMIT` | `60/minute` | 全局限流 |
| `NWR_LLM_RATE_LIMIT` | `10/minute` | LLM 调用限流 |

## 部署方式

### 方式 1: Docker Compose（推荐）

```bash
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY 和其他配置
docker compose up -d
```

服务启动：
- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 监控指标：`http://localhost:8000/metrics`

### 方式 2: 直接运行

```bash
# 1. 后端
pip install -e ".[dev]"
uvicorn novel_runtime.main:app --host 0.0.0.0 --port 8000 --workers 1

# 2. 前端（开发模式）
cd frontend
npm install
npm run dev     # 开发，代理 /api -> :8000

# 3. 前端（生产构建）
cd frontend
npm run build
# 用任意静态服务器提供 dist/ 目录
```

### 方式 3: systemd 服务

```ini
# /etc/systemd/system/novel-runtime.service
[Unit]
Description=Novel Writing Runtime
After=network.target

[Service]
Type=simple
User=novel
WorkingDirectory=/opt/novel-runtime
EnvironmentFile=/opt/novel-runtime/.env
ExecStart=/opt/novel-runtime/.venv/bin/uvicorn novel_runtime.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 监控

### Prometheus 指标

端点：`/metrics`（默认不公开在 API 文档中）

5 个自定义指标：

| 指标名 | 类型 | Label | 说明 |
|--------|------|-------|------|
| `nwr_llm_calls_total` | Counter | `agent`, `status` | LLM 调用次数 |
| `nwr_llm_tokens_total` | Counter | `agent`, `type` | 消耗 token 数 |
| `nwr_llm_latency_seconds` | Histogram | `agent` | LLM 调用延迟 |
| `nwr_task_duration_seconds` | Histogram | `task_type` | 任务执行时间 |
| `nwr_chapter_status_count` | Gauge | `project`, `status` | 章节状态分布 |

### Prometheus 配置

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'novel-runtime'
    scrape_interval: 30s
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboard

```bash
# 导入 grafana/dashboards/nwr-overview.json
```

4 个面板：
1. LLM Calls/min — 调用速率
2. LLM Latency — p50/p95 延迟
3. Token Usage — token 消耗速率
4. Chapter Status — 章节状态统计

### 告警规则

参见 `grafana/alerts.yaml`，规则：

| 告警名 | 条件 | 严重度 |
|--------|------|--------|
| LLMHighErrorRate | 5min 错误率 > 10% | warning |
| LLMHighLatency | p95 延迟 > 60s | warning |
| TaskBacklog | 10min 内 > 10 任务 | info |
| NoLLMThroughput | 5min 无调用 | info |

## 日志

```bash
# JSON 格式
export NWR_LOG_FORMAT=json

# 日志文件
export NWR_LOG_FILE=/var/log/novel-runtime.log

# Loki 采集（JSON 格式）
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 备份

数据分两部分：

```bash
# 1. SQLite 数据库
cp -r /path/to/novel_projects/nwr.db /backup/

# 2. 项目文件
cp -r /path/to/novel_projects /backup/

# 推荐：定时任务
0 3 * * * tar czf /backup/novel-$(date +\%Y\%m\%d).tar.gz /path/to/novel_projects
```

## 扩容与限制

| 场景 | 方案 |
|------|------|
| 单用户并发写 | SQLite WAL 模式已启用 |
| 多项目同时 LLM 调用 | 当前单 worker 顺序，多 worker 需外部队列 |
| 存储 > 10GB | 迁移到 PostgreSQL + 对象存储 |

## 升级

```bash
git pull
docker compose build
docker compose up -d
# SQLite 数据自动兼容（查看 CHANGELOG）
```

## 故障排查

### LLM 调用失败

```bash
curl -s http://localhost:8000/health | jq .checks.llm
# 查看 latency 和 status_code
```

### 数据库损坏

```bash
sqlite3 nwr.db "PRAGMA integrity_check;"
# 如损坏：从备份恢复
```

### 磁盘空间

```bash
du -sh novel_projects/
du -sh novel_projects/nwr.db
```

## 安全

1. 设置 `NWR_AUTH_TOKEN` 启用 Bearer 认证
2. 前端 Nginx 配置 HTTPS（Let's Encrypt）
3. 定期轮换 `LLM_API_KEY`
4. `/health` 和 `/metrics` 自动豁免认证
