# Phase 14: CLI 完善

## 前置条件
- Phase 13 完成（闭环测试通过）

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 14.1 | CLI 框架搭建 (Typer) | Phase 13 | 0.5天 |
| 14.2 | 项目管理命令 | 14.1 | 0.5天 |
| 14.3 | 文风分析命令 | 14.1 | 0.5天 |
| 14.4 | Bible 生成命令 | 14.1 | 0.5天 |
| 14.5 | 上下文编译命令 | 14.1 | 0.5天 |
| 14.6 | 章节操作命令 | 14.2-14.5 | 1天 |
| 14.7 | 状态管理命令 | 14.6 | 0.5天 |
| 14.8 | 查询命令 | 14.7 | 0.5天 |
| 14.9 | CLI 集成测试 | 14.8 | 0.5天 |

---

## Task 14.1: CLI 框架搭建

**文件:**
- `novel_runtime/cli/__init__.py`
- `novel_runtime/cli/main.py`

### Contract: cli.main

**Framework:** Typer

**App:** `novel` (main command group)

**Commands:**
```text
novel init           # 创建项目
novel style           # 文风相关命令
novel bible           # Bible 相关命令
novel context          # 上下文编译
novel chapter          # 章节相关命令
novel state            # 状态相关命令
novel health           # 健康检查
novel next             # 下一章建议
```

**Options:**
- `--project, -p`: 项目路径（默认当前目录）
- `--verbose, -v`: 详细输出
- `--config, -c`: 配置文件路径

**Output:** 使用 Rich 库美化输出（进度条、表格、颜色）

---

## Task 14.2-14.8: 命令实现细节

### `novel init`

```text
用法: novel init --name NAME --genre GENRE [--idea IDEA] [--target-reader READER] [--selling-point POINT]

流程:
1. 创建项目目录
2. 初始化目录结构
3. 生成 project.yaml
4. 输出: 项目创建成功，下一步建议

输出示例:
✅ 项目 '都市修仙项目' 创建成功!
📁 项目路径: ./novel_20260616_xxxxx
📋 下一步: 运行 novel style analyze 上传样本文本
```

### `novel style analyze`

```text
用法: novel style analyze --project PATH --sample FILE --name NAME [--run-adversarial]

流程:
1. 上传样本文本
2. 分析文风
3. (可选) 运行对抗测试
4. 输出: 文风资产摘要

输出示例:
📊 文风分析完成!
🏷️  文风名称: 都市快节奏爽文
📝 核心特征: 短句为主, 对白直接, 情绪曲线递进
✅ 对抗测试: 通过
📋 文风资产: style_001.yaml
```

### `novel bible generate`

```text
用法: novel bible generate --project PATH [--round 1|2|3]

流程:
Round 1: 生成3个方向变体，用户选择
Round 2: 生成角色概念，用户确认
Round 3: 生成完整 Bible

输出示例 (Round 1):
📊 方向变体生成完成!
1️⃣ 快节奏爽文型
2️⃣ 剧情推进型
3️⃣ 人物成长型
请选择 (1-3): 
```

### `novel context compile`

```text
用法: novel context compile --project PATH --chapter N [--goal "本章目标"]

流程:
1. 运行 Context Assembler
2. 运行 State Health Checker
3. 运行 Context Compiler
4. 输出: Context Pack 路径 + 健康告警数量

输出示例:
📚 上下文编译完成!
📄 Context Pack: chapters/chapter_001/context_pack.md
⚠️  健康告警: 2 条
  - 角色遗漏: 林雪已5章没有发展
  - 节奏重复: 连续2章同类型
```

### `novel chapter plan/draft/polish/review/fix/approve`

```text
用法: novel chapter plan --project PATH --chapter N
用法: novel chapter draft --project PATH --chapter N
用法: novel chapter polish --project PATH --chapter N
用法: novel chapter review --project PATH --chapter N [--types continuity,quality,cross_chapter,reader_sim]
用法: novel chapter fix --project PATH --chapter N
用法: novel chapter approve --project PATH --chapter N [--final-text FILE]

每步完成后输出:
✅ 章节规划完成! → chapters/chapter_001/chapter_plan.md
📊 节奏类型: 递进型
📋 子线推进: subplot_faction_war
📋 Agent Contract: 3 promises, 2 constraints
```

### `novel state update/rollback`

```text
用法: novel state update --project PATH --chapter N
用法: novel state rollback --project PATH --target-chapter N

state update 输出:
✅ 状态更新完成!
📊 快照已保存: snapshots/state_after_chapter_001.yaml
📄 更新文件: story_state.yaml, characters.yaml, hooks.yaml
⚠️  Bible 更新建议: 新增隐藏势力'暗阁'
📋 下一章建议:
  1. 神秘势力后续
  2. 赵坤的报复
  3. 林雪邀请主角私下见面

rollback 输出:
⚠️  确认回滚到第 22 章? [y/N]: y
✅ 状态已回滚到第 22 章
```

### `novel health check`

```text
用法: novel health check --project PATH [--chapter N]

输出:
📊 状态健康检查
⚠️  2 个告警:
  🔴 伏笔过期: H005 已超出计划回收范围3章
  🟡 角色遗漏: 林雪已5章没有发展
✅ 6 项正常
```

### `novel next suggest`

```text
用法: novel next suggest --project PATH

输出:
📋 下一章建议:
  1. 神秘势力后续 (优先级: 高)
     原因: 伏笔 H012 已到推进时机
  2. 赵坤的报复 (优先级: 中)
     原因: 子线 faction_war 3章未推进
  3. 林雪私下见面 (优先级: 中)
     原因: 角色林雪需要发展
```

---

## Task 14.9: CLI 集成测试

**文件:** `tests/integration/test_cli.py`

**测试范围:**
- test_cli_init: 创建项目 → 目录结构完整
- test_cli_style_analyze: 文风分析 → style_asset 生成
- test_cli_bible_generate: Bible 生成 → 文件存在
- test_cli_context_compile: 上下文编译 → context_pack 生成
- test_cli_chapter_plan: 章节规划 → chapter_plan 生成
- test_cli_health_check: 健康检查 → 告警列表

**验收标准:**
- [ ] 所有 CLI 命令可用
- [ ] 每步的输入输出正确
- [ ] 错误信息清晰
- [ ] Rich 输出格式化正确
