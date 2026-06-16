# Phase 15 Completion — 前端闭环开发计划

> 继承 phase_15.md Task 15.4–15.12 未完成项，目标是让用户能纯 UI 完成项目创建 → 章节 approve 闭环。

## 前置条件

- Phase 0–15 后端已完成（37 API 端点、10 Agent、92 测试通过）
- 前端骨架已搭建（三栏布局、API Client 层、ProjectList 页面）
- 前端组件目录 `ai/` `asset/` `chapter/` `project/` `review/` 为空

## 共享技术栈

| 依赖 | 用途 | 安装 |
|------|------|------|
| `@uiw/react-md-editor` | Markdown 编辑器（带预览） | `npm install @uiw/react-md-editor` |
| `react-diff-viewer-continued` | 状态 Diff 展示 | `npm install react-diff-viewer-continued` |
| 已有 React Query + Zustand | 异步请求 / 状态管理 | — |

### 异步任务轮询模式

所有 AI 操作（plan / draft / polish / review / approve / compile / analyze / generate 等）均为异步任务。前端统一模式：

```tsx
// hooks/useTaskPolling.ts
const { data: task, isLoading } = useQuery({
  queryKey: ['task', taskId],
  queryFn: () => api.getTask(projectId, taskId),
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    return status === 'success' || status === 'failed' ? false : 2000;
  },
  enabled: !!taskId,
});
```

### Toast 通知模式

```tsx
// 已有 uiStore.notify(message, type)
// type: 'info' | 'success' | 'error'
```

---

## Task A.1: 左侧面板实化（资产树 + 章节列表）

### 新增后端端点

**`GET /api/projects/{project_id}/chapters`** — 章节列表

```
Response 200:
[
  {
    "chapter_number": 1,
    "title": "第一章 开端",
    "status": "approved",
    "word_count": 3200
  }
]
```

实现：在 `api/chapters.py` 增加 `list_chapters` 路由，调用 `chapter_storage.list_chapters(project_id)`。

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `AssetTree.tsx` | `components/asset/` | 7 类资产（Bible / 文风 / 章节 / 状态 / 伏笔 / 子线 / 策略）可点击，点击后通过 `uiStore.setSelectedAsset(type, id)` 通知 CenterPanel |
| `ChapterList.tsx` | `components/chapter/` | 调 `GET /chapters` 渲染章节列表，状态色块：planned=灰 / drafted=黄 / reviewed=蓝 / approved=绿 / locked=锁图标 |

### 修改文件

- `LeftPanel.tsx`：替换占位 `<div>` 为 `<AssetTree />` + `<ChapterList />`
- `uiStore.ts`：增加 `selectedAsset: { type: string; id: string } | null` + `setSelectedAsset`
- `api/chapters.ts`：增加 `listChapters(projectId)` 调用

### 验收标准

- [ ] 左侧显示 7 类资产节点，点击后 CenterPanel 切换显示内容
- [ ] 章节列表按 chapter_number 排序，状态图标/颜色正确
- [ ] 无项目选中时显示"请先选择项目"

---

## Task A.2: 项目创建 3 轮向导

### 新增页面

| 页面 | 路由 | 功能 |
|------|------|------|
| `ProjectCreate.tsx` | `/project/new` | 3 步向导 |

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `WizardStyle.tsx` | `components/project/` | Step 1: 用户粘贴文本样本 → 调 `POST /styles/analyze` → 展示返回的 ConditionalRule 列表，用户确认/编辑 → 保存 style_id |
| `WizardBibleDirection.tsx` | `components/project/` | Step 2: 调 `POST /bible/direction` → 渲染 3 个方向变体卡片 → 用户选择 1 个 direction_id |
| `WizardBibleCharacters.tsx` | `components/project/` | Step 3: 调 `POST /bible/characters` → 展示角色概念 → 用户编辑/确认 → 调 `POST /bible/generate` 生成完整 Bible |

