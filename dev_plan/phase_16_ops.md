# Phase 16 — 运维（Ops）生产就绪

> 目标：把单机原型打磨成"可部署、可观测、可调试、可扩展"的服务。
> 前置条件：Phase 0–15 + Phase 15 Completion 全部完成（96 测试通过，前端 0 error build）。
> 原则：不修改 agent/service 业务逻辑，只在外围加 middleware/decorator/lifespan hook。

---

## B.1 结构化日志（Logging）

### 现状
整个 codebase 0 处 `logging` 调用，调试全靠 `print` 和异常堆栈。

### 方案

**依赖**：`python-json-logger`

**`config.py` 新增字段**：
- `log_level: str = "INFO"`
- `log_format: str = "text"`（可选 `json`）
- `log_file: str = ""`（空 = stderr）

**`main.py` lifespan 配置**：
- 先装 root logger（`rich` console handler，text 格式）
- 如果 `log_file` 非空，加 `RotatingFileHandler`（10MB, 5 backup）
- 如果 `log_format=json`，handler 用 `pythonjsonlogger.jsonlogger.JsonFormatter`

**Middleware 层**：
- `correlation_id_middleware`：`uuid4()` 生成 `request_id`，注入 `ContextVar('request_id')`
- `request_logging_middleware`：记录 `{method, path, status_code, duration_ms}`

**Agent 层**：
- `BaseAgent.__init__` 设置 `self.logger = logging.getLogger(f"novel_runtime.agents.{self.__class__.__name__}")`
- 执行开始/结束记录 `INFO`、validation errors 记录 `WARNING`

**LLM 层**：
- `OpenAICompatibleProvider.generate_with_usage()` 记录：
  - `INFO`: `{request_id, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, attempt}`
  - `WARNING`: 重试 `{attempt, error}`
  - `ERROR`: 最终失败 `{error}`（异常已抛出，日志确保记录）

**Service 层**：
- `TaskService` 记录任务状态流转 `{project_id, task_id, task_type, status, duration_ms}`

### 验收标准
- [ ] `uvicorn` 启动可见 `[novel_runtime]` 前缀日志
- [ ] 任意 API 调用产生 `request_id` 追踪
- [ ] LLM 调用记录 token 消耗和耗时
- [ ] `NWR_LOG_FORMAT=json` 输出 JSON 行
- [ ] 测试：`pytest tests/ -q` 全部通过（日志不应改行为）

---

## B.2 Metrics & 健康检查

### 方案

**依赖**：`prometheus-fastapi-instrumentator`

**`/metrics` 端点**：
- 自动注册 HTTP 请求数/延迟直方图
- 自定义指标：
  - `nwr_llm_calls_total{agent, status}` Counter
  - `nwr_llm_tokens_total{agent, type}` Counter（`type=prompt|completion`）
  - `nwr_llm_latency_seconds{agent}` Histogram
  - `nwr_task_duration_seconds{task_type}` Histogram
  - `nwr_chapter_status_count{project, status}` Gauge

**`/health` 升级**：
```json
{
  "status": "ok",
  "version": "0.1.0",
  "checks": {
    "database": {"status": "ok", "detail": "3 tables"},
    "storage": {"status": "ok", "path": "./novel_projects"},
    "llm": {"status": "ok"} // 或 "error": "API key not set"
  }
}
```

### 自定义指标打点

- `LLMProvider.generate_with_usage()` 调 `nwr_llm_*` 指标
- `TaskService.execute_task()` 调 `nwr_task_duration_seconds`
- `api/chapters.py` 调 `nwr_chapter_status_count`（POST /approve 时）

### 验收标准
- [ ] `curl localhost:8000/metrics` 返回 Prometheus 格式
- [ ] `curl localhost:8000/health` 返回 3 个检查
- [ ] 一次 LLM 调用后 `nwr_llm_calls_total` > 0
- [ ] 测试通过

---

## B.3 Docker 化

### 方案

**`Dockerfile`（backend）**：
- 多阶段构建
- builder: `python:3.10-slim`，`pip install -e .[dev]`
- runner: `python:3.10-slim`，copy `/app`
- CMD: `uvicorn novel_runtime.main:app --host 0.0.0.0 --port 8000`
- HEALTHCHECK: `curl -f http://localhost:8000/health`

**`Dockerfile.frontend`**：
- builder: `node:20-alpine`，`npm ci && npm run build`
- runner: `nginx:alpine`，copy `dist/` 到 nginx html
- nginx 配置：`/api/*` proxy_pass `http://backend:8000`

**`docker-compose.yml`**：
```yaml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes: ["./novel_projects:/app/novel_projects"]
    env_file: .env

  frontend:
    build: frontend/
    ports: ["3000:80"]
    depends_on: [backend]
```

**`.env.example`**：
```bash
NWR_LLM_BASE_URL=https://api.openai.com/v1
NWR_LLM_MODEL=gpt-4o-mini
LLM_API_KEY=
NWR_LOG_FORMAT=json
NWR_AUTH_TOKEN=
```

### 验收标准
- [ ] `docker compose build` 成功
- [ ] `docker compose up -d` 后 `curl localhost:8000/health` 返回 ok
- [ ] `open http://localhost:3000` 页面正常

