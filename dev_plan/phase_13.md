# Phase 13: 闭环测试 + 连续5章验证 + 量化验收

## 前置条件
- Phase 0-12 全部完成

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 13.1 | 端到端闭环测试框架 | Phase 12 | 1天 |
| 13.2 | 最小闭环测试 | 13.1 | 2天 |
| 13.3 | 量化验收测试 | 13.1 | 2天 |
| 13.4 | 连续5章生成测试 | 13.2 | 3天 |
| 13.5 | Prompt 调优 | 13.3, 13.4 | 3天 |
| 13.6 | 错误处理 + 边界情况 | 13.5 | 1天 |
| 13.7 | README + 部署说明 | 13.6 | 0.5天 |

依赖关系图:
```text
Phase 12 → 13.1 → 13.2 → 13.4 → 13.5 → 13.6 → 13.7
13.1 → 13.3 → 13.5
```

---

## Task 13.1: 端到端闭环测试框架

**文件:**
- `tests/e2e/conftest.py`
- `tests/e2e/test_full_pipeline.py`
- `tests/fixtures/` (测试数据)

**依赖:** Phase 12

### Contract: tests.e2e.conftest

**Fixtures:**
- `real_llm_provider`: 真实 LLM Provider（需要 API Key）
- `full_project`: 创建完整测试项目（含 Bible、Style、3章历史）
- `test_style_sample`: 样本文风文本（都市爽文风格）
- `test_bible_input`: Bible 生成输入数据

### 测试数据准备

**tests/fixtures/style_sample_urban.txt:**
- 约 2000 字的都市快节奏爽文样本文本
- 包含打斗场景、对话场景、场景描写

**tests/fixtures/test_project/:**
- 预创建的项目目录，包含 Bible、3章历史、状态文件

### 测试流程设计

```text
完整闭环测试流程:
1. 创建项目 (渐进式3轮)
2. 上传样本文本 + 分析文风 (含对抗测试)
3. 生成 Novel Bible (含 Writing Strategy + Subplot Registry)
4. 编译第1章上下文 (含叙事诊断 + 状态健康报告)
5. 生成第1章规划 (含节奏规划 + 子线分配 + Agent Contract)
6. 生成第1章正文 (含状态标注)
7. 文风润色
8. 4维度审查 (连续性 + 质量 + 跨章 + 读者模拟)
9. 修复重写 (如有问题)
10. 确认第1章
11. 状态更新 (标注确认式 + diff 感知)
12. Bible 演进检测
13. 编译第2章上下文
```

**验收标准:**
- [ ] 测试框架可运行
- [ ] Fixtures 可用
- [ ] 闭环流程设计完整

---

## Task 13.2: 最小闭环测试

**文件:** `tests/e2e/test_minimal_loop.py`

**测试步骤:**

```python
class TestMinimalLoop:
    """最小闭环测试: 创建项目到第2章上下文编译"""
    
    def test_step_1_create_project(self, real_llm_provider):
        """创建项目"""
        # 创建项目
        # 渐进式3轮 Bible 生成
        # 验收: 项目目录结构完整, Bible 文件存在
    
    def test_step_2_style_analysis(self, real_llm_provider, project):
        """文风分析"""
        # 上传样本文本
        # 分析文风 (含对抗测试)
        # 验收: style_asset.yaml 存在且字段完整
    
    def test_step_3_bible_generation(self, real_llm_provider, project):
        """Bible 生成"""
        # Round 1: 方向变体
        # Round 2: 角色概念
        # Round 3: 完整 Bible
        # 验收: 5个 Bible 文件存在, bible_version=1
    
    def test_step_4_context_compile(self, real_llm_provider, project):
        """编译第1章上下文"""
        # 编译 Context Pack
        # 验收: context_pack.md 存在, 包含叙事诊断
    
    def test_step_5_chapter_plan(self, real_llm_provider, project):
        """生成第1章规划"""
        # 生成 Chapter Plan
        # 验收: chapter_plan.md 存在, 包含节奏规划 + Agent Contract
    
    def test_step_6_chapter_draft(self, real_llm_provider, project):
        """生成第1章正文"""
        # 生成 Draft + State Annotations
        # 验收: draft.md 存在, state_annotations.yaml 存在
    
    def test_step_7_narrative_polish(self, real_llm_provider, project):
        """文风润色"""
        # Polish Draft
        # 验收: styled_draft.md 存在, 文风与 style_asset 一致
    
    def test_step_8_review(self, real_llm_provider, project):
        """4维度审查"""
        # Continuity Review
        # Quality Review
        # Cross-Chapter Review (首章可能有限)
        # Reader Simulation
        # 验收: 4个review文件存在, fix_instructions.yaml 存在
    
    def test_step_9_approve_and_update(self, real_llm_provider, project):
        """确认第1章 + 状态更新"""
        # 确认章节
        # 状态更新
        # 验收: final.md 存在, snapshot 存在, 状态文件已更新
    
    def test_step_10_compile_chapter_2(self, real_llm_provider, project):
        """编译第2章上下文"""
        # 编译第2章 Context Pack
        # 验收: context_pack.md 存在, 信息基于第1章更新后的状态
    
    def test_full_loop(self, real_llm_provider):
        """完整闭环一次性测试"""
        # 执行 step_1 到 step_10
        # 验收: 全流程无报错
```

