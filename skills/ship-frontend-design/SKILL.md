---
name: ship-frontend-design
description: "ShipKit stage. Designs frontend architecture based on UI/UX prototypes with page-API mapping. Use after ship-contract completes."
---

# 前端技术方案 (Frontend Design)

## Overview

前端技术方案阶段基于 UI/UX 设计稿（Figma / 墨刀 / 原型图）、tech-research.md 的项目事实发现和 api-contract.md，设计前端的整体架构与实现路径。

核心目标：
- 建立"页面-组件-接口"三层映射，确保设计可落地
- 基于真实的 UI/UX 设计稿规划组件结构与状态流向
- 基于 `Existing Surface Inventory` 区分复用、扩展、新增或避免触碰的页面、组件、store、API client
- 产出可直接拆解为开发任务的前端方案
- 明确路由、权限、状态管理等横切关注点

产出物：`frontend-design.md`

## When to Use

- api-contract.md 已完成且 stage_status 为 ready
- 已有 UI/UX 设计稿（Figma / 墨刀 / 原型图）或可访问的设计资源；上游 `ship-shape` 产出的 `design-brief.md` + `resource/wireframes/` 也视为可用 UIUX 资料
- 需要为前端开发拆解出明确的页面与组件结构
- 涉及前端状态管理、路由、权限等架构决策

## When NOT to Use

- api-contract.md 尚未完成 —— 接口未定无法做映射
- 没有任何 UI/UX 设计资料 —— 必须先要求用户提供设计稿，或回到 UIUX Material Gate / `ship-shape` 生成线框并确认
- 纯后端项目 —— 跳过本阶段直接进入后端设计
- 仅是已有页面的样式微调 —— 直接进入实现阶段

## UI/UX-Driven Design Philosophy

前端设计的核心原则：**设计稿是事实源，不能凭空想象页面**。

```
错误模式：根据需求文档"想象"页面 → 与设计师对不上
正确模式：从设计稿出发 → 反推组件结构 → 映射到接口 → 拆解开发任务
```

如果没有设计稿：
1. 优先要求用户提供 Figma / 墨刀 / 截图
2. 若用户表示"按你的理解做"，回到 UIUX Material Gate / `ship-shape` 产出线框图（wireframe）并获取确认
3. 不可在没有任何视觉依据时直接开始组件设计

## Diagram Guidance

复杂前端建议使用 PlantUML source 写入 Markdown 辅助评审，不要求渲染图片入库；简单项目不强制画图，可合并章节或写明“不适用 + 原因”。图示只辅助用户流、页面/API 顺序和状态流，不能替代 UI evidence，也不能在没有设计稿时假装页面事实已定稿。

推荐图类型：
- activity diagram：表达多步骤表单、审批、支付、导入导出等用户流和异常流
- sequence diagram：表达 Page / API / store / router 的调用顺序
- component diagram：表达页面、组件、状态 owner、server state cache 和共享 store 关系

推荐触发条件：
- 多步骤表单、审批/支付/导入导出、复杂错误恢复
- 复杂权限、组织层级、数据不可见或资源存在性不能泄露
- 多页面共享状态、实时刷新、离线/弱网、乐观更新
- Page-API Mapping 仅靠表格难以理解调用顺序或异常路径

每张图下方必须补充：范围、参与方、关键路径、至少一个关键异常路径、权限路径或未授权分支、未覆盖范围、一致性检查。图中的页面、用户操作、状态、接口必须与 Page Tree、Page-API Mapping、UI State Matrix 和 State / Data Flow 一致。

## Delegation Boundary

本阶段是少数允许**拥有正式产物**的并行阶段之一。

- 当 `api-contract.md.stage_status = ready` 且 UI/UX 资料可访问时，可由子代理独立拥有并产出 `frontend-design.md`
- 允许与 `ship-backend-design` 并行执行，但两者只能共享 `api-contract.md`、`requirements.md` 和 `spec_context`，不可互改对方正式产物
- `parallel_subagent` 仅作用于当前节点；允许只启动前端设计，不要求与后端成对启动
- `assistive_subagent` 在本阶段无效；若 `ask_on_parallel_stage = false` 且没有显式 `node_overrides[ship-frontend-design] = parallel_subagent`，则回退 `current_context`
- 子代理仍不得推进 `ship-design-review`，正式阶段切换由 orchestrator 统一收口
- 本阶段只消费 workspace `spec_root` 下的规范，不从 `meta.yml.projects` 预设前后端角色；项目是否包含 UI / page / component 必须基于 Project Reality First 证据判断
- 当 `meta.yml.scenario: technical_plan_provided` 时，frontend design 必须按 `technical_plan_source.selected_scope` 裁剪：只覆盖 selected scope 相关页面、组件、API client、状态和错误 UX。未选中技术方案内容不得进入本期设计，除非作为依赖风险或 open question 记录。

