---
name: ship-plan-review
description: "ShipKit hard gate. Reviews implementation plans for completeness and feasibility. Produces review-plan.md. Use after ship-delivery-plan completes."
---

# 计划评审 (Plan Review)

## Overview

计划评审是硬门禁阶段，负责评审 `frontend-plan.md` 和 `backend-plan.md` 两份实施计划，确保任务完整性、依赖合理性、与设计方案的对齐，以及前后端并行开发的可行性。

核心目标：
- 验证任务覆盖所有设计方案中的功能点
- 确保任务粒度适中，每个任务可在一次对话中独立完成
- 验证依赖关系合理，接口对齐任务排在时间线前部
- 产出 `review-plan.md`，记录评审结论与修改要求
- 用户明确批准后方可通过门禁

## When to Use

- `project_scope` 对应的 plan 文档已完成（stage_status: ready）
- 设计评审已通过（review-design.md 的 review_status: approved）
- 准备进入实施阶段前的最后检查点

## When NOT to Use

- 计划文档尚未完成 —— 等待计划阶段完成
- 设计评审未通过 —— 先完成 design-review
- 仅调整单个任务的优先级 —— 直接修改 plan 文件
- 需求或设计发生重大变更 —— 先更新设计文档并重新通过设计评审

## Gate Protocol

本阶段为 **硬门禁 (Hard Gate)**，遵循以下规则：

1. **不可跳过**：实施计划必须经过评审才能开始编码
2. **必须用户签字**：AI 可以执行评审，但最终通过/拒绝决定权在用户
3. **阻塞后续**：`review_status` 不为 `approved` 时，禁止进入 `ship-build` 阶段
4. **修改后重审**：如果状态为 `revision_needed`，修改后必须重新执行评审流程

### 状态流转

```
pending → approved     (用户确认通过)
pending → rejected     (计划存在根本性问题，需重新规划)
pending → revision_needed  (存在问题，需修改后重审)
revision_needed → pending  (修改完成，重新提交评审)
```

## Delegation Boundary

本阶段的质量门禁检查执行者由 orchestrator 基于 delegation 配置决定：

- `current_context`：主代理直接执行计划评审并写 `review-plan.md`
- `gate_check_subagent`：子代理执行计划评审并直接写正式 `review-plan.md` 草案

配置解释：

- `node_overrides[ship-plan-review]` 优先于 `delegation.default_mode`
- `assistive_subagent` 在本阶段解释为 `gate_check_subagent`
- `parallel_subagent` 在本阶段无效；记录 warning 后回退到 `default_mode`，仍无法解析则回退 `current_context`

约束：

- 子代理可以完整执行 DAG、覆盖、粒度、依赖关系检查，并产出正式 gate 草案
- 若由子代理起草，frontmatter 中的 `review_status` 必须保持 `pending`
- 若由子代理起草，`user_sign_off`、`signed_at` 必须保持为空
- 主代理必须重新读取正式草案、复核检查结果并按需要修订
- 只有主代理可以把 `review_status` 改成 `approved / rejected / revision_needed`
- 子代理不可替用户做 `approved / rejected / revision_needed` 决策

## Scope Adaptation

本阶段根据 `project_scope` 调整评审范围：

| project_scope | 评审文档 | 检查重点 |
|---------------|---------|---------|
| `fullstack` | frontend-plan.md + backend-plan.md | 双侧覆盖 + 依赖对齐 + checkpoint 一致 |
| `backend_only` | backend-plan.md | 后端覆盖 + 依赖合理 + 粒度适中 |
| `frontend_only` | frontend-plan.md | 前端覆盖 + 依赖合理 + 粒度适中 |

入口条件调整：

- `fullstack`：`frontend-plan.md` AND `backend-plan.md` 均 ready
- `backend_only`：`backend-plan.md` ready
- `frontend_only`：`frontend-plan.md` ready

Review Checklist 调整：

- 缺失侧的检查项标记为 `na`（不适用），不计入 pass/fail
- 双侧对齐检查项（checkpoint 一致性、contract task 时间线对齐、循环依赖）在单侧模式下标记为 `na`
- `reviewed_documents` 只列出实际评审的文档

## Review Checklist

评审时必须逐项检查：

