# Phase 2: LLM 调用层 + Prompt 模板 + 输出校验框架

## 前置条件
- Phase 0 完成
- Phase 1 完成（Storage 层可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 2.1 | LLM Provider 基类 + 工厂 | Phase 0 | 1天 |
| 2.2 | OpenAI Compatible Provider | 2.1 | 1天 |
| 2.3 | Prompt 模板加载器 + 渲染 | 2.1 | 0.5天 |
| 2.4 | Token 计数器 + 预算管理 | 2.1 | 1天 |
| 2.5 | 输出校验框架 | 2.1 | 1天 |
| 2.6 | Base Agent (validate + retry) | 2.1, 2.4, 2.5 | 1.5天 |
| 2.7 | 任务执行器 (BackgroundTasks) | 2.6, Phase 1.6 | 1天 |
| 2.8 | LLM + Agent 集成测试 | 2.2-2.7 | 1天 |

依赖关系图:
```text
2.1 → 2.2
2.1 → 2.3
2.1 → 2.4
2.1 → 2.5
2.1 + 2.4 + 2.5 → 2.6
2.6 + Phase 1.6 → 2.7
2.2 + 2.3 + 2.4 + 2.5 + 2.6 + 2.7 → 2.8
```

---

## Task 2.1: LLM Provider 基类 + 工厂

**文件:**
- `novel_runtime/llm/__init__.py`
- `novel_runtime/llm/provider.py`

**依赖:** Phase 0

### Contract: llm.provider.LLMProvider (抽象基类)

**抽象方法:**

#### `generate(prompt: str, system_prompt: str = "", context: dict | None = None, temperature: float | None = None, max_tokens: int | None = None) → str`
- Input: prompt, system_prompt, 可选 context dict, 可选 temperature/max_tokens
- Output: LLM 生成的文本
- 调用失败时抛出 `LLMCallError`
- 默认 temperature 由 config 提供，参数可覆盖

#### `generate_with_usage(prompt: str, system_prompt: str = "", context: dict | None = None, temperature: float | None = None, max_tokens: int | None = None) → tuple[str, dict]`
- 返回 `(text, usage_dict)`
- `usage_dict` 包含 `prompt_tokens`, `completion_tokens`, `total_tokens`
- Provider 不支持 usage 时，usage_dict 值为 -1

#### `count_tokens(text: str) → int`
- 返回文本的 token 数量
- Provider 特定 tokenizer

### Contract: llm.provider.create_provider

**Input:**
- `config: Settings`

**Output:**
- `LLMProvider` 实例

**Guarantees:**
- 根据 `config.llm_provider` 字段创建对应 Provider
- 目前只支持 `openai_compatible`，其他值抛出 `ValueError`

**Error cases:**
- 未知 provider 类型 → `ValueError`

**验收标准:**
- [ ] 抽象基类定义完整
- [ ] 工厂方法根据配置创建正确 Provider

**测试用例:**
- test_create_provider_openai: config.llm_provider="openai_compatible" → 创建 OpenAICompatibleProvider
- test_create_provider_unknown: config.llm_provider="unknown" → ValueError

---

## Task 2.2: OpenAI Compatible Provider

**文件:**
- `novel_runtime/llm/openai_provider.py`

**依赖:** Task 2.1

### Contract: llm.openai_provider.OpenAICompatibleProvider

**初始化参数:**
- `base_url: str`
- `model: str`
- `api_key: str` (从环境变量读取)
- `default_temperature: float = 0.7`
- `default_max_tokens: int = 4096`
- `max_retries: int = 1`

**Implements:** LLMProvider

#### `generate` 实现

**Behavior:**
- 使用 httpx 发送 POST 请求到 `{base_url}/chat/completions`
- 请求体: `{"model": self.model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}`
- 如果 `context` 不为空，将其追加到 system_prompt 末尾
- 重试逻辑：请求失败时重试 `max_retries` 次，指数退避
- 超时设置：连接超时 10s，读取超时 120s（长文本生成）

**Error cases:**
- API Key 无效 → `LLMCallError` 包含状态码 401
- 请求超时 → `LLMCallError` 包含 "timeout"
- 429 限流 → `LLMCallError` 包含状态码 429，自动重试
- 500 服务器错误 → `LLMCallError`，自动重试

#### `generate_with_usage` 实现

**Behavior:**
- 同 `generate`，但从 response 中提取 `usage` 字段
- usage 字段不存在时返回 `{prompt_tokens: -1, completion_tokens: -1, total_tokens: -1}`

#### `count_tokens` 实现

**Behavior:**
- 使用 tiktoken 库
- 默认使用 cl100k_base 编码（GPT-3.5/4 兼容）
- 中文文本 token 计数准确度 ±5%