## Process

```
1. 读取 requirements.md、tech-research.md、api-contract.md
   verify: 已理解 Existing Surface Inventory、Requirement-to-Reality Mapping 和 API contract
2. 收集与索引 UI/UX 设计资料并记录证据等级
   verify: 所有页面的设计稿可访问，Design Evidence Quality 已记录
3. 构建页面树（Page Tree）、复杂用户流、异常流与权限流
   verify: 覆盖 requirements.md 所有用户路径与关键异常路径
4. 加载 ship-spec 约束
   verify: 已记录匹配的 `spec_id` 或“无匹配规范”
5. 按原子设计分层规划组件
   verify: 每个组件标注数据来源
6. 编写 Existing Frontend Surface Plan
   verify: 现有页面、组件、store、API client 已标注 reuse / extend / new / avoid / unknown
7. 编写页面-接口映射表与 Page-to-Contract 双向覆盖
   verify: 覆盖所有页面操作、错误码和未消费 contract
8. 设计状态管理方案、状态所有权与 UI State Matrix
   verify: 区分 URL/local/server/global/derived state 与 UI 状态分支
9. 设计路由与权限
   verify: 与 requirements.md 权限模型一致
10. 制定前端非功能方案
   verify: 性能/SEO/无障碍各至少一条
```

### 步骤详解

**Step 1: 收集与索引设计资料**

- 列出所有 Figma / 墨刀 / 原型图链接
- 对图片资源建立 `resource/ui/` 索引
- 对每个页面截图标注页面 ID（与 Page Tree 对应）

**Step 2: 构建页面树**

从 requirements.md 的用户路径反推：
- 列出所有路由路径
- 标注每个页面的访问权限
- 区分公开页面、登录后页面、特定角色页面

**Step 3: 加载 ship-spec 约束**

- 先读 `.docs/spec/INDEX.md`，优先从 `frontend / shared` 分类选择候选 spec
- 基于 `tech-selection.md` 的技术栈标签、`requirements.md` 的 domain 信息和涉及文件匹配规范
- 规范匹配边界固定为 workspace `spec_root`
- 将命中的 `spec_id` 记录到 `frontend-design.md.referenced_spec_ids`
- 无匹配规范时显式写“无匹配规范”，并把 warning 写入 `spec_warnings`
- 若 INDEX 与 frontmatter 不一致，记录 warning，默认 Warn Then Continue

**Step 4: 组件分层（Atomic Design）**

```
atoms      → Button / Input / Icon
molecules  → SearchBar / FormField / Card
organisms  → Header / Sidebar / TodoList
templates  → DashboardLayout / AuthLayout
pages      → HomePage / TodoListPage
```

**Step 5: 页面-接口映射（核心产物）**

这是前端方案最关键的产物，必须详尽完整。

**Step 6-8: 横切关注点**

状态管理、路由、性能、无障碍均需明确决策与依据。

## Page-API Mapping Protocol

页面-接口映射表是前端方案的核心交付物，规则如下：

### 映射粒度

每个**用户操作**都必须有一行映射，包括：
- 页面加载（onMount）
- 表单提交
- 按钮点击
- 滚动加载更多
- 路由切换
- 定时刷新

### 映射表格式

```markdown
| 页面 | 用户操作 | 触发时机 | 调用接口 | 请求参数 | 响应处理 | 错误处理 |
|------|----------|----------|----------|----------|----------|----------|
| TodoListPage | 加载列表 | onMount | GET /api/v1/todos | page=1&pageSize=20 | 渲染列表 | 显示错误 toast |
| TodoListPage | 创建待办 | 点击新建按钮 | POST /api/v1/todos | { title, description } | 新增到列表头 | 高亮错误字段 |
| TodoListPage | 删除待办 | 点击删除按钮 | DELETE /api/v1/todos/:id | id | 从列表移除 | 显示错误 toast |
```