```markdown
- [ ] 前端任务覆盖所有页面和组件（frontend-design.md 中的每个页面/组件都有对应任务）
- [ ] 后端任务覆盖所有接口和 Service（backend-design.md 中的每个接口都有对应任务）
- [ ] 任务粒度适中（每个任务可在一次对话中完成，预估 30-120 分钟）
- [ ] 依赖关系合理，无循环依赖（任务 DAG 无环）
- [ ] 接口对齐任务（contract task）在前后端共享时间线前部
- [ ] 每个任务有明确的完成判定标准（Definition of Done）
- [ ] 每个任务包含 `任务目标 / 上下文 / 约束 / 验收 / 输出` 执行简报
- [ ] 任务与 AC 的映射完整（每条验收标准至少被一个任务覆盖）
- [ ] 估时合理（无单任务超过 4 小时，无任务少于 15 分钟）
```

### Task Brief Review Rules

每个任务项必须通过执行简报检查。任一任务缺失以下段落，评为 Major，`review_status` 应为 `revision_needed`：

- `任务目标`：一句话说明当前任务要完成的可交付目标，不写泛泛的“实现功能”。
- `上下文`：包含仓库探索证据、关键代码路径、接口、状态源、数据源或设计文档引用。
- `约束`：列出禁止事项、兼容要求、文件范围或不能破坏的既有行为。
- `验收`：列出任务级验收结果，必须能映射到 AC refs 和 verification command。
- `输出`：说明 build agent 应直接修改代码、更新 evidence，并汇报改动文件。

判定细则：

- `上下文` 只写业务背景、没有代码路径或接口证据，按 Major 处理。
- `约束` 为空或只写“无”，但任务存在兼容/范围限制，按 Major 处理。
- `验收` 与 AC refs 或 verification command 不一致，按 Major 处理；导致 AC 无法覆盖时升级为 Critical。
- `输出` 不能替代 `allowed_files`；若输出要求修改的文件不在 `allowed_files` 中，按 Major 处理。

## Process

```
┌─────────────────────────────────────────────────────────┐
│                  计划评审流程                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 读取 frontend-plan.md + backend-plan.md             │
│       │                                                 │
│       ▼                                                 │
│  2. 读取 review-design.md 确认设计已通过                  │
│       │                                                 │
│       ▼                                                 │
│  3. 构建任务依赖图 (Task DAG)                            │
│       │                                                 │
│       ▼                                                 │
│  4. 验证任务覆盖完整性                                    │
│       │                                                 │
│       ▼                                                 │
│  5. 验证任务粒度与可独立性                                │
│       │                                                 │
│       ▼                                                 │
│  6. 验证依赖关系与执行顺序                                │
│       │                                                 │
│       ▼                                                 │
│  7. 逐项执行 Review Checklist                            │
│       │                                                 │
│       ▼                                                 │
│  8. 汇总问题与修改建议                                    │
│       │                                                 │
│       ▼                                                 │
│  9. 产出 review-plan.md                                 │
│       │                                                 │
│       ▼                                                 │
│ 10. 提交用户审批                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Task Granularity Rules

### 合适粒度的判定标准

| 维度 | 合适 | 过粗 | 过细 |
|------|------|------|------|
| 时间 | 30-120 分钟 | > 4 小时 | < 15 分钟 |
| 文件 | 1-5 个文件变更 | > 10 个文件 | 仅改 1 行 |
| 功能 | 一个完整的可验证功能点 | 多个独立功能混在一起 | 半个功能，无法独立验证 |
| 测试 | 可写 1-3 个测试用例验证 | 需要 10+ 测试才能覆盖 | 无法独立测试 |

### 粒度调整规则

1. **过粗的任务**：按功能边界拆分，确保每个子任务有独立的 Definition of Done
2. **过细的任务**：合并相关任务，避免上下文切换开销
3. **不可分割的大任务**：标注为"复合任务"，内部列出子步骤，但作为一个整体交付

### 可独立验证的判定

每个任务完成后，必须能通过以下至少一种方式验证：
- 运行特定测试用例通过
- 启动应用后可观察到预期行为
- API 调用返回预期响应
- 代码编译/构建通过且无新增 warning

## Dependency Validation Rules

### Rule 1: 接口对齐任务前置

接口对齐任务（定义 TypeScript types / API client / mock data）必须排在前后端各自时间线的前 20%。

```
违规示例：
  Task 1: 实现用户列表页面
  Task 2: 实现用户详情页面
  Task 3: 定义 API types 和 mock
  → 问题：接口对齐任务排在第 3 位，前两个任务无法独立开发

正确示例：
  Task 1: 定义 API types、生成 client、准备 mock data
  Task 2: 实现用户列表页面（使用 mock）
  Task 3: 实现用户详情页面（使用 mock）
