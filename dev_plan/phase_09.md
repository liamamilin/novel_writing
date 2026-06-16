# Phase 9: Chapter Writer (含状态标注) + Narrative Polisher

## 前置条件
- Phase 8 完成（Chapter Plan 可用）
- Phase 3 完成（Style Asset 可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 9.1 | State Annotations 数据模型 + Validator | Phase 0 | 0.5天 |
| 9.2 | Chapter Writer Agent + Prompt | Phase 2, 8 | 3天 |
| 9.3 | Narrative Polisher Agent + Prompt | Phase 2, 3 | 2天 |
| 9.4 | Chapter Service (draft + polish) | 9.1, 9.2, 9.3 | 1天 |
| 9.5 | Chapter Draft/Polish API 端点 | 9.4 | 0.5天 |
| 9.6 | 集成测试 | 9.5 | 1天 |

依赖关系图:
```text
Phase 0 → 9.1 → 9.4 → 9.5 → 9.6
Phase 2+8 → 9.2 → 9.4
Phase 2+3 → 9.3 → 9.4
```

---

## Task 9.1: State Annotations 数据模型 + Validator

**文件:**
- `novel_runtime/models/state_annotations.py` (已在 Phase 0 定义，此处实现 Validator)
- `novel_runtime/llm/output_validator.py` (扩展)

**依赖:** Phase 0

### Contract: output_validator.StateAnnotationsValidator(BaseValidator)

**初始化参数:**
- `required_annotation_types: list[str]` — 必须包含的标注类型

**Behavior:**
- 尝试将 LLM 输出解析为 YAML
- 校验为合法的 `StateAnnotationsFile` 结构
- 检查 `annotations` 列表中是否包含 `required_annotation_types`
- 检查每个 annotation 的 `type`, `location`, 必需字段

**验收标准:**
- [ ] 合法的状态标注通过校验
- [ ] 缺少必需类型的标注报错
- [ ] 格式错误的标注报错

**测试用例:**
- test_valid_annotations: 合法标注 → is_valid=True
- test_missing_required_type: 缺少 character_state_change → is_valid=False
- test_invalid_location_format: location 格式错误 → is_valid=False

---

## Task 9.2: Chapter Writer Agent + Prompt

**文件:**
- `novel_runtime/agents/chapter_writer.py`
- `prompts/chapter_write.md`

**依赖:** Phase 2, 8

### Agent: ChapterWriterAgent

**继承:** BaseAgent

#### `write(context_pack: str, chapter_plan: str, style_asset: StyleAsset, character_voices: list[CharacterVoice], contract: AgentContract) → ChapterWriteResult`

**Contract:**

**Input:**
- context_pack: 完整 Context Pack
- chapter_plan: Chapter Plan Markdown
- style_asset: 文风资产
- character_voices: 本章出场角色的声音资产
- contract: Agent Contract (从 Plan 中提取)

**Output:**
- `ChapterWriteResult`: `draft: str` (Markdown), `annotations: StateAnnotationsFile`, `contract_check: dict`

**contract_check:**
- `promises_fulfilled: list[bool]` — 每个承诺是否满足
- `constraints_followed: list[bool]` — 每个约束是否遵守
- `all_fulfilled: bool`

**Behavior:**
1. 加载 Prompt 模板 `chapter_write`
2. 渲染变量: `{context_pack}`, `{chapter_plan}`, `{style_params}`, `{voice_params}`, `{contract_promises}`, `{contract_constraints}`
3. 调用 LLM（可能需要分段调用以控制长度）
4. 解析输出:
   - 提取正文部分 → draft
   - 提取状态标注部分 → annotations
   - 自检 Agent Contract → contract_check
5. 校验输出
6. 返回结构化结果

**Validator:** 组合校验:
- MarkdownValidator 校验正文包含场景分隔
- StateAnnotationsValidator 校验标注包含必需类型

### Prompt Design: chapter_write.md

**Input Specification:**
- `{{context_pack}}`: 完整 Context Pack
- `{{chapter_plan}}`: Chapter Plan（含 Agent Contract）
- `{{style_params}}`: 文风参数摘要
- `{{voice_params}}`: 角色声音参数
- `{{contract_promises}}`: Agent Contract promises
- `{{contract_constraints}}`: Agent Contract constraints

**Output Specification:**
- Markdown 正文 + YAML 状态标注
- 正文必须按场景分隔（### Scene N）
- 状态标注必须包含: character_state_change, new_hook, subplot_advance 等
- 状态标注以 `---ANNOTATIONS---` 分隔符与正文分开

**Key Instructions:**
1. 严格按照 Chapter Plan 的场景列表生成
2. 严格遵循 Agent Contract 的 promises 和 constraints
3. 每个场景必须产生至少一个状态变化
4. 保持人物信息边界（角色不知道不该知道的事）
5. 保持当前时间线一致
6. 不提前暴露未公开秘密
7. 每个角色的对白必须符合 Character Voice Asset
8. 根据条件文风规则调整不同场景的写法（战斗场景 vs 情感场景）
9. 结尾必须保留下一章驱动力
10. 生成正文的同时生成结构化的状态标注
11. 标注中的 location 使用 "scene_N_paragraph_M" 格式

**Failure Modes:**