---

## B.4 LLM 缓存

### 方案

**`llm/cache.py`**：
- `LLMCache` 类，SQLite 存储
- key：`sha256(prompt + system_prompt + context_json + model + temperature)`
- value：`{response_text, created_at, hit_count}`
- TTL：`NWR_LLM_CACHE_TTL=86400`（默认 24h），0 = 不过期

**集成到 Provider**：
- `OpenAICompatibleProvider` 构造时接收 `cache: LLMCache | None`
- `generate_with_usage()` 首行检查缓存：
  ```python
  if self.cache:
      key = self.cache.make_key(prompt, system_prompt, context, temperature, self.model)
      cached = self.cache.get(key)
      if cached:
          return cached.response_text, {"cached": True, "total_tokens": 0}
  ```
- 无缓存时调用 LLM 后存结果
- `cached=True` 时不打 LLM metrics

**配置**：
- `Settings.llm_cache_enabled: bool = False`
- `Settings.llm_cache_ttl: int = 86400`
- `Settings.llm_cache_path: str = ""`（空 = `{storage_base_path}/llm_cache.db`）

**CLI**：
- `novel cache stats` — 显示命中率
- `novel cache clear` — 清空缓存

### 验收标准
- [ ] 两次相同 prompt 调用，第二次命中缓存并返回相同结果
- [ ] `NWR_LLM_CACHE_ENABLED=false`（默认）不受影响
- [ ] `novel cache stats` 显示 `{"total": N, "hits": M}`
- [ ] 测试通过

---

## B.5b 孤儿任务恢复

### 方案

**问题**：FastAPI BackgroundTasks 进程内执行，服务重启后 `running` 状态任务永远挂起。

**`task_repo.py` 新增**：
- `list_orphans(threshold_seconds: int = 300) -> list[Task]`：
  `SELECT * FROM tasks WHERE status='running' AND updated_at < datetime('now', '-5 minutes')`

**`main.py` lifespan 改造**：
```python
async def lifespan(app):
    # ... 原有启动逻辑 ...
    orphans = app.state.task_repo.list_orphans()
    for t in orphans:
        task_repo.update_status(t.task_id, "failed", error="Service restart — task orphaned")
        logger.warning("orphan_task_failed", task_id=t.task_id, project_id=t.project_id)
    yield
```

### 验收标准
- [ ] 启动时自动清理 5 分钟前 `running` 的任务
- [ ] 测试 `list_orphans` 方法
- [ ] 测试通过

---

## B.6 Bearer Token 认证 + 限流

### 方案

**依赖**：`slowapi`

**认证**：
- `Settings.auth_token: str = ""`（空 = 禁用）
- `auth_middleware`：检查 `Authorization: Bearer {token}`，不匹配返回 401
- 跳过 `/health`、`/metrics`、`/docs`、`/openapi.json`
- 前端 `api/client.ts`：`localStorage.getItem('nwr_token')` 自动注入

**限流**：
- `slowapi.Limiter` 全局绑定
- 默认：`60/minute`（全端点）
- LLM 端点（`/api/projects/*/chapters/*/draft` 等）: `10/minute`（per project）
- 健康检查/文档：不限流

### 验收标准
- [ ] `NWR_AUTH_TOKEN=""`（默认）行为不变
- [ ] 设置 token 后无 header 返回 401
- [ ] 设置 token 后正确 header 正常访问
- [ ] `slowapi` 限流返回 429
- [ ] 测试通过

---

## B.7 CI（GitHub Actions）

### 方案

**`.github/workflows/ci.yml`**：

```yaml
jobs:
  backend:
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}" }
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ tests/integration/ -q --timeout=30

  frontend:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
        working-directory: frontend/
      - run: npm run build
        working-directory: frontend/

  docker:
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

**`pre-commit` 配置**（可选）：
- `ruff check`（Python lint）
- `prettier --check frontend/src/`（前端格式化）

### 验收标准
- [ ] `.github/workflows/ci.yml` 文件存在
- [ ] 验证：`act --job backend` 可模拟运行（非强制）

---

## 执行顺序

```
B.1 日志 → B.2 Metrics → B.4 缓存 → B.5b 孤儿任务 → B.6 认证 → B.3 Docker → B.7 CI
```

依赖关系：B.1 独立；B.2 强依赖 B.1（日志共享 logger）；B.4 独立但 hook B.2 指标；B.5b 独立；B.6 独立；B.3 依赖 B.6（`.env.example` 含 auth token）；B.7 依赖全部。

---

## 测试策略

- B.1：只新增 module-level `caplog` fixture 验证日志输出，不改行为
- B.2：`prometheus-fastapi-instrumentator` 自带测试，加 `TestClient.get("/metrics")` 验证
- B.4：独立 `test_llm_cache.py` unit 测试
- B.5b：`test_task_repo.py` 新增 `test_list_orphans`
- B.6：`test_api_auth.py` 测试认证/限流
- B.3/B.7：脚本验证，不纳入 pytest

**基线**：每子任务完成 `pytest tests/ -q` ≥ 96 passed（B.4/B.5b/B.6 会新增测试，基线提升）。