### 完整性检查

- 每个页面至少有一行映射（包括纯展示页面也要标注 onMount）
- 每个接口在 api-contract.md 中至少被一个页面引用
- 接口与页面的映射关系双向一致
- 页面操作调用的接口必须存在于 api-contract.md；api-contract.md 中面向前端的接口必须至少有一个页面操作消费，或说明是非前端 consumer
- 错误码、loading、empty、error、permission denied 等 UI 状态必须纳入覆盖检查

反向覆盖建议表：

```markdown
| 页面操作 | 使用接口 | contract 是否存在 | 错误码是否覆盖 | loading/empty/error 是否设计 |
|---|---|---|---|---|
```

## Component Design Rules

### 组件分类原则

| 层级 | 职责 | 是否含业务逻辑 | 示例 |
|------|------|----------------|------|
| atoms | 最小 UI 单元 | 否 | Button, Input |
| molecules | 简单组合 | 否 | SearchBar, Card |
| organisms | 业务区块 | 是 | TodoList, OrderTable |
| templates | 页面骨架 | 否 | DashboardLayout |
| pages | 页面容器 | 是 | TodoListPage |

### 数据来源标注

每个组件必须明确标注数据来源：

```markdown
### TodoList (organism)
- **数据来源**：
  - props: 无
  - store: useTodoStore (todos, loading, error)
  - API: 通过 store 间接调用 GET /api/v1/todos
- **触发的接口**：DELETE /api/v1/todos/:id（删除按钮）
- **关联页面**：TodoListPage
```

### 组件复用边界

- 同一组件被 ≥3 个页面使用 → 抽到 `components/shared/`
- 仅被 1 个页面使用 → 放在该页面目录下
- 明确禁止在 atoms/molecules 中调用 API

## Output: frontend-design.md

编写前先读取 [`references/frontend-design-template.md`](./references/frontend-design-template.md)。

使用规则：
- 模板是写作引导，不是 rigid schema；章节顺序可调整，不适用章节可裁剪
- 模板中的“必答问题”必须被显式回答；若当前项目不适用，需写明原因
- `frontend-design.md` 仍以本文件定义的 frontmatter、stage_status 和 verification 要求为准

### Frontmatter

```yaml
---
stage: ship-frontend-design
stage_status: draft  # draft / ready
updated_at: ""
evidence_complete: false
spec_checked_at: ""
referenced_spec_ids: []
spec_warnings: []
---
```

### 推荐覆盖点

以下内容是推荐覆盖点，不要求固定章节顺序；可按项目复杂度合并或拆分，但需确保模板中的必答问题有对应答案。

#### 1. 前端架构概览
- 框架选择（React / Vue / Svelte）及版本
- 路由方案（React Router / Next.js App Router / Vue Router）
- 状态管理（Redux / Zustand / Pinia / Context）
- 构建工具（Vite / Next.js / Webpack）
- 样式方案（Tailwind / CSS Modules / styled-components）
- UI 组件库（shadcn/ui / Ant Design / Element Plus）

#### 2. 页面树（Page Tree）

```
/                    → HomePage         (公开)
/login               → LoginPage        (公开)
/register            → RegisterPage     (公开)
/todos               → TodoListPage     (需登录)
/todos/:id           → TodoDetailPage   (需登录)
/admin               → AdminLayout      (需管理员)
  /admin/users       → UserManagePage   (需管理员)
```

#### 3. 组件清单（按原子设计分层）

```markdown
### Atoms
- Button (variants: primary/secondary/ghost)
- Input (types: text/password/number)
- Icon (基于 lucide-react)

### Molecules
- SearchBar = Input + Button
- FormField = Label + Input + ErrorMessage

### Organisms
- TodoList - 数据来源: useTodoStore - 触发接口: DELETE /api/v1/todos/:id
- TodoForm - 数据来源: 内部 state - 触发接口: POST /api/v1/todos

### Templates
- DashboardLayout = Header + Sidebar + Outlet
- AuthLayout = LogoBanner + Outlet

### Pages
- TodoListPage = DashboardLayout + TodoList + TodoForm
```

#### 4. Referenced Specs / Constraints
- 引用的 `spec_id` 列表
- 对当前方案生效的关键约束
- 若无匹配规范，显式记录原因和 warnings