### 修改文件

- `App.tsx`：增加 `/project/new` 路由
- `projectStore.ts`：增加 `createProject` action（POST /projects → 拿到 project_id）

### 验收标准

- [ ] 3 步可完整走通：选风格 → 选方向 → 确认角色 → 生成 Bible
- [ ] 每步有 loading spinner，LLM 调用失败显示错误 toast
- [ ] 完成后跳转到 `/project/:id`

---

## Task A.3: 中间章节编辑器 + 状态流转

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `ChapterEditor.tsx` | `components/chapter/` | 用 `@uiw/react-md-editor` 渲染 Markdown，三态 tab（plan / draft / final），approved 章节只读 |

### 修改文件

- `CenterPanel.tsx`：根据 `uiStore.selectedAsset` 切换显示 `ChapterEditor` / 资产详情 / 空状态
- `chapterStore.ts`：增加 `loadChapter(projectId, chapterNumber)` + `updateDraft(projectId, chapterNumber, content)`

### 章节状态进度条

```
planned → drafted → reviewed → approved → locked
  ●────────●─────────●──────────●────────●
```

当前状态高亮，可回退的状态用实心圆，不可达的用空心圆。

### 验收标准

- [ ] 选中章节后，CenterPanel 显示 Markdown 编辑器
- [ ] plan/draft/final tab 可切换，内容为对应 `.md` 文件
- [ ] approved 章节编辑器只读 + 顶部提示"此章节已锁定"
- [ ] 状态进度条正确显示当前状态

---

## Task A.4: 右侧 AI 操作面板真接入

### 新增文件

| 文件 | 位置 | 功能 |
|------|------|------|
| `useTaskPolling.ts` | `hooks/` | React Query hook，轮询任务状态直到 success/failed |
| `TaskProgressBar.tsx` | `components/ai/` | 当前任务进度条 + 状态文字 |

### 修改文件

- `RightPanel.tsx`：全部按钮改为真实 API 调用

### 按钮行为映射

| 按钮 | API 调用 | 启用条件 | 异步 |
|------|---------|---------|------|
| 编译上下文 | `POST /context/compile` | 项目已选 | 是（轮询） |
| 生成规划 | `POST /chapters/{ch}/plan` | 有上下文包 | 是 |
| 生成草稿 | `POST /chapters/{ch}/draft` | status >= planned | 是 |
| 文风润色 | `POST /chapters/{ch}/polish` | status >= drafted | 是 |
| 审查(4维) | `POST /chapters/{ch}/review` | status >= drafted | 是 |
| 确认章节 | `POST /chapters/{ch}/approve` | status >= reviewed | 否（同步） |

### 验收标准

- [ ] 6 个按钮全部正确调用后端 API
- [ ] 异步操作显示进度条 + 自动轮询
- [ ] 操作完成/失败时 toast 通知
- [ ] 按钮根据章节状态自动启用/禁用

---

## Task A.5: 审查报告 4 标签

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `ReviewTabs.tsx` | `components/review/` | 4 个 tab：连贯性 / 质量 / 跨章 / 读者模拟 |
| `FixInstructionList.tsx` | `components/review/` | FixInstruction 列表，按 severity 排序（critical → major → minor），带"应用修复"按钮 |

### 数据源

审查结果从章节目录的 review YAML 文件读取。后端已有 `GET /chapters/{ch}/review`（需确认是否返回 4 类报告）。

### CenterPanel 集成

当 `uiStore.selectedAsset.type === 'review'` 时，CenterPanel 显示 `ReviewTabs`。

### 验收标准

- [ ] 4 个 tab 切换正确，每类审查结果显示对应内容
- [ ] FixInstruction 按 severity 排序
- [ ] "应用修复"按钮触发 polish 流程

---

## Task A.6: 状态 Diff + 快照回滚

### 新增后端端点

**`GET /api/projects/{project_id}/state/snapshots`** — 快照列表

