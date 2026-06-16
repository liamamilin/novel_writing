# Phase 3: 文风资产 + Character Voice Asset + 对抗测试

## 前置条件
- Phase 0 完成（数据模型）
- Phase 1 完成（Storage 层）
- Phase 2 完成（LLM 调用层 + 输出校验）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 3.1 | Style Storage 层 | Phase 1 | 0.5天 |
| 3.2 | Style Analyst Agent + Prompt | Phase 2 | 2天 |
| 3.3 | Character Voice Asset 数据结构与 Storage | Phase 1 | 0.5天 |
| 3.4 | 文风对对抗测试 | 3.2 | 1天 |
| 3.5 | Style Service 编排层 | 3.1, 3.2, 3.3 | 1天 |
| 3.6 | Style API 端点 | 3.5 | 0.5天 |
| 3.7 | Style 集成测试 | 3.6 | 1天 |

依赖关系图:
```text
Phase 1 → 3.1 ──→ 3.5 → 3.6 → 3.7
Phase 2 → 3.2 → 3.4 ─→ 3.5
Phase 1 → 3.3 ─────────→ 3.5
```

---

## Task 3.1: Style Storage 层

**文件:**
- `novel_runtime/storage/style_storage.py`

**依赖:** Phase 1

### Contract: storage.style_storage.StyleStorage

#### `save_style_asset(project_path: Path, style: StyleAsset) → Path`
- 保存 style_asset.yaml 到 `style_assets/{style_id}.yaml`
- 如果 style_id 对应文件已存在，覆盖

#### `load_style_asset(project_path: Path, style_id: str) → StyleAsset`
- 加载指定 style_id 的文风资产
- 不存在时抛出 `FileNotFoundError`

#### `list_style_assets(project_path: Path) → list[StyleAsset]`
- 列举 `style_assets/` 下所有 .yaml 文件
- 按 style_id 排序

#### `save_source_text(project_path: Path, sample_id: str, text: str) → Path`
- 保存样本文本到 `source_texts/{sample_id}.txt`

#### `load_source_text(project_path: Path, sample_id: str) → str`
- 加载样本文本

#### `list_source_texts(project_path: Path) → list[str]`
- 列举所有样本文本 ID

#### `save_character_voice(project_path: Path, voice: CharacterVoice) → Path`
- 保存到 `style_assets/character_voices/{voice_id}. yaml`

#### `load_character_voice(project_path: Path, voice_id: str) → CharacterVoice`
- 加载角色声音资产

#### `list_character_voices(project_path: Path) → list[CharacterVoice]`
- 列举所有角色声音

**验收标准:**
- [ ] 文风资产 YAML 读写正确（含 conditional_rules）
- [ ] 样本文本读写正确
- [ ] 角色声音资产读写正确

**测试用例:**
- test_style_roundtrip: StyleAsset → 保存 → 加载 → 字段一致
- test_style_conditional_rules: 含 conditional_rules 的 StyleAsset 读写正确
- test_source_text: 样本文本 → 保存 → 加载 → 内容一致
- test_character_voice_roundtrip: CharacterVoice → 保存 → 加载 → 字段一致

---

## Task 3.2: Style Analyst Agent + Prompt

**文件:**
- `novel_runtime/agents/style_analyst.py`
- `prompts/style_analysis.md`

**依赖:** Phase 2

### Agent: StyleAnalystAgent

**继承:** BaseAgent

**方法:**

#### `analyze_style(sample_ids: list[str], style_name: str) → StyleAsset`
- Input: 样本文本 ID 列表, 目标文风名称
- 从 Storage 加载所有样本文本
- 构造 Prompt 变量: `{samples}`, `{style_name}`
- 调用 LLM 生成文风分析
- 校验输出为合法的 YAML
- 返回 StyleAsset model