#### 4.1 Existing Frontend Surface Plan

来自 `tech-research.md` 的现有前端 surface 必须逐项处理，避免把已有页面/组件重复新建：

```markdown
| Surface | Existing Item | Path / Source | Relation | Plan | Risk / Open Question |
|---|---|---|---|---|---|
| Page | UserProfilePage | src/pages/user/Profile.tsx | extend | 增加编辑入口与保存态 | 头像字段 owner 待确认 |
| API client | userApi.getProfile | src/api/user.ts | reuse | 新增 updateProfile 方法 | 需保持现有缓存 key |
```

Relation 建议使用：`reuse`、`extend`、`replace`、`new`、`avoid`、`unknown`。

#### 5. 页面-接口映射表（核心产物）

完整列出每个页面的每个用户操作对应的接口调用。

#### 5.1 User Flow Diagram / Diagrams

复杂用户流建议补充 PlantUML activity / sequence / component diagram，并在图下说明范围、参与方、关键路径、异常路径、权限路径、未覆盖范围、一致性检查。图示不替代 UI evidence。

#### 5.2 Page-to-Contract Bidirectional Coverage

```markdown
| 页面操作 | 使用接口 | contract 是否存在 | 错误码是否覆盖 | loading/empty/error 是否设计 |
|---|---|---|---|---|
```

#### 5.3 Cross-Document Traceability Matrix

```markdown
| Domain ID | AC ID | Contract | Frontend Page/Action | UI State / Error UX | Test Focus |
|---|---|---|---|---|---|
```

#### 5.4 Test Focus / Verification Scenario

Test Focus 应能直接输入后续 delivery plan 和 verification 阶段，按 page action、UI state、permission UX、error UX 写清场景与预期结果。

```markdown
| Domain ID | AC ID | Design Surface | Scenario | Expected Result | Evidence |
|---|---|---|---|---|---|
```

#### 6. 状态管理方案
- 全局状态：用户信息、认证 token、全局通知
- 局部状态：表单数据、UI 临时状态
- 服务端状态：API 数据缓存（推荐 React Query / SWR）
- 数据流向图：用户操作 → 组件 → Store/Hook → API → Store 更新 → 组件重渲染

#### 6.1 UI State Matrix

至少提示 initial、loading、empty、error、partial success、optimistic、permission denied、offline；不适用项写明原因。

```markdown
| 页面 | 状态 | 触发条件 | UI 表现 | 可执行操作 |
|---|---|---|---|---|
```

#### 6.2 Frontend Data Ownership

```markdown
| 状态 | Owner | 存储位置 | 更新来源 | 是否持久化 | 不变量 |
|---|---|---|---|---|---|
```

#### 7. 路由与权限设计
- 路由守卫机制（公开 / 已登录 / 特定角色）
- Token 存储与刷新策略
- 401 / 403 的统一处理

#### 7.1 Permission UX

覆盖未登录、无权限、数据不可见、操作被禁用、资源不存在但不能泄露存在性。

```markdown
| 权限场景 | 页面/组件表现 | 接口错误 | 前端处理 |
|---|---|---|---|
```

#### 8. UI/UX 设计资料索引
- Figma 链接（含具体页面锚点）
- 墨刀 / 截图清单
- 设计系统引用（设计 token / 颜色 / 间距）
- 组件库映射（设计稿组件 → 代码组件）

#### 8.1 Design Evidence Quality

证据等级：`high` = Figma final design / design system / 完整交互说明；`medium` = 截图 / 原型 / 局部设计稿；`low` = wireframe / 用户口述 / 暂存假设。低证据等级不能假装已定稿。

```markdown
| 页面 | 证据等级 | 来源 | 缺失信息 | 采用假设 |
|---|---|---|---|---|
```

#### 9. 前端非功能方案
- **性能**：路由懒加载、图片懒加载、虚拟列表、防抖节流
- **SEO**：SSR / SSG 决策、meta 标签、sitemap
- **无障碍**：语义化 HTML、ARIA 属性、键盘导航、对比度
- **国际化**：i18n 方案、文案管理
- **响应式**：断点定义（mobile/tablet/desktop）

#### 9.1 Accessibility / Responsive Detail

```markdown
| 页面/组件 | Keyboard | Screen Reader | Focus | Contrast | Mobile Behavior |
|---|---|---|---|---|---|
```

