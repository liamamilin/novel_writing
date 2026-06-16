# Phase 15: Web UI

## 前置条件
- Phase 14 完成（CLI 可用）
- 所有后端 API 可用

## 任务总览

| Task | 名称 | 依赖 | 预估 |
|------|------|------|------|
| 15.1 | React 项目初始化 | 无 | 0.5天 |
| 15.2 | API Client 层 | 15.1 | 0.5天 |
| 15.3 | 三栏布局骨架 | 15.1 | 0.5天 |
| 15.4 | 项目创建页面 (渐进式3轮) | 15.2 | 1天 |
| 15.5 | 左侧资产树 | 15.2 | 1天 |
| 15.6 | 中间章节编辑区 | 15.2 | 1.5天 |
| 15.7 | 右侧 AI 操作面板 | 15.2 | 1天 |
| 15.8 | 审查报告展示 | 15.5, 15.6 | 1天 |
| 15.9 | 状态快照查看 + Diff | 15.5 | 0.5天 |
| 15.10 | Bible 版本管理 | 15.5 | 0.5天 |
| 15.11 | Subplot/Hook/Strategy 管理 | 15.5 | 1天 |
| 15.12 | 整体打磨 | 15.3-15.11 | 1天 |

---

## Task 15.1: React 项目初始化

**技术栈:**
- React 18 + TypeScript
- Vite (构建工具)
- Tailwind CSS (样式)
- React Router (路由)
- Zustand (状态管理)
- React Query (数据请求)
- Milkdown 或 Editor.js (Markdown 编辑器)

**项目结构:**
```text
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  tailwind.config.js
  src/
    main.tsx
    App.tsx
    api/                    # API Client
      client.ts
      projects.ts
      styles.ts
      bible.ts
      context.ts
      chapters.ts
      state.ts
      subplots.ts
      hooks.ts
    stores/                 # Zustand stores
      projectStore.ts
      chapterStore.ts
      uiStore.ts
    components/             # UI 组件
      layout/
        ThreeColumnLayout.tsx
        LeftPanel.tsx
        CenterPanel.tsx
        RightPanel.tsx
      project/
        CreateProjectDialog.tsx
        DirectionSelector.tsx
        CharacterEditor.tsx
      asset/
        AssetTree.tsx
        StyleAssetViewer.tsx
        CharacterVoiceEditor.tsx
      chapter/
        ChapterEditor.tsx
        ChapterStatusBadge.tsx
        ChapterTimeline.tsx
      review/
        ReviewPanel.tsx
        ReviewTabs.tsx
        FixInstructionList.tsx
      ai/
        ActionButton.tsx
        AsyncTaskList.tsx
        HealthAlertList.tsx
    pages/
      ProjectList.tsx
      ProjectDetail.tsx
      ChapterDetail.tsx
    types/
      index.ts
```

**验收标准:**
- [ ] `npm run dev` 可启动
- [ ] 首页可访问

---

## Task 15.2: API Client 层

**文件:** `frontend/src/api/`

### Contract: api.client

**Base Configuration:**
- `baseURL`: 可配置（默认 `/api`）
- 请求拦截: 自动添加项目 ID
- 响应拦截: 统一错误处理
- 异步任务轮询: POST 返回 task_id → 轮询状态直到完成

**Methods:**
- 每个后端 API 端点对应一个方法
- 异步操作返回 task_id 和轮询逻辑
- 错误统一处理，展示 toast 通知

**验收标准:**
- [ ] 所有 API 端点可调用
- [ ] 异步任务轮询正确
- [ ] 错误处理统一

---

## Task 15.3: 三栏布局骨架

**文件:** `frontend/src/components/layout/`

### 布局设计

```text
┌──────────────┬─────────────────────┬──────────────┐
│   Left Panel │   Center Panel      │  Right Panel  │
│   280px      │   flex-1            │  320px        │
│              │                     │              │
│  Asset Tree  │  Chapter Editor     │  AI Actions   │
│  - Bible     │  - Markdown Editor  │  - Buttons    │
│  - Styles    │  - Status Bar      │  - Task List  │
│  - Chapters  │  - Review Panel    │  - Health     │
│  - States    │                     │              │
│  - Hooks     │                     │              │
│  - Subplots  │                     │              │
└──────────────┴─────────────────────┴──────────────┘
```

**交互:**
- 左栏可折叠
- 右栏可折叠
- 中间 Markdown 编辑器全屏模式
- 响应式布局（移动端堆叠）

**验收标准:**
- [ ] 三栏布局正确
- [ ] 可折叠
- [ ] 响应式

---

## Task 15.4: 项目创建页面 (渐进式3轮)

**UI 流程:**

**Round 1 — 方向选择:**
- 输入框: 项目名称、类型、创意、目标读者
- 生成 3 个方向变体卡片
- 每个卡片: 名称、核心卖点、节奏风格、主角类型
- 用户选择或混搭

**Round 2 — 角色确认:**
- 展示角色概念列表
- 每个角色: 名称、性格、目标、弧线方向
- 编辑按钮: 修改角色属性
- 确认按钮

**Round 3 — Bible 生成:**
- 显示生成进度
- 生成完成后展示 Bible 摘要
- 按钮: 查看 Bible / 开始写作

**验收标准:**
- [ ] 3轮流程可完整走通
- [ ] 每轮有加载状态和错误处理