```
Response 200:
[
  {
    "snapshot_id": "snapshot_after_chapter_001",
    "chapter_number": 1,
    "created_at": "2026-06-16T10:00:00Z"
  }
]
```

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `StateDiff.tsx` | `components/asset/` | 用 `react-diff-viewer-continued` 渲染状态变更 diff |
| `SnapshotList.tsx` | `components/asset/` | 快照列表 + "回滚到此"按钮（调 `POST /state/rollback`） |

### CenterPanel 集成

当 `uiStore.selectedAsset.type === 'state'` 时显示 `StateDiff` + `SnapshotList`。

### 验收标准

- [ ] 快照列表正确显示
- [ ] Diff 以行级方式展示变更（增/删/改高亮）
- [ ] 回滚按钮触发确认弹窗 → 调用 rollback API → 成功后 toast + 刷新

---

## Task A.7: Bible 版本 + Subplot/Hook/Strategy 管理

### 新增组件

| 组件 | 位置 | 功能 |
|------|------|------|
| `BibleVersion.tsx` | `components/asset/` | 显示 Bible changelog、当前 version；查看更新提议 / 应用更新 |
| `SubplotTable.tsx` | `components/asset/` | Subplot CRUD 表格（调 `GET/POST/PUT /subplots`） |
| `HookTable.tsx` | `components/asset/` | Hook CRUD 表格（调 `GET/POST/PUT /hooks`） |
| `StrategyForm.tsx` | `components/asset/` | Strategy 编辑表单（调 `GET/PUT /strategy`） |

### CenterPanel 集成

AssetTree 点击对应资产类型时，CenterPanel 切换为对应组件。

### 验收标准

- [ ] Bible 版本历史可查看，更新提议可查看和一键应用
- [ ] Subplot 表格可增/删/改
- [ ] Hook 表格可增/删/改，含 urgency 级别显示
- [ ] Strategy 表单可编辑和保存

---

## Task A.8: 整体打磨

### 全局

| 项目 | 实现 |
|------|------|
| ErrorBoundary | `components/ErrorBoundary.tsx`，包裹 `<App>` |
| 加载骨架 | 各面板数据加载时显示 `<Skeleton />`（用 Tailwind animate-pulse） |
| 空状态 | 无项目 / 无章节时显示引导提示 |
| 键盘快捷键 | ⌘S 保存草稿、⌘↩ 触发当前章节下一步 |
| 响应式 | < 1024px 时左栏收为抽屉（hamburger 按钮） |

### 验收标准

- [ ] API 错误时页面不崩溃，显示友好错误信息
- [ ] 所有加载状态有骨架屏
- [ ] 快捷键生效
- [ ] 窄屏可正常使用

---

## 新增后端端点汇总

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/chapters` | GET | 章节列表（含 status + word_count） |
| `/api/projects/{id}/state/snapshots` | GET | 快照列表 |

现有端点足够覆盖其他所有前端需求，无需额外补充。

## 新增依赖汇总

```
npm install @uiw/react-md-editor react-diff-viewer-continued
```

## 文件清单估算

| 类型 | 新增文件数 | 修改文件数 |
|------|-----------|-----------|
| 前端组件 (.tsx) | ~18 | 4 (LeftPanel, CenterPanel, RightPanel, App) |
| 前端 Hook (.ts) | 2 (useTaskPolling, useKeyboard) | 1 (chapterStore) |
| 后端 API (.py) | 0 | 1 (api/chapters.py) |
| 后端 Service (.py) | 0 | 1 (chapter_service.py — 加 list 方法) |
| 后端测试 (.py) | 1 (test_list_chapters) | 0 |
| 总计 | ~21 新 | ~6 改 |

## 执行顺序

A.1 → A.2 → A.3 → A.4 → A.5 → A.6 → A.7 → A.8

每个子阶段完成后：`npm run build` 0 error + `pytest tests/ -q` 全部通过。