**验收标准:**
- [ ] 可调用 OpenAI Compatible API 并获取响应
- [ ] 重试逻辑正确（失败后重试指定次数）
- [ ] Token 计数与 API 使用量误差在 ±10% 内
- [ ] 超时和错误正确处理

**测试用例:**
- test_generate_success: Mock API 返回 → 正确提取文本
- test_generate_with_usage: Mock API → 正确提取 usage
- test_generate_retry: Mock API 第一次失败第二次成功 → 重试后返回结果
- test_generate_max_retries_exceeded: Mock API 连续失败 → LLMCallError
- test_count_tokens: 中英文混合文本 → token 数在合理范围
- test_context_injection: context dict → 追加到 system_prompt

---

## Task 2.3: Prompt 模板加载器 + 渲染

**文件:**
- `novel_runtime/llm/prompt_loader.py`

**依赖:** Task 2.1

### Contract: llm.prompt_loader.PromptLoader

**初始化参数:**
- `prompts_dir: Path` — Prompt 模板目录路径

#### `load(template_name: str, variables: dict | None = None) → str`
- Input: 模板名（不含扩展名, 如 "style_analysis"），可选变量字典
- Output: 渲染后的 Prompt 文本

**Behavior:**
- 从 `prompts_dir/{template_name}.md` 加载模板
- 模板使用 `{{variable_name}}` 语法
- 如果提供了 variables，替换所有匹配的 `{{key}}` 为对应值
- 未匹配的 `{{key}}` 保留原样（不报错，用于可选变量）
- 模板不存在时抛出 `FileNotFoundError`

**Guarantees:**
- 模板加载后缓存（同一模板只读取一次文件）
- 缓存可通过 `clear_cache()` 清除

#### `list_templates() → list[str]`
- 列出 prompts_dir 下所有 .md 文件的名称（不含扩展名）

**验收标准:**
- [ ] 模板加载和变量替换正确
- [ ] 缓存机制工作
- [ ] 未匹配变量静默保留

**测试用例:**
- test_load_simple: 加载模板 → 渲染变量 → 正确替换
- test_load_missing_variable: 模板有 {{optional}} 但未提供 → 保留原文
- test_template_not_found: 不存在的模板名 → FileNotFoundError
- test_list_templates: 列出所有模板 → 正确
- test_cache: 两次加载同一模板 → 第二次使用缓存

---

## Task 2.4: Token 计数器 + 预算管理

**文件:**
- `novel_runtime/llm/token_counter.py`

**依赖:** Task 2.1

### Contract: llm.token_counter.TokenCounter

#### `count_tokens(text: str) → int`
- 使用 tiktoken 计算文本 token 数
- 同 Provider 的计数方法

#### `count_messages_tokens(messages: list[dict]) → int`
- 计算 OpenAI 格式消息列表的 token 数
- 包含消息格式开销（role, content 等字段）

### Contract: llm.token_counter.TokenBudgetManager

**初始化参数:**
- `total_budget: int` — 总 token 预算（默认从 config 读取）
- `allocation: dict[str, int]` — 各部分 token 分配
- `priority_order: list[str]` — 截断优先级

#### `allocate(sections: dict[str, str]) → dict[str, str]`
- Input: 各部分名称到内容的映射，如 `{"style_and_voices": "...", "character_state": "..."}`
- Output: 裁剪后的各部分名称到内容的映射

**Behavior:**
- 为每个部分计算 token 数
- 如果总量在预算内，原样返回
- 如果超出预算，按 priority_order 从低优先级开始截断
- 截断策略:
  - 截断到该部分分配预算的 80%
  - 在句号/换行处截断（保持语义完整）
  - 截断后追加 "...(已截断，预算不足)"

**Guarantees:**
- 返回的内容总 token 数 <= total_budget
- 高优先级部分优先保留
- 截断位置在句子边界

#### `get_budget_summary(sections: dict[str, str]) → dict[str, dict]`
- 返回各部分的 `{name: {tokens: int, budget: int, percentage: float, truncated: bool}}`

**验收标准:**
- [ ] Token 计数误差在 ±10% 内（与实际 API 比较）
- [ ] 预算内内容完整保留
- [ ] 超预算内容按优先级截断
- [ ] 截断位置在句子边界

**测试用例:**
- test_count_tokens: 英文文本 → token 数合理
- test_count_tokens_chinese: 中文文本 → token 数合理
- test_allocate_within_budget: 总量在预算内 → 原样返回
- test_allocate_over_budget: 总量超预算 → 低优先级截断
- test_allocate_truncate_at_sentence: 截断位置在句号/换行处
- test_budget_summary: 返回各部分统计信息

---

## Task 2.5: 输出校验框架

**文件:**
- `novel_runtime/llm/output_validator.py`

**依赖:** Task 2.1