---

## Task 15.5: 左侧资产树

**组件:** `AssetTree`

**树结构:**
```text
📁 项目名称
├── 📖 Bible
│   ├── novel_bible.md
│   ├── world_setting.md
│   ├── character_profiles.md
│   ├── volume_plan.md
│   └── chapter_plan.md
├── 🎨 文风资产
│   ├── style_001.yaml
│   └── character_voices/
├── 📝 章节
│   ├── chapter_001 ✓
│   ├── chapter_002 🔧
│   └── chapter_003 ○
├── 📊 状态
│   ├── story_state.yaml
│   ├── characters.yaml
│   └── hooks.yaml
├── 🔗 伏笔
├── 📈 子线
└── ⚙️ 策略
```

**交互:**
- 点击文件 → 在中间区域打开（Markdown 查看器或 YAML 编辑器）
- 章节状态图标: ✓ approved, 🔧 drafting, ○ planned
- 右键菜单: 重命名、删除

**验收标准:**
- [ ] 资产树正确显示项目结构
- [ ] 点击打开文件内容
- [ ] 章节状态图标正确

---

## Task 15.6: 中间章节编辑区

**组件:** `ChapterEditor`

**功能:**
- Markdown 编辑器（Milkdown 或类似）
- 章节状态流转换示: planned → drafted → reviewed → approved → locked
- 状态切换按钮: 确认/拒绝
- 审查报告标签页: Continuity | Quality | Cross-Chapter | Reader Sim
- 修复指令列表 + 执行按钮
- Diff 视图: draft vs final

**验收标准:**
- [ ] Markdown 编辑器可编辑
- [ ] 状态流转正确
- [ ] 审查报告标签切换正确

---

## Task 15.7: 右侧 AI 操作面板

**组件:** `ActionPanel`

**按钮组:**
```text
📁 项目管理
  - 创建项目
  - 查看项目信息

🎨 文风
  - 上传样本
  - 分析文风
  - 生成测试段落
  - 对抗测试

📖 Bible
  - 生成方向变体
  - 生成角色概念
  - 生成完整 Bible
  - 查看/更新 Bible

📝 章节
  - 编译上下文
  - 生成规划
  - 生成草稿
  - 文风润色
  - 审查 (4维度)
  - 修复重写
  - 确认章节

📊 状态
  - 更新状态
  - 查看健康报告
  - 回滚状态
```

**异步任务状态:**
- 每个按钮点击后显示 loading
- 异步任务完成后显示 toast 通知
- 任务失败显示错误信息和重试按钮

**验收标准:**
- [ ] 所有按钮可点击
- [ ] Loading 状态正确
- [ ] 异步任务轮询正确

---

## Task 15.8: 审查报告展示

**组件:** `ReviewPanel`, `ReviewTabs`, `FixInstructionList`

**审查报告内容:**
- Continuity: Issues 列表 + 严重程度标记
- Quality: 评分雷达图 + 具体问题
- Cross-Chapter: 节奏分析图 + 子线状态
- Reader Sim: 情绪曲线图 + 弃书风险评分

**修复指令列表:**
- 按 severity 排序
- 每条显示: 类型、位置、问题描述、建议修改
- 执行按钮: 自动修复

**验收标准:**
- [ ] 4个标签页切换正确
- [ ] 修复指令按严重程度排序
- [ ] 自动修复按钮可触发

---

## Task 15.9: 状态快照查看 + Diff

**组件:** `SnapshotViewer`

**功能:**
- 列出所有快照（按章节号排序）
- 选择快照查看完整状态
- Diff 视图: 对比两个快照的差异
- 回滚按钮

**验收标准:**
- [ ] 快照列表正确
- [ ] Diff 视图可用
- [ ] 回滚按钮触发确认对话框

---

## Task 15.10: Bible 版本管理

**组件:** `BibleVersionManager`

**功能:**
- 显示当前 Bible 版本号
- Changelog 列表
- 查看 Bible 更新提案
- 确认/拒绝更新

**验收标准:**
- [ ] 版本号正确显示
- [ ] 更新提案可确认/拒绝

---

## Task 15.11: Subplot/Hook/Strategy 管理

**组件:** `SubplotManager`, `HookManager`, `StrategyEditor`

**Subplot Manager:**
- 列表视图: 名称、类型、状态、上次推进章节
- 创建/编辑子线对话框
- 汇合点管理

**Hook Manager:**
- 列表视图: 内容、类型、紧迫度、状态
- 筛选: 按类型、状态、优先级
- 手动触发/回收伏笔

**Strategy Editor:**
- 编辑每个策略参数
- 保存/重置

**验收标准:**
- [ ] 子线 CRUD 正确
- [ ] 伏笔列表和筛选正确
- [ ] 策略编辑保存正确

---

## Task 15.12: 整体打磨

**打磨内容:**
- 全局错误处理和 toast 通知
- Loading 状态统一
- 空状态设计（首次使用引导）
- 快捷键支持
- 响应式适配
- 暗色模式支持（可选）

**验收标准:**
- [ ] 所有后端 API 都有对应 UI
- [ ] 渐进式 Bible 生成交互完整
- [ ] 章节全流程可以纯 UI 操作
- [ ] 审查报告清晰可读
- [ ] 无明显 UI bug