**验收标准:**
- [ ] 最小闭环完整跑通
- [ ] 每步的产出文件存在且格式正确
- [ ] 无未捕获的异常

---

## Task 13.3: 量化验收测试

**文件:** `tests/e2e/test_quantitative.py`

### 连续性验收测试

```python
class TestContinuityMetrics:
    """连续性验收标准"""
    
    def test_character_state_consistency(self):
        """角色状态矛盾率 < 5%"""
        # 连续生成5章
        # 检查角色状态是否有矛盾
        # 矛盾定义: 角色在同一时间出现在不同地点, 知道不该知道的信息等
    
    def test_timeline_consistency(self):
        """时间线跳跃错误 = 0"""
        # 检查时间线是否有不合理跳跃
    
    def test_hook_tracking(self):
        """已埋伏笔遗忘率 < 10%"""
        # 检查 open 状态的伏笔是否在合理范围内被提及或推进
    
    def test_information_boundary(self):
        """信息边界违规 = 0"""
        # 检查角色是否知道不该知道的信息
    
    def test_subplot_tracking(self):
        """子线遗忘 = 0 (超过策略阈值未推进)"""
        # 检查活跃子线是否在策略阈值内被推进
```

### 写作质量验收测试

```python
class TestQualityMetrics:
    """写作质量验收标准"""
    
    def test_each_chapter_has_conflict(self):
        """每章有明确冲突 = 100%"""
        # 检查每章的 chapter_plan 是否有 Conflict 字段
    
    def test_each_chapter_has_ending_hook(self):
        """每章结尾有继续阅读驱动力 = 100%"""
        # 检查每章的 Ending Hook
    
    def test_no_consecutive_3_chapters_without_satisfaction(self):
        """连续3章无爽点 = 0次"""
        # 检查每章的 satisfaction_level
    
    def test_reader_sim_score(self):
        """读者模拟器评分 > 7/10"""
        # 检查 reader_sim_review 的弃书风险评分
    
    def test_style_consistency(self):
        """文风与 Style Asset 一致性"""
        # 人工评估或自动化检查关键文风参数
```

### 节奏验收测试

```python
class TestRhythmMetrics:
    """节奏验收标准"""
    
    def test_no_consecutive_same_rhythm(self):
        """连续2章同节奏类型 = 0次"""
        # 检查各章 rhythm_type
    
    def test_protagonist_progress(self):
        """主角连续2章无实质进展 = 0次"""
        # 检查 state_annotations 中主角的发展标注
    
    def test_hook_overload(self):
        """伏笔过载 (超过策略上限) = 0次"""
        # 检查 open hooks 数量 vs strategy.max_open_hooks
```

**验收标准:**
- [ ] 连续性指标全部达标
- [ ] 写作质量指标全部达标
- [ ] 节奏指标全部达标

---

## Task 13.4: 连续5章生成测试

**文件:** `tests/e2e/test_five_chapters.py`

### 测试流程

```python
class TestFiveChapterGeneration:
    """连续5章生成测试"""
    
    def test_generate_five_chapters(self, real_llm_provider):
        """连续生成5章并验证"""
        # 创建项目 + Bible (使用预设数据加速)
        # 生成第1章 → 确认 → 状态更新
        # 生成第2章 → 确认 → 状态更新
        # ...
        # 生成第5章 → 确认 → 状态更新
        
        # 验证:
        # 1. 每章生成无报错
        # 2. 状态正确更新
        # 3. 伏笔被记录
        # 4. 子线被推进
        # 5. 角色状态无矛盾
        # 6. 时间线无跳跃
    
    def test_state_snapshot_consistency(self):
        """快照一致性"""
        # 检查每章后的 snapshot
        # 每个 snapshot 应该可以独立恢复
        
    def test_context_pack_evolution(self):
        """上下文包演化"""
        # 检查第1-5章的 context_pack
        # 每章的上下文应该基于前一章更新后的状态
    
    def test_health_report_progression(self):
        """健康报告演化"""
        # 检查每章的 state_health_report
        # 随着章节增加，健康报告应该有正确的告警
```