重点覆盖 Modal、Dropdown、Table、Form、Toast、Date picker、Drag and drop 等关键组件。

#### 9.2 Analytics / Performance Budget / Accessibility Tests

- Analytics events：关键页面进入、关键操作提交、失败原因、转化漏斗
- Performance budget：首屏、交互延迟、列表渲染规模、bundle 分包
- Accessibility tests：键盘路径、focus trap、screen reader label、contrast

### stage_status 流转规则

- `draft`：页面树或映射表不完整，存在未对齐的设计资料
- `ready`：页面树覆盖所有用户路径，映射表覆盖所有用户操作，可进入设计评审

### evidence_complete 判定标准

- 每个页面有可访问的 UI/UX 设计资料
- Design Evidence Quality 已区分 high / medium / low，低证据等级未被当作定稿
- 已记录 `referenced_spec_ids` 或“无匹配规范”
- 已消费 `tech-research.md` 的 Existing Surface Inventory，并区分复用、扩展、新增或避免触碰的前端 surface
- 映射表覆盖所有页面的所有用户操作
- 每个接口在映射表中至少被一个页面引用
- 状态管理与路由权限方案明确

## Anti-Rationalizations

1. **"先按需求文档想象页面，等设计稿出来再调整"** —— 没有设计稿就开始的设计大概率推翻重做。先要求设计稿，或先产出线框图获取确认。
2. **"组件之后再分层，先把页面写出来"** —— 不分层会导致后期复用时被迫重构。先分层成本低，事后重构成本高 5 倍。
3. **"页面-接口映射太繁琐，注释里写一下就行"** —— 映射表是前后端联调的依据，是测试用例的来源。注释里的信息不可被检索、不可被工具消费。
4. **"状态管理用最简单的就行"** —— "简单"取决于场景。表单状态用全局 store 是过度设计，跨页面共享数据用 props drilling 是欠设计。必须基于实际数据流向决策。
5. **"无障碍不重要，先做主流程"** —— 无障碍是基础设施而非装饰。事后补无障碍的成本远高于一开始就做。

## Red Flags

- **没有 UI/UX 设计资料就开始组件设计** → 必然返工
- **页面-接口映射表为空或仅有少数页面** → 设计未落地
- **接口被定义但无任何页面调用** → api-contract.md 有冗余接口
- **页面调用未定义的接口** → api-contract.md 有遗漏
- **状态管理方案选择没有依据** → 可能过度设计或欠设计
- **路由设计未考虑权限** → 安全隐患
- **组件层级混乱**（atom 调用 API） → 违反分层原则

## Verification

完成 frontend-design.md 后，执行以下检查：

```
□ 是否有完整的 UI/UX 设计资料索引？
□ 是否已读取 tech-research.md 的 Existing Surface Inventory？
□ 页面 / 组件 / store / API client 方案是否区分 reuse / extend / new / avoid / unknown？
□ 前端规范是否先从 `.docs/spec/INDEX.md` 的 frontend/shared 分类中选择？
□ 页面树是否覆盖 requirements.md 所有用户路径？
□ 组件清单是否按原子设计分层？
□ 每个组件是否标注了数据来源？
□ 页面-接口映射表是否覆盖所有用户操作？
□ api-contract.md 中每个接口是否在映射表中被引用？
□ 状态管理方案是否区分了全局/局部/服务端状态？
□ 路由权限设计是否与 requirements.md 一致？
□ 是否包含性能/SEO/无障碍方案各至少一条？
□ 响应式断点是否定义？
□ frontmatter 字段是否正确填写？
□ 复杂用户流是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的页面 / 用户操作 / 状态 / 接口是否存在于 Page Tree、Page-API Mapping、State Matrix？
□ 每个关键页面是否覆盖 loading、empty、error、permission denied 等状态，或说明不适用原因？
□ 每个页面操作调用的接口是否存在于 api-contract.md？
□ api-contract.md 中面向前端的接口是否至少有一个页面操作消费，或说明是非前端 consumer？
□ 401 / 403 / 404 / 409 等关键错误码是否有对应 UX 处理？
□ 前端设计是否能追溯到 Domain ID、AC ID、Contract、Page Action 和 Test Focus？
```

全部通过后，将 `stage_status` 设为 `ready`，`evidence_complete` 设为 `true`。
