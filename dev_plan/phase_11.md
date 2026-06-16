# Phase 11: Cross-Chapter Auditor + Reader Simulator

## 前置条件
- Phase 10 完成（Review 框架可用）
- Phase 7 完成（Context Pack 可用）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 11.1 | Cross-Chapter Auditor Agent + Prompt | Phase 2, 7, 10 | 2天 |
| 11.2 | Reader Simulator Agent + Prompt | Phase 2, 3, 7 | 2天 |
| 11.3 | 4维度审查聚合 | 10.4, 11.1, 11.2 | 1天 |
| 11.4 | Review Service 扩展 | 11.3 | 0.5天 |
| 11.5 | 集成测试 | 11.4 | 1天 |

---

## Task 11.1: Cross-Chapter Auditor Agent + Prompt

**文件:**
- `novel_runtime/agents/cross_chapter_auditor.py`
- `prompts/cross_chapter_review.md`

### Agent: CrossChapterAuditorAgent

#### `review(styled_draft: str, recent_plans: list[str], recent_reviews: list[str], story_state: dict, hooks: list[Hook], subplots: list[Subplot], strategy: WritingStrategy) → CrossChapterReviewResult`

**Contract:**

**Input:**
- styled_draft: 当前章节正文
- recent_plans: 最近3-5章的 chapter_plan.md
- recent_reviews: 最近3-5章的审查报告
- story_state: 全局状态（story_state.yaml 内容）
- hooks: 伏笔列表
- subplots: 子线列表
- strategy: 写作策略

**Output:**
- `CrossChapterReviewResult`: `review_content: str` (Markdown)

**审查维度:**
1. 节奏连续性：最近N章的节奏变化是否合理
2. 子线推进：各子线是否按策略推进
3. 伏笔管理：开放伏笔数量是否过载/过少
4. 角色发展：主要角色是否有持续发展
5. 读者体验预测：读者是否会产生疲劳/困惑/无聊
6. 策略合规性：是否违反 writing_strategy 中的各项策略

### Prompt Design: cross_chapter_review.md

**Key Instructions:**
1. 必须回看最近3-5章的节奏类型，判断是否连续同节奏
2. 必须检查每条活跃子线的推进频率
3. 必须统计开放伏笔数量并与策略上限比较
4. 必须检查主要角色的发展频率
5. 每个维度给出具体数据和诊断
6. 输出 format 必须包含 Rhythm Analysis, Subplot Status, Hook Status, Character Development, Strategy Compliance 五个章节

---

## Task 11.2: Reader Simulator Agent + Prompt

**文件:**
- `novel_runtime/agents/reader_simulator.py`
- `prompts/reader_simulation.md`

### Agent: ReaderSimulatorAgent

#### `simulate(styled_draft: str, style_asset: StyleAsset, recent_summary: str, target_reader: str, strategy: WritingStrategy) → ReaderSimResult`

**Contract:**

**Input:**
- styled_draft: 当前章节正文
- style_asset: 文风资产
- recent_summary: 最近1章摘要
- target_reader: 目标读者画像（如"喜欢快节奏打脸升级的读者"）
- strategy: 写作策略

**Output:**
- `ReaderSimResult`: `review_content: str` (Markdown)

**模拟维度:**
1. 兴奋点预测：哪里读者会兴奋
2. 无聊点预测：哪里读者可能跳读
3. 困惑点预测：哪里读者可能不理解
4. 弃书风险预测：哪里读者可能弃书（1-10分）
5. 下一章期待预测：读者看完后最想看什么
6. 对主角的共情程度：上升/平稳/下降
7. 爽感释放满意度
8. 情绪弧线预测：开头→中段→结尾

### Prompt Design: reader_simulation.md

**Key Instructions:**
1. 模拟目标读者视角，不是文学评论家视角
2. 兴奋点和无聊点必须指向具体段落/场景
3. 弃书风险必须给出1-10分数
4. 必须从"读者是否想继续看下一章"的角度评价
5. 情绪弧线必须给出具体的情感标签和曲线
6. 不要做文学性评价，只做读者体验预测

---

## Task 11.3: 4维度审查聚合

**文件:** `novel_runtime/compiler/fix_instruction_merger.py` (扩展)

### Contract: merge_all_reviews

**Input:**
- `continuity_review: ContinuityReviewResult`
- `quality_review: QualityReviewResult`
- `cross_chapter_review: str`
- `reader_sim_review: str`

**Output:**
- `FixInstructionsFile` — 合并所有4维度审查的修复指令

**Behavior:**
1. 从连续性审查提取 critical 和 moderate 问题
2. 从质量审查提取分数 < 6 的维度
3. 从跨章审查提取策略违规和节奏问题
4. 从读者模拟提取弃书风险 > 6 的点
5. 合并并去重
6. 按 severity 排序
7. 如果修复指令超过 10 条，只保留 critical + severity 最高的 moderate

---

## Task 11.4: Review Service 扩展

**文件:** `novel_runtime/services/review_service.py` (扩展)

### Contract: ReviewService 扩展 review_chapter

- 新增 review_types: "cross_chapter", "reader_sim"
- 加载最近3-5章的 plan 和 review
- 加载 story_state, hooks, subplots, strategy
- 调用 CrossChapterAuditorAgent
- 调用 ReaderSimulatorAgent
- 保存审查报告到对应文件
- 合并所有4维度生成 fix_instructions

**验收标准:**
- [ ] 4维度审查全部可执行
- [ ] 修复指令合并跨4个维度

---

## Task 11.5: 集成测试

**测试范围:**
- test_cross_chapter_review: Mock LLM → 包含5个维度
- test_reader_simulation: Mock LLM → 包含弃书风险评分
- test_merge_all_reviews: 4维度审查 → 合并修复指令
- test_review_service_4d: 完整4维度审查流程
- test_review_api_4d: HTTP 测试

**验收标准:**
- [ ] 跨章审查包含所有5个维度
- [ ] 读者模拟包含弃书风险评分
- [ ] 4维度修复指令合并正确