#### `generate_test_paragraph(style: StyleAsset, topic: str = "一场激烈的拍卖会") → str`
- Input: 文风资产, 测试主题
- 构造 Prompt 变量: `{style_params}`, `{topic}`
- 调用 LLM 生成测试段落
- 返回生成的段落文本

#### `get_prompt_template() → str`
- 返回 `"style_analysis"`

#### `get_validator() → BaseValidator`
- 返回 YAMLValidator，校验字段: narration, sentence_rhythm, dialogue_style, description_density, emotion_curve, conflict_pattern, chapter_opening, chapter_ending, scene_density, avoid

### Prompt Design: style_analysis.md

**Input Specification:**
- `{{samples}}`: 合并后的样本文本，用 `---` 分隔多个样本
- `{{style_name}}`: 目标文风名称（如 "都市快节奏爽文"）

**Output Specification:**
- YAML 格式，包含所有 StyleAsset 字段
- 必须包含 conditional_rules 的示例模板

**Key Instructions:**
1. 分析叙事视角 (第一人称/第三人称/全知/贴身视角)
2. 分析句式节奏 (短句为主/中等/长句为主)
3. 分析对白风格 (直接冲突型/含蓄型/信息型)
4. 描写密度 (环境描写比例, 动作描写比例, 心理描写比例)
5. 情绪曲线模式 (铺垫→爆发→释放, 或其他模式)
6. 冲突推进方式 (外部冲突驱动/内部驱动)
7. 章节开头方式 (冲突开场/悬念开场/日常开场)
8. 章节结尾方式 (反转/Twitter hook/情绪收束)
9. 禁用表达模式 (大段设定说明, 连续心理独白, 重复口癖, 过度形容)
10. 条件文风规则 (战斗场景/情感场景/对话场景的文风调整)
11. 不复制原文表达，只提取抽象特征
12. 输出 YAML 格式严格遵守字段定义

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 输出不是合法 YAML | 解析失败 | 提示"请输出合法的YAML格式" |
| 缺少必需字段 | 校验不通过 | 提示缺少的具体字段名 |
| conditional_rules 为空 | 文风无法场景化调整 | 提示"请至少为战斗场景和情感场景各写一条条件规则" |
| avoid 字段为空 | 缺少禁用表达 | 提示"请列出至少3个该文风应避免的表达模式" |

**Test Inputs:**
- Case 1: 提供一段都市快节奏爽文样本 → 预期: sentence_rhythm 包含"短句", dialogue_style 包含"直接冲突"
- Case 2: 提供传统文学样本 → 预期: sentence_rhythm 包含"长句", description_density 包含"高"
- Case 3: 提供两段不同样本 → 预期: 分析综合特征

**验收标准:**
- [ ] Agent 能从样本文本生成完整的 StyleAsset
- [ ] 生成的 StyleAsset 包含所有必需字段
- [ ] 输出格式校验正确
- [ ] 重试逻辑在格式错误时工作

**测试用例:**
- test_analyze_style: Mock LLM 返回合法 YAML → StyleAsset 字段完整
- test_analyze_style_invalid_yaml: Mock LLM 返回非法格式 → 重试 or 报错
- test_generate_test_paragraph: Mock LLM 返回段落 → 返回文本

---

## Task 3.3: Character Voice Asset 数据结构与 Storage

**文件:**
- 已在 Task 3.1 中包含

**说明:** Character Voice 的数据结构模型已在 Phase 0 定义（`models/style.py` 中的 `CharacterVoice`），Storage 方法已在 Task 3.1 中包含。此任务主要是验证模型和存储的完整性。

**验收标准:**
- [ ] CharacterVoice 模型序列化/反序列化正确
- [ ] speech_patterns 子对象正确处理
- [ ] internal_monologue 子对象正确处理
- [ ] quirks 列表正确处理

**测试用例:**
- test_character_voice_full: 包含所有字段的 CharacterVoice 读写
- test_character_voice_minimal: 只包含必需字段的 CharacterVoice 读写
- test_character_voice_quirks: 包含多个 quirks 的读写

