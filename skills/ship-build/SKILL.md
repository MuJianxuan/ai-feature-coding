---
name: ship-build
description: "ShipKit stage. Executes coding tasks from the `ship-delivery-plan` outputs one at a time. Use after ship-plan-review gate passes."
---

# 编码执行 (Implementation)

## Overview

编码执行阶段负责将 frontend-plan.md 和 backend-plan.md 中的任务逐一转化为可运行的代码。核心原则：**Contract-First Slicing** —— 先实现前后端接口对齐任务，再并行推进各端实现，且一次只执行一个任务，完成后停下等用户确认。

核心目标：
- 严格按 plan 中定义的任务顺序执行，一次一任务
- 每个任务完成后必须通过验证（测试/构建/lint）
- 保持 Scope Discipline，不修改 spec 之外的文件
- 通过 TODO → DOING → DONE 状态流转追踪进度

产物：代码改动 + plan.md 中的任务状态更新

## When to Use

- frontend-plan.md 和 backend-plan.md 已通过 plan-review gate（`stage_status: ready`）
- api-contract.md 已定稿（Contract-First 的前提）
- 开发环境已就绪（依赖安装、数据库初始化等）

## When NOT to Use

- plan 尚未通过评审 —— 回到 `ship-plan-review` 阶段
- 发现需求有重大歧义 —— 回到 `ship-intake` 阶段
- 纯技术调研/方案验证 —— 使用 tech-research 阶段
- 需要修改 API 契约 —— 回到 `ship-contract` 阶段

## Contract-First Execution Order

```
Phase 1: 接口对齐 (Contract Layer) ── 必须最先完成
├── 后端：实现 API endpoint stubs（路由 + 请求/响应 DTO + 类型定义）
├── 前端：实现 API client layer（请求函数 + 类型定义 + Mock 数据）
└── 验证：前后端类型定义与 api-contract.md 完全一致

Phase 2: 前后端并行实现
├── 后端：按 backend-plan.md 任务顺序逐一实现（业务逻辑 + 数据层）
├── 前端：按 frontend-plan.md 任务顺序逐一实现（组件/页面 + 状态管理）
└── 两端可并行，但每端内部仍是一次一任务

Phase 3: 集成联调
├── 替换前端 Mock，对接真实后端
├── 端到端基本路径跑通
└── 异常路径快速 sanity check
```

### 执行顺序的强制规则

1. **Phase 1 必须在所有任务前完成**：契约层是前后端的"握手协议"，先对齐才能并行
2. **同一 Phase 内不跳任务**：plan 中的任务顺序代表了依赖关系，按序执行
3. **跨 Phase 的依赖必须显式标注**：例如前端任务依赖后端的某个 endpoint，需在 plan 中标记 `blocked_by`

## Delegation Boundary

本阶段保持**正式执行串行**。

- 正式编码任务仍遵守“一次一任务”和“单 `DOING` 唯一性”
- 允许子代理承担只读或辅助性工作：
  - 下一个任务的现状阅读与文件清单整理
  - spec 匹配与引用建议
  - 测试/构建/环境预检查
  - 已完成 slice 的证据整理
- 上述辅助节点在 `node_overrides` 中的 canonical `node_id` 固定为：
  - `ship-build.read-next-task`
  - `ship-build.spec-scan`
  - `ship-build.env-precheck`
  - `ship-build.evidence-pack`
- 子代理不得并行推进多个正式编码任务，不得自行把任务状态从 `TODO/DOING` 改为 `DONE/BLOCKED`
- 子代理只返回检查结果、引用建议或证据包，不直接编辑正式 plan / 代码任务记录的 canonical 状态或正文
- 每个 verified slice 完成后，是否继续下一个正式任务仍由用户决定

## Process (单任务执行循环)