**验收标准:**
- [ ] 5章连续生成无报错
- [ ] 角色状态无矛盾
- [ ] 时间线无跳跃
- [ ] 伏笔被记录（open/triggered/resolved）
- [ ] 子线被推进
- [ ] 每章有快照
- [ ] 每章有摘要

---

## Task 13.5: Prompt 调优

**目标:** 基于测试结果，调整各 Agent 的 Prompt 模板

**调优维度:**
1. 输出格式稳定性 — 确保每次生成都能正确解析
2. 内容质量 — 确保生成的文本、审查报告等满足要求
3. Agent Contract 达成率 — 确保 Writer 满足 Planner 的承诺
4. 状态标注覆盖率 — 确保 state_annotations 覆盖所有关键状态变化
5. 文风一致性 — 确保 Polish 后的文本符合 style_asset

**调优方法:**
1. 识别最常见的格式错误 → 在 Prompt 末尾追加格式示例
2. 识别最常见的内容质量问题 → 在 Prompt 中增加具体指令
3. Agent Contract 达成率低 → 加强 Planner 的约束或 Writer 的指令
4. 状态标注遗漏 → 在 Writer Prompt 中增加遗漏类型的提醒
5. 文风不一致 → 在 Polisher Prompt 中增加具体文风参数对照

**验收标准:**
- [ ] 各 Agent 输出格式校验通过率 > 90%
- [ ] 重试率 < 20%
- [ ] 量化验收标准全部达标

---

## Task 13.6: 错误处理 + 边界情况

**文件:** `tests/e2e/test_edge_cases.py`

### 边界测试用例

```python
class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_style_analysis(self):
        """空样本文本分析"""
    
    def test_very_long_style_sample(self):
        """超长样本文本"""
    
    def test_first_chapter_no_history(self):
        """第1章无历史上下文"""
    
    def test_zero_hooks(self):
        """无伏笔情况"""
    
    def test_zero_subplots(self):
        """无子线情况"""
    
    def test_max_hooks_exceeded(self):
        """伏笔超过上限"""
    
    def test_state_update_with_user_edits(self):
        """用户修改后的状态更新"""
    
    def test_rollback_after_3_chapters(self):
        """3章后回滚"""
    
    def test_bible_update_after_new_world_setting(self):
        """新增世界观设定后的 Bible 更新"""
    
    def test_llm_call_failure_retry(self):
        """LLM 调用失败重试"""
    
    def test_invalid_chapter_status_transition(self):
        """非法章节状态转换"""
```

**验收标准:**
- [ ] 所有边界情况有合理错误处理
- [ ] 错误信息清晰可操作
- [ ] 不丢失数据

---

## Task 13.7: README + 部署说明

**文件:**
- `README.md`
- `docs/deployment.md`

### README.md 内容

```markdown
# Novel Writing Runtime

自动化小说边写运行时

## 快速开始

### 安装
pip install -e .

### 配置
export NWR_LLM_API_KEY=your-api-key
export NWR_LLM_BASE_URL=https://api.example.com/v1
export NWR_LLM_MODEL=gpt-4

### 创建项目
novel init --name "我的小说" --genre "都市修仙"

### 生成文风资产
novel style analyze --project my-project --sample style_sample.txt --name "都市快节奏"

### 生成 Novel Bible
novel bible generate --project my-project

### 生成章节
novel context compile --project my-project --chapter 1
novel chapter plan --project my-project --chapter 1
novel chapter draft --project my-project --chapter 1
novel chapter polish --project my-project --chapter 1
novel chapter review --project my-project --chapter 1
novel chapter approve --project my-project --chapter 1

### 更新状态
novel state update --project my-project --chapter 1

### 继续下一章
novel context compile --project my-project --chapter 2
...

## 开发
pip install -e ".[dev]"
pytest tests/
```

### docs/deployment.md 内容

- Python 环境要求 (3.11+)
- 依赖安装
- 环境变量配置
- SQLite 初始化
- 关键配置项说明
- 常见问题排查

**验收标准:**
- [ ] README 完整可操作
- [ ] 部署说明覆盖所有配置项