---

## Task 3.4: 文风对抗测试

**文件:**
- `novel_runtime/agents/style_analyst.py` (新增方法)
- `prompts/adversarial_test.md`

**依赖:** Task 3.2

### Agent: StyleAnalystAgent 新增方法

#### `adversarial_test(style: StyleAsset) → AdversarialTestResult`

**Contract:**

**Input:**
- `style: StyleAsset` — 待测试的文风资产

**Output:**
- `AdversarialTestResult`:
  - `passed: bool` — 是否通过
  - `deviation_paragraph: str` — 生成的偏离段落
  - `analysis: str` — 对偏离段落的文风分析
  - `identified_deviation: bool` — 是否成功识别偏离

**Behavior:**
1. 基于 style_asset 生成一段**故意偏离**该文风的段落
   - Prompt: "根据以下文风参数，写一段**刻意违反**这些特征的文字"
2. 用 style_analyst 对偏离段落进行文风分析
3. 比较分析结果和原始 style_asset
4. 如果分析结果与原始资产显著不同（偏离点被识别），测试通过
5. 如果分析结果与原始资产相似（偏离点未被识别），测试失败

**Guarantees:**
- 最多生成 3 轮偏离段落
- 如果 3 轮都未通过，返回 passed=False 并记录原因
- 每轮调整偏离程度

**Error cases:**
- LLM 生成失败 → 返回 passed=False

### Prompt Design: adversarial_test.md

**Step 1 Prompt (生成偏离):**
- 输入: `{style_params}` — 完整的文风参数
- 指令: "写一段刻意违反以下文风特征的文字。违反方式包括：句式节奏相反、对白风格相反、情绪曲线平坦、缺少冲突推进"
- 输出: 一段约500字的偏离段落

**Step 2 Prompt (分析偏离段落):**
- 输入: `{deviation_paragraph}`
- 指令: "分析以下文字的文风特征"
- 输出: YAML 格式的文风参数

**Step 3 (代码逻辑):**
- 比较 Step 2 的分析结果和原始 style_asset
- 如果关键特征（sentence_rhythm, dialogue_style, emotion_curve）方向相反 → 通过
- 如果关键特征相似 → 未通过，调整偏离参数重试

**验收标准:**
- [ ] 能生成偏离文风的段落
- [ ] 能识别偏离和不偏离的段落
- [ ] 测试结果正确反映文风资产的区分度

**测试用例:**
- test_adversarial_pass: Mock LLM 返回明显偏离的段落 → 分析结果与原始差异大 → passed=True
- test_adversarial_fail: Mock LLM 返回与原始相似的段落 → 分析结果与原始差异小 → passed=False
- test_adversarial_retry: 第一次未通过，第二次通过 → 重试后 passed=True

---

## Task 3.5: Style Service 编排层

**文件:**
- `novel_runtime/services/style_service.py`

**依赖:** Task 3.1, 3.2, 3.3

### Contract: services.style_service.StyleService

#### `upload_sample(project_id: str, sample_name: str, text: str) → str`
- Input: 项目 ID, 样本名称, 样本文本
- 生成 sample_id
- 调用 StyleStorage.save_source_text
- 返回 sample_id

#### `analyze_style(project_id: str, sample_ids: list[str], style_name: str, run_adversarial: bool = True) → StyleAsset`
- Input: 项目 ID, 样本 ID 列表, 目标文风名称, 是否运行对抗测试
- 创建异步任务（样本多时耗时较长）
- 调用 StyleAnalystAgent.analyze_style
- 如果 run_adversarial=True:
  - 调用 StyleAnalystAgent.adversarial_test
  - 未通过时记录警告，仍然保存资产
- 调用 StyleStorage.save_style_asset 保存结果
- 更新 project.default_style_id
- 返回 StyleAsset

**同步版本:** `analyze_style_sync` — 直接调用，返回结果而非任务 ID