```
┌──────────────────────────────────────────────────────┐
│            单任务执行循环（Loop until DONE）           │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 选取下一任务（TODO 中第一个非 blocked 任务）        │
│         │                                            │
│         ▼                                            │
│  2. 状态置为 DOING（同时只能一个任务为 DOING）         │
│         │                                            │
│         ▼                                            │
│  3. 读取任务的"完成判定标准" + 关联文件清单             │
│         │                                            │
│         ▼                                            │
│  4. 读取相关现有代码（不要假设，先看实际）              │
│         │                                            │
│         ▼                                            │
│  5. 编写代码（含必要的注释与类型）                     │
│         │                                            │
│         ▼                                            │
│  6. 运行验证（测试/构建/lint，按任务类型）              │
│         │                                            │
│    ┌────┴────┐                                       │
│    │ 通过？  │                                       │
│    └────┬────┘                                       │
│      Y/ │ \N                                         │
│      ▼  │  ▼                                         │
│  7a.状态  7b.诊断+修复（不退化为模式匹配重试）          │
│   置DONE                                             │
│      │                                               │
│      ▼                                               │
│  8. 在 plan.md 更新状态、追加完成证据链接              │
│      │                                               │
│      ▼                                               │
│  9. 停下，向用户报告并等待确认                         │
│      │                                               │
│      ▼                                               │
│  10. 用户确认 → 回到步骤 1 选取下一任务                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 步骤详解

**Step 1-2: 任务选取与状态置位**
- 从 plan.md 的 TODO 列表选择第一个不被 blocked 的任务
- 立即将该任务的 status 改为 DOING
- 同一 plan 中只能有一个任务处于 DOING（DOING 唯一性）

**Step 3-4: 上下文准备**
- 阅读任务条目中的"完成判定标准"（Acceptance Criteria for Task）
- 阅读"关联文件清单"中列出的所有文件，理解现状
- 如果任务关联了 design 文档章节，读取该章节
- 使用 `ship-spec` hook 匹配 `.docs/spec/*.md`，将命中的 `spec_id` 写入任务的 `spec_refs`
- 若无匹配规范或规范 frontmatter 不合法，记录 warning，但默认继续
- 不要凭记忆或假设直接动手

**Step 5: 编写代码**
- 严格在任务定义的文件范围内修改
- 遵守项目已有的代码风格、命名约定、目录结构
- 必要时编写测试（后端任务建议 TDD，前端组件任务建议先写 stories/snapshot）

**Step 6-7: 验证与修复**
- 按任务类型运行对应验证（见 Verification Per Task）
- 验证失败时进入诊断流程，不要无目的地重试
- 同一错误重复出现 2 次以上，必须停下分析根因

**Step 8: 状态更新与证据留存**
- 在 plan.md 中将任务 status 改为 DONE
- 追加完成证据：测试输出、构建日志、关键文件路径

**Step 9-10: 停下汇报**
- 向用户报告：完成了什么、验证结果、下一个任务是什么
- 等待用户确认后再进入下一任务

## Scope Discipline Rules

1. **只改 spec 之内的文件**：任务条目未列出的文件不动
2. **发现需要改额外文件时停下**：报告给用户，由用户决定是否扩大范围
3. **不顺手重构**：哪怕看到旁边的代码很烂，也不在当前任务里清理
4. **不顺手补功能**：spec 没要求的边界处理，记入"建议"而不是直接写
5. **不修改 plan**：发现 plan 有问题（任务遗漏、依赖错误、判定标准模糊），停下报告，由用户决定是回到 plan 阶段还是局部调整

### Scope Discipline 的边界例外

以下情况算"任务必要工作"，不算越界：
- 修改任务文件时，附带的 import 调整、类型定义补充
- 为了让测试能跑起来，对测试基础设施（fixtures、setup）的最小改动
- 项目级配置文件中明确属于该任务的字段（如新 endpoint 注册到路由表）

## Task Lifecycle (TODO → DOING → DONE)

### 状态定义

| 状态 | 含义 | 进入条件 | 退出条件 |
|------|------|----------|----------|
| TODO | 待执行 | 任务从 plan 创建时初始状态 | 被选中开始执行 |
| DOING | 执行中 | 当前正在编码 | 验证通过且证据齐全 |
| DONE | 已完成 | 验证通过 | 不可逆（除非用户明确要求回滚） |
| BLOCKED | 阻塞 | 依赖任务未完成或外部依赖未就绪 | 阻塞条件解除 |

### 状态记录格式

在 plan.md 中每个任务条目使用 frontmatter 或 inline 标注：

```markdown
### Task FE-001: 实现登录页面骨架
- status: DONE
- assignee: claude
- started_at: 2026-05-22T10:00:00+08:00
- finished_at: 2026-05-22T10:35:00+08:00
- spec_refs:
  - react-query-data-fetching
  - error-handling
- evidence:
  - tests: src/pages/Login.test.tsx (12 passed)
  - build: pnpm build → success
  - files: src/pages/Login.tsx, src/pages/Login.module.css
- notes: ""
```

### DOING 唯一性

- 同一时刻整个 plan 中最多只能有 1 个任务处于 DOING
- 切换任务前必须将当前 DOING 任务推进到 DONE 或显式回退到 TODO
- 中断时（如用户切换需求）必须将 DOING 回退到 TODO 并记录中断原因

## Verification Per Task

不同任务类型对应不同的验证手段。每个任务在 plan 中的"完成判定标准"应明确指定。

### 后端任务验证

| 任务类型 | 验证手段 |
|---------|---------|
| 数据模型 / Migration | 运行 migration + schema 校验 + 单元测试 |
| API endpoint | 路由测试 + 请求/响应类型校验 + 异常路径测试 |
| 业务逻辑 (Service) | 单元测试覆盖正常 + 边界 + 异常 |
| 数据访问层 (Repository) | 集成测试（含 DB 真实交互） |

### 前端任务验证

| 任务类型 | 验证手段 |
|---------|---------|
| 组件 (Presentational) | 单元测试 / Storybook stories / 视觉检查 |
| 页面 / 路由 | 渲染测试 + 路由跳转测试 + 关键交互测试 |
| 状态管理 (Store/Hook) | 单元测试覆盖 action / selector |
| API Client | 类型校验 + Mock 请求测试 |

### 通用最低要求

- `lint` 通过（项目已配置的 linter）
- `typecheck` 通过（如使用 TypeScript / Pyright / mypy 等）
- `build` 通过（前端任务）或 `compile` 通过（编译型语言）
- 新增/修改的代码至少有一个对应的自动化验证

## Resume Protocol (中断恢复)

当会话中断（用户切走、上下文压缩、流程被打断）后恢复执行时：

1. **读取 plan.md** 找到当前 DOING 任务
2. **读取该任务的最近一次 evidence**，确认实际进展到哪一步
3. **运行验证**，确认环境状态与文件状态一致
4. **不要凭印象继续**：如果验证显示部分代码已改但测试未跑，先把验证补齐再继续
5. **如果发现 DOING 任务已经实际完成但状态未更新**，先补齐状态变更再选取下一任务
6. **若 `spec_refs` 缺失**：先重新执行 spec 匹配并把结果补到任务证据，再继续实现

## Anti-Rationalizations

1. **"这个任务跟旁边那个一起做了更高效"** —— 一次一任务是为了让用户能精确审查每一步。批量推进会让 review 失效，最终 bug 反而更多。
2. **"这个改动很小，不用跑测试了"** —— "很小"是错觉的高发区。每个任务都跑验证是纪律，而非建议。
3. **"plan 写得不太对，我直接改成更合理的"** —— plan 是用户和评审过的契约。发现问题停下来报告，不要单方面调整。
4. **"这个文件不在任务里但顺手改一下吧"** —— 顺手改是 scope 蔓延的入口，下次审查时会发现一堆"不知道哪冒出来的"改动。
5. **"测试失败可能是 flaky，再跑一次"** —— 重试 1 次可以接受，超过 1 次必须诊断根因。flaky 测试是债，不是借口。

## Red Flags

以下情况出现时，必须暂停并处理：

- **同一任务验证失败 ≥ 3 次**：停下分析根因，可能是任务定义有问题或环境问题
- **修改文件超出任务清单 50%**：scope 已经偏离，回到 plan 检查任务粒度
- **plan 中的任务依赖关系出现循环**：plan 有结构性问题，回到 plan-review
- **Phase 1（契约层）尚未完成就开始 Phase 2 任务**：契约未对齐会导致后期大量返工
- **DOING 任务超过 1 个**：状态机被破坏，必须先收敛
- **发现 api-contract.md 与实际需求不符**：停下回到 `ship-contract` 阶段
- **测试通过但用户验收失败**：测试与 AC 不对齐，回到 `ship-verify` 阶段补齐

## Verification (退出 Checklist)

任务标记 DONE 之前逐项确认：

```markdown
## 任务退出检查 (Per Task)

- [ ] 完成判定标准的每一条都已满足
- [ ] 自动化验证（test / build / lint / typecheck）全部通过
- [ ] 改动文件在任务清单范围内
- [ ] 关键改动有对应的测试覆盖
- [ ] plan.md 中状态已更新为 DONE，evidence 已填写
- [ ] 任务条目已记录 `spec_refs`（无匹配规范时显式写明）
- [ ] 无未提交的临时调试代码（console.log / TODO 占位）
- [ ] 无 spec 之外的"顺手改动"

## 阶段退出检查 (整个 Implementation 结束)

- [ ] frontend-plan.md 中所有任务为 DONE
- [ ] backend-plan.md 中所有任务为 DONE
- [ ] Phase 1（契约层）实现与 api-contract.md 一致
- [ ] 端到端关键路径已跑通（即使是手动验证）
- [ ] 已知的偏离/妥协已记录在 plan.md 的 notes 字段
- [ ] 相关规范已加载并在任务证据中留痕（如适用）
- [ ] 准备进入 `ship-verify` 阶段（或 `ship-verify` 已与 `ship-build` 同步完成）
```