```

### Rule 2: 无循环依赖

任务依赖图必须是有向无环图 (DAG)。

```
违规示例：
  Task A depends_on Task B
  Task B depends_on Task C
  Task C depends_on Task A
  → Critical: 循环依赖，无法确定执行顺序

检测方法：对任务依赖图执行拓扑排序，若失败则存在环
```

### Rule 3: 关键路径合理

关键路径（最长依赖链）上的任务数不应超过总任务数的 60%。

```
违规示例：
  10 个任务中有 8 个串行依赖
  → Major: 并行度过低，无法有效利用前后端并行开发优势
```

### Rule 4: 前后端并行可行性

前端和后端的任务时间线应能并行推进，仅在接口对齐点同步。

```
验证方法：
  1. 标记所有"同步点"（前后端都依赖的任务）
  2. 同步点之间的任务应可独立执行
  3. 前端使用 mock 数据开发，后端使用测试驱动开发
```

### Rule 5: 任务与 AC 映射完整

每条验收标准 (AC) 必须至少被一个任务覆盖，每个任务必须关联至少一条 AC。

```
违规示例：
  AC-003: "用户可以导出订单为 CSV"
  所有任务中无一提及导出功能
  → Critical: 验收标准无对应实施任务
```

## Output: review-plan.md (产物结构)

### Frontmatter

```yaml
---
stage: ship-plan-review
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""
reviewed_at: ""
reviewed_documents: ["frontend-plan.md", "backend-plan.md"]
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
---
```

### 核心章节

1. **评审摘要** —— 一段话总结评审结论与整体可行性判断
2. **评审 Checklist** —— 逐项标记通过/未通过
3. **发现的问题** —— 按严重程度分级列出
4. **修改建议** —— 针对每个问题给出具体修改方案
5. **用户签字** —— 用户确认评审结论的签字区域

### 问题严重程度定义

| 级别 | 定义 | 示例 |
|------|------|------|
| Critical | 计划存在根本性缺陷，无法正确实施 | AC 无对应任务；存在循环依赖 |
| Major | 计划可执行但会导致效率低下或返工 | 接口对齐任务未前置；任务粒度过粗 |
| Minor | 计划可执行，但有优化空间 | 估时偏差；描述不够清晰 |

## Anti-Rationalizations

1. **"计划赶不上变化，写那么细没用"** —— 计划不是预测未来，是建立共识。粒度适中的计划让每个任务可独立验证，变化时只需调整局部而非推倒重来。
2. **"前后端联调时再对齐接口"** —— 接口对齐任务前置是并行开发的前提。不前置 = 前端写完了等后端，后端改了前端又要改，联调变成互相等待。
3. **"任务太细会限制开发者发挥"** —— 任务粒度不是限制，是保护。粒度适中意味着每个任务有明确的完成标准，开发者不会在模糊需求中浪费时间。
4. **"估时不准很正常，不用太在意"** —— 单个任务估时可以有偏差，但如果系统性偏差（所有任务都超时 2x），说明粒度或依赖有问题。估时是粒度合理性的信号。
5. **"先开始做，做到哪算哪"** —— 没有计划的实施是最大的浪费。返工成本远高于计划成本。硬门禁存在的意义就是防止"先做再说"的冲动。

## Verification

在标记 `review_status` 之前，必须确认：

```markdown
## 退出检查

- [ ] 已读取并理解 frontend-plan.md 全部任务定义
- [ ] 已读取并理解 backend-plan.md 全部任务定义
- [ ] 已确认 review-design.md 状态为 approved
- [ ] 任务覆盖完整性验证已完成（AC ↔ Task 映射表）
- [ ] 任务依赖图已构建，确认无循环依赖
- [ ] 接口对齐任务已确认排在时间线前部
- [ ] 每个任务的粒度已检查（30-120 分钟范围）
- [ ] 每个任务有明确的 Definition of Done
- [ ] 每个任务执行简报完整且与 `allowed_files`、AC refs、verification command 一致
- [ ] Review Checklist 每项已逐一检查并标注结果
- [ ] 所有发现的问题已按严重程度分级
- [ ] 每个 Critical/Major 问题有具体修改建议
- [ ] review-plan.md 已按模板完整输出
- [ ] 已明确告知用户评审结论，等待用户签字确认
- [ ] Frontmatter 字段已正确填写
```

### review_status 判定规则

| 条件 | status |
|------|--------|
| 存在 Critical 问题 | `rejected` |
| 存在 Major 问题但无 Critical | `revision_needed` |
| 仅有 Minor 问题或无问题 | 可标记 `approved`（用户确认后） |
| 用户明确拒绝 | `rejected` |
