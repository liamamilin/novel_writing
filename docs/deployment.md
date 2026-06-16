# 部署说明

## 环境要求

- Python 3.10+
- SQLite 3.x（内置支持）

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd novel_runtime

# 安装依赖
pip install -e ".[dev]"

# (可选) 安装 tiktoken 以获得准确的 Token 计数
pip install tiktoken
```

## 配置

所有配置通过环境变量设置，前缀为 `NWR_`：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| NWR_LLM_API_KEY | 是 | - | LLM API Key |
| NWR_LLM_BASE_URL | 是 | - | API 端点 URL |
| NWR_LLM_MODEL | 是 | - | 模型名称 |
| NWR_LLM_PROVIDER | 否 | openai_compatible | Provider 类型 |
| NWR_STORAGE_BASE_PATH | 否 | ./novel_projects | 项目存储路径 |
| NWR_LOG_LEVEL | 否 | INFO | 日志级别 |

也支持 `.env` 文件:

```bash
NWR_LLM_API_KEY=sk-xxx
NWR_LLM_BASE_URL=https://api.openai.com/v1
NWR_LLM_MODEL=gpt-4
```

## 启动

```bash
# API 服务
uvicorn novel_runtime.main:app --host 0.0.0.0 --port 8000

# 开发模式（热重载）
uvicorn novel_runtime.main:app --reload
```

## 测试

```bash
# 全部测试
pytest tests/

# 带覆盖率
pytest tests/ --cov=novel_runtime

# 端到端测试（需要 LLM API Key）
pytest tests/e2e/
```

## 常见问题

**Q: 启动时提示 SQLite 错误？**
A: 检查 NWR_STORAGE_BASE_PATH 是否可写，默认路径为 `./novel_projects`。

**Q: LLM 调用失败？**
A: 确认 NWR_LLM_API_KEY、NWR_LLM_BASE_URL、NWR_LLM_MODEL 三个环境变量已正确设置。

**Q: Token 计数不准确？**
A: 安装 tiktoken: `pip install tiktoken`