### Contract: llm.output_validator.BaseValidator

**抽象方法:**

#### `validate(raw_output: str) → ValidationResult`
- Input: LLM 原始输出文本
- Output: `ValidationResult` 包含 `is_valid: bool`, `parsed_data: Any`, `errors: list[str]`

#### `get_schema() → dict`
- 返回期望的输出格式描述（用于 Prompt 中的格式说明）

### Contract: llm.output_validator.ValidationResult

**Fields:**
- `is_valid: bool`
- `parsed_data: Any` — 解析后的数据（如果 is_valid=True）
- `errors: list[str]` — 错误列表（如果 is_valid=False）
- `raw_output: str` — 原始输出

### Contract: llm.output_validator.YAMLValidator(BaseValidator)

**初始化参数:**
- `required_fields: list[str]` — 必须存在的顶级字段
- `optional_fields: list[str]` — 可选字段
- `field_types: dict[str, type]` — 字段类型校验

**Behavior:**
- 尝试将 raw_output 解析为 YAML
- 检查所有 required_fields 存在
- 检查 field_types 中指定的字段类型
- 解析失败时返回 `is_valid=False` + 具体错误信息

### Contract: llm.output_validator.MarkdownValidator(BaseValidator)

**初始化参数:**
- `required_sections: list[str]` — 必须存在的章节标题（二级标题 ##）
- `section_content_rules: dict[str, str]` — 各章节的内容规则描述（如 "至少3行"）

**Behavior:**
- 解析 Markdown 标题结构
- 检查所有 required_sections 存在
- 可选：检查各章节内容满足规则

### Contract: llm.output_validator.validate_with_retry

**Input:**
- `validator: BaseValidator`
- `llm_output: str`
- `max_retries: int = 1`
- `provider: LLMProvider`
- `original_prompt: str`
- `original_system_prompt: str = ""`

**Output:**
- `ValidationResult` — 最终验证结果

**Behavior:**
1. 用 validator 验证 llm_output
2. 如果 is_valid=True，直接返回
3. 如果 is_valid=False 且 max_retries > 0：
   - 构造重试 prompt，包含原始输出 + 错误信息 + 期望格式
   - 重新调用 LLM
   - 重新验证
4. 如果仍然失败，返回最后一次的 ValidationResult（is_valid=False，保留原始输出）

**Guarantees:**
- 最多重试 max_retries 次
- 每次重试的 prompt 包含具体的错误信息
- 不修改原始 llm_output

**验收标准:**
- [ ] YAML 校验器正确校验必需字段和类型
- [ ] Markdown 校验器正确校验章节结构
- [ ] 重试逻辑在第一次失败后能重试
- [ ] 重试失败后返回原始输出

**测试用例:**
- test_yaml_validator_valid: 合法 YAML → is_valid=True
- test_yaml_validator_missing_field: 缺少必需字段 → is_valid=False + 具体错误
- test_yaml_validator_wrong_type: 字段类型错误 → is_valid=False
- test_markdown_validator_valid: 合法 Markdown → is_valid=True
- test_markdown_validator_missing_section: 缺少章节 → is_valid=False
- test_validate_with_retry_success: 第一次失败，重试成功 → 返回成功结果
- test_validate_with_retry_all_fail: 两次都失败 → 返回 is_valid=False

---

## Task 2.6: Base Agent (validate + retry)

**文件:**
- `novel_runtime/agents/__init__.py`
- `novel_runtime/agents/base.py`

**依赖:** Task 2.1, 2.4, 2.5

### Contract: agents.base.BaseAgent

**初始化参数:**
- `provider: LLMProvider`
- `prompt_loader: PromptLoader`
- `validator: BaseValidator | None = None`
- `max_retries: int = 1`

**抽象方法:**

#### `get_prompt_template() → str`
- 返回该 Agent 使用的 Prompt 模板名

#### `get_validator() → BaseValidator | None`
- 返回该 Agent 使用的输出校验器，None 表示不校验

#### `process_output(raw_output: str, context: dict) → AgentResult`
- 处理 LLM 输出，提取结构化数据
- 子类实现

### Contract: agents.base.AgentResult

**Fields:**
- `success: bool`
- `data: Any` — 处理后的数据
- `raw_output: str` — LLM 原始输出
- `validation_errors: list[str]` — 校验错误（如有）
- `retries_used: int` — 使用了几次重试
- `tokens_used: dict` — token 使用量

### Contract: agents.base.BaseAgent.execute

**Input:**
- `variables: dict` — Prompt 模板变量
- `context: dict | None = None` — 传递给 LLM 的额外上下文

**Output:**
- `AgentResult`