| 失败模式 | 症状 | 应对策略 |
|----------|------|----------|
| 缺少状态标注 | 无 ANNOTATIONS 分隔符 | 提示"必须在正文后用 ---ANNOTATIONS--- 分隔符输出状态标注" |
| 场景数量不匹配 | 与 Plan 不一致 | 提示"必须严格按照 Chapter Plan 的场景列表生成，场景数量为 N" |
| 角色对白无区分 | 所有角色说话风格相同 | 提示"每个角色的对白必须符合其 Character Voice Asset，特别强调 {character_name} 的 {voice_feature}" |
| 状态标注遗漏 | 缺少关键类型 | 提示"状态标注必须包含以下类型: {required_types}" |

**验收标准:**
- [ ] 正文按场景分隔
- [ ] 状态标注包含必需类型
- [ ] Agent Contract 自检通过
- [ ] 角色声音区分明显

---

## Task 9.3: Narrative Polisher Agent + Prompt

**文件:**
- `novel_runtime/agents/narrative_polisher.py`
- `prompts/narrative_polish.md`

**依赖:** Phase 2, 3

### Agent: NarrativePolisherAgent

**继承:** BaseAgent

#### `polish(draft: str, annotations: StateAnnotationsFile, style_asset: StyleAsset, chapter_plan: str, character_voices: list[CharacterVoice]) → str`

**Contract:**

**Input:**
- draft: 正文草稿 Markdown
- annotations: 状态标注（用于确保不改变剧情事实）
- style_asset: 文风资产
- chapter_plan: 章节规划（含节奏要求）
- character_voices: 角色声音资产

**Output:**
- 润色后的正文 Markdown

**Behavior:**
1. 加载 Prompt 模板 `narrative_polish`
2. 渲染变量: `{draft}`, `{style_params}`, `{rhythm_type}`, `{voice_params}`, `{annotations_summary}`
3. 调用 LLM
4. 校验输出是 Markdown
5. 返回润色后文本

**Validator:** 简单 MarkdownValidator，只需确认非空且有段落

### Prompt Design: narrative_polish.md

**Key Instructions:**
1. 强化场景张力：增加冲突表现力，压缩铺垫，突出爆发点
2. 优化情绪曲线：确保情绪从铺垫到爆发到释放的节奏合理
3. 增强对白冲突感：对白要直接、有对抗性，减少寒暄
4. 调整节奏快慢交替：紧张场景用短句，舒缓场景放慢
5. 确保角色声音区分度：每个角色说话有独特风格
6. 删除不符合文风的表达：参照 style_asset 的 avoid 列表
7. **硬约束：不得改变剧情事实**（参照 annotations）
8. **硬约束：不得新增重大设定**
9. **硬约束：不得改变人物动机**
10. **硬约束：不得改变伏笔状态**

---

## Task 9.4: Chapter Service (draft + polish)

**文件:** `novel_runtime/services/chapter_service.py` (扩展)

### Contract: ChapterService 新增方法

#### `generate_draft(project_id: str, chapter_number: int) → ChapterWriteResult`
1. 检查章节状态（必须是 planned）
2. 加载 context_pack, chapter_plan, style_asset, character_voices
3. 提取 Agent Contract 从 chapter_plan
4. 调用 ChapterWriterAgent.write()
5. 验证 Agent Contract 自检结果
6. 保存 draft.md 和 state_annotations.yaml
7. 更新章节状态为 drafted
8. 返回结果

#### `polish_draft(project_id: str, chapter_number: int) → str`
1. 检查章节状态（必须是 drafted）
2. 加载 draft, annotations, style_asset, chapter_plan, character_voices
3. 调用 NarrativePolisherAgent.polish()
4. 保存 styled_draft.md
5. 返回润色后文本

**Error cases:**
- 章节状态不正确 → `InvalidStateTransitionError`
- style_asset 未设置 → `StyleNotSetError`

**验收标准:**
- [ ] Draft 生成包含正文和标注
- [ ] Polish 后不改变剧情事实
- [ ] 章节状态流转正确

---

## Task 9.5: Chapter Draft/Polish API 端点

**文件:** `novel_runtime/api/chapters.py` (扩展)

### API 端点

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/draft`
- Request: `{"context_pack_path": "...", "plan_path": "...", "target_word_count": 3000}`
- Response: `{"draft_path": "...", "state_annotations_path": "...", "contract_check": {...}}`
- 异步执行

#### `POST /api/projects/{project_id}/chapters/{chapter_number}/polish`
- Request: `{"draft_path": "...", "style_id": "style_001"}`
- Response: `{"styled_draft_path": "..."}`
- 异步执行

**验收标准:**
- [ ] API 端点可调用
- [ ] 异步任务可查询状态

---

## Task 9.6: 集成测试

**文件:** `tests/integration/test_chapter_writer.py`, `tests/integration/test_narrative_polisher.py`

**测试范围:**
- test_writer_generates_draft: Mock LLM → draft 包含正文和标注
- test_writer_contract_check: Agent Contract 自检
- test_writer_voice_distinction: 角色声音区分
- test_polisher_preserves_facts: 润色不改变剧情事实
- test_polisher_applies_style: 润色后文风一致
- test_chapter_service_draft_flow: 完整 draft 流程
- test_chapter_service_polish_flow: 完整 polish 流程
- test_api_draft: HTTP 测试
- test_api_polish: HTTP 测试

**验收标准:**
- [ ] 所有集成测试通过
- [ ] Draft 包含正文和状态标注
- [ ] Polish 后文风与 style_asset 一致