#### `generate_test_paragraph(project_id: str, style_id: str, topic: str = "一场激烈的拍卖会") → str`
- 加载 StyleAsset
- 调用 StyleAnalystAgent.generate_test_paragraph
- 返回生成的段落

#### `get_style(project_id: str, style_id: str) → StyleAsset`
- 加载指定文风资产

#### `list_styles(project_id: str) → list[StyleAsset]`
- 列举项目所有文风资产

#### `save_character_voice(project_id: str, voice: CharacterVoice) → CharacterVoice`
- 保存角色声音资产

#### `get_character_voice(project_id: str, voice_id: str) → CharacterVoice`
- 加载角色声音资产

**验收标准:**
- [ ] 上传样本 → 分析文风 → 保存资产完整流程可跑通
- [ ] 对抗测试可选执行
- [ ] 角色声音资产 CRUD 正确

**测试用例:**
- test_upload_sample: 上传样本文本 → sample_id 正确
- test_analyze_style_sync: Mock LLM → 分析 → 保存 → 可查询
- test_analyze_style_with_adversarial: Mock LLM → 分析 + 对抗 → 保存
- test_list_styles: 创建2个 style → 列出 → 2个结果

---

## Task 3.6: Style API 端点

**文件:**
- `novel_runtime/api/styles.py`

**依赖:** Task 3.5

### API 端点

#### `POST /api/projects/{project_id}/style-samples`
- Request body: `{"sample_name": "样本文风1", "text": "样本文本内容"}`
- Response: `{"sample_id": "sample_001", "status": "uploaded"}`
- 调用 `StyleService.upload_sample`

#### `POST /api/projects/{project_id}/styles/analyze`
- Request body: `{"sample_ids": ["sample_001"], "style_name": "都市快节奏爽文", "run_adversarial": true}`
- Response: `{"task_id": "task_xxx", "status": "pending"}` （异步）
- 调用 `StyleService.analyze_style`（异步版本）
- 如果样本少且短，可以同步返回

#### `GET /api/projects/{project_id}/styles/{style_id}`
- Response: StyleAsset JSON
- 调用 `StyleService.get_style`

#### `GET /api/projects/{project_id}/styles`
- Response: `list[StyleAsset]`
- 调用 `StyleService.list_styles`

#### `POST /api/projects/{project_id}/styles/{style_id}/test-paragraph`
- Request body: `{"topic": "一场激烈的拍卖会"}`
- Response: `{"paragraph": "生成的测试段落"}`
- 调用 `StyleService.generate_test_paragraph`

#### `GET /api/tasks/{task_id}`
- Response: Task JSON（查询异步任务状态）
- 调用 `TaskService.get_task`

**验收标准:**
- [ ] 所有端点可通过 HTTP 测试
- [ ] 错误情况返回正确状态码
- [ ] 异步任务状态可查询

**测试用例:**
- test_api_upload_sample: POST → 201 + sample_id
- test_api_analyze_style: POST → 202 + task_id
- test_api_get_style: GET → StyleAsset
- test_api_list_styles: GET → list
- test_api_test_paragraph: POST → paragraph
- test_api_style_not_found: GET 不存在的 style_id → 404

---

## Task 3.7: Style 集成测试

**文件:**
- `tests/integration/test_style_service.py`
- `tests/integration/test_style_api.py`

**测试范围:**

### Service 层集成测试 (Mock LLM)
- test_full_style_pipeline: 上传样本 → 分析文风 → 保存 → 查询
- test_style_with_adversarial: 分析文风 + 对抗测试
- test_multiple_samples: 多个样本的分析

### API 层集成测试 (Mock LLM)
- test_api_upload_and_analyze: 上传样本 → 触发分析 → 查询结果
- test_api_async_flow: 异步分析 → 轮询任务状态 → 结果
- test_api_error_handling: 不存在的项目 → 404

**验收标准:**
- [ ] 所有集成测试通过
- [ ] 测试覆盖率 > 80%