**Behavior:**
1. 加载 Prompt 模板
2. 渲染模板变量
3. 调用 `provider.generate_with_usage`
4. 如果有 validator:
   a. 用 validator 校验输出
   b. 校验失败 → 构造重试 prompt（包含错误信息）→ 重新调用 → 重新校验
   c. 最多重试 max_retries 次
5. 调用 `process_output` 处理最终输出
6. 返回 `AgentResult`

**Guarantees:**
- 非 LLM 错误不重试（如文件读写错误）
- LLM 错误（429, 500, timeout）由 Provider 层重试
- 校验失败时重试，重试 prompt 包含具体错误信息
- `retries_used` 记录实际重试次数
- `tokens_used` 记录所有调用（含重试）的总 token 使用量

**验收标准:**
- [ ] 执行流程完整: 模板加载 → 渲染 → LLM 调用 → 校验 → 处理
- [ ] 校验失败后正确重试
- [ ] AgentResult 包含所有必要信息

**测试用例:**
- test_execute_success: Mock LLM 返回合法输出 → success=True
- test_execute_validation_fail_retry: Mock LLM 第一次非法，第二次合法 → success=True, retries_used=1
- test_execute_validation_fail_all: Mock LLM 总是非法 → success=False, retries_used=max_retries
- test_execute_llm_error: Mock LLM 抛出 LLMCallError → AgentResult.success=False
- test_execute_records_tokens: 检查 tokens_used 字段

---

## Task 2.7: 任务执行器 (BackgroundTasks)

**文件:**
- `novel_runtime/services/task_service.py`

**依赖:** Task 2.6, Phase 1.6 (db.task_repo)

### Contract: services.task_service.TaskService

**方法清单:**

#### `create_task(project_id: str, task_type: TaskType, input_data: dict) → Task`
- 创建任务记录，状态为 pending
- 返回 Task model

#### `execute_task(task_id: str, agent: BaseAgent, variables: dict, context: dict | None = None) → Task`
- 更新任务状态为 running
- 调用 `agent.execute(variables, context)`
- 成功: 更新任务状态为 success，保存 output_data
- 失败: 更新任务状态为 failed，保存 error 信息
- 返回更新后的 Task

#### `execute_task_async(project_id: str, task_type: TaskType, agent: BaseAgent, variables: dict, context: dict | None = None) → Task`
- 创建任务 → 通过 FastAPI BackgroundTasks 异步执行 → 立即返回 pending 状态的 Task
- 任务完成后更新数据库记录

#### `get_task(task_id: str) → Task`
- 查询任务状态

#### `list_tasks(project_id: str, task_type: TaskType | None = None) → list[Task]`
- 按项目列出任务，可按类型筛选

#### `cancel_task(task_id: str) → Task`
- 取消 pending 状态的任务
- running 状态的任务不可取消

**Error cases:**
- 任务不存在 → `ValueError`
- 取消 running 状态任务 → `InvalidStateTransitionError`

**Guarantees:**
- 异步任务通过 BackgroundTasks 执行，不阻塞 API
- 任务状态转换遵循: pending → running → success/failed
- 任务失败时 error 信息完整保存

**验收标准:**
- [ ] 同步任务执行正确
- [ ] 异步任务通过 BackgroundTasks 执行
- [ ] 任务状态转换正确
- [ ] 失败任务保存错误信息

**测试用例:**
- test_create_task: 创建任务 → pending 状态
- test_execute_task_success: 执行成功 → success 状态 + output_data
- test_execute_task_failure: 执行失败 → failed 状态 + error 信息
- test_execute_async: 异步执行 → 立即返回 pending → 完成后 success
- test_cancel_task: 取消 pending 任务 → cancelled 状态
- test_cancel_running_task: 取消 running 任务 → InvalidStateTransitionError

---

## Task 2.8: LLM + Agent 集成测试

**文件:**
- `tests/unit/test_llm.py`
- `tests/unit/test_prompt_loader.py`
- `tests/unit/test_token_counter.py`
- `tests/unit/test_output_validator.py`
- `tests/integration/test_base_agent.py`
- `tests/integration/test_task_service.py`

**依赖:** Task 2.1-2.7

**测试范围:**

### Unit Tests (不需要 LLM)
- test_token_counter_accuracy: 与 tiktoken 直接调用比较
- test_prompt_loader_rendering: 变量替换正确性
- test_yaml_validator: 各种输入的校验
- test_markdown_validator: 各种输入的校验
- test_budget_allocation: 预算分配和截断

### Integration Tests (Mock LLM)
- test_base_agent_full_flow: Mock LLM → 加载模板 → 渲染 → 调用 → 校验 → 处理
- test_base_agent_retry: Mock LLM 第一次非法 → 重试成功
- test_task_service_sync: 同步任务执行
- test_task_service_async: 异步任务执行

**验收标准:**
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 测试覆盖率 > 80%
