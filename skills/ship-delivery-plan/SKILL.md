---
name: ship-delivery-plan
description: "ShipKit stage. Combines frontend and backend planning into one delivery planning stage. Use after ship-design-review completes."
---

# 交付计划 (Delivery Plan)

## Overview

本阶段将实现计划统一收敛到一个交付计划阶段。`fullstack` 保留前后端两份独立计划产物并做双向依赖校对；`backend_only` / `frontend_only` 只产出对应侧 plan。

产物按 `project_scope` 裁剪：
- `fullstack`：`frontend-plan.md` + `backend-plan.md`
- `backend_only`：`backend-plan.md`
- `frontend_only`：`frontend-plan.md`

核心原则：
- **Contract-First**：接口对齐任务和 checkpoint 先定义
- **Scope-Aware Order**：fullstack 默认先写前端计划，再写后端计划；单侧 scope 只写对应计划
- **Cross-Checked**：fullstack 阶段末必须做一次前后端计划一致性校验；单侧 scope 不执行双侧 sync
- **Project-Explicit**：project_group 需求下，每个任务必须写明目标 `project:`，或在任务标题中显式标明目标项目

## When to Use

- `ship-design-review` 已通过
- `pipeline_mode: standard`，即使是 `backend_only` / `frontend_only`，也仍使用本阶段产出对应侧 plan
- `api-contract.md` 和 `project_scope` 对应的设计文档已稳定
- 即将进入 `ship-plan-review`
- `technical_plan_provided` 场景下，仅为 `technical_plan_source.selected_scope` 生成任务，且每个任务可追溯到 selected scope、AC ID 和仓库探索证据

## When NOT to Use

- `ship-design-review` 尚未通过
- 设计文档仍在变化
- `pipeline_mode: fast-track`，且已改用 `fast-track-tasks.md` 作为 build 任务事实源
- `technical_plan_provided` 场景下，任务会覆盖未选中技术方案内容

## Stage Contract

本阶段属于单 stage、多产物按 scope 裁剪：

1. **frontend 子段**
   - 产出 `frontend-plan.md`
   - frontmatter:

```yaml
---
stage: ship-delivery-plan
artifact_role: frontend-plan
stage_status: draft
updated_at: ""
evidence_complete: false
task_count: 0
---
```

2. **backend 子段**
   - 产出 `backend-plan.md`
   - frontmatter:

```yaml
---
stage: ship-delivery-plan
artifact_role: backend-plan
stage_status: draft
updated_at: ""
evidence_complete: false
task_count: 0
---
```

阶段退出条件：
- `fullstack`：`frontend-plan.md.stage_status = ready`，`backend-plan.md.stage_status = ready`，并已完成一次 cross-check，确认 contract task / 依赖 / AC 覆盖一致
- `backend_only`：`backend-plan.md.stage_status = ready`
- `frontend_only`：`frontend-plan.md.stage_status = ready`

## Process

```
1. 读取 review-design.md + api-contract.md + `project_scope` 对应的设计文档
   verify: 上游设计已通过且可用
2. 按 `project_scope` 执行对应子段
   verify: 对应 plan ready
3. fullstack 执行 sync 子段；单侧 scope 跳过 sync 并记录 na
   verify: fullstack 两份计划的 contract task、checkpoint、AC 覆盖与依赖关系一致；单侧 scope 无 sync blocker
4. 写回 task_count 与阶段摘要
   verify: 实际产出的 plan frontmatter 和 meta 索引一致
```

## Delegation Boundary

本阶段属于 `forbidden` 节点，**禁止启动任何子代理**，包括辅助委派与只读支线。

- 阶段内固定顺序保持 `fullstack: frontend -> backend -> sync`；`backend_only` 只执行 backend；`frontend_only` 只执行 frontend
- 可在当前上下文中参考前一份计划来完善后一份计划，不得拆出任何子代理去起草、审计或收集阶段内材料
- `sync` 子段是本阶段的核心收敛动作，必须由主上下文统一完成
- 只有主上下文可以写回 task_count、`stage_status` 和阶段摘要

## Scope Adaptation

本阶段根据 `project_scope` 调整产物和子段序列：

| project_scope | 产物 | 子段序列 | current_part 值域 |
|---------------|------|---------|------------------|
| `fullstack` | frontend-plan.md + backend-plan.md | frontend → backend → sync | frontend / backend / sync |
| `backend_only` | backend-plan.md | backend | backend |
| `frontend_only` | frontend-plan.md | frontend | frontend |

退出条件调整：

- `fullstack`：两份 plan 均 ready + sync 完成
- `backend_only`：`backend-plan.md` ready（无 sync 需求）
- `frontend_only`：`frontend-plan.md` ready（无 sync 需求）

单侧模式下：

- 不产出缺失侧的 plan 文件
- 不执行 sync 子段（无双侧对齐需求）
- `meta.yml` 中缺失侧的 task_count 保持 0
- Delegation 仍为 `forbidden`（单侧计划仍由主上下文统一完成）

technical_plan_provided 裁剪规则：

- 只为 selected scope 生成 `frontend-plan.md` / `backend-plan.md` 或单侧 plan。
- 未选中内容（未选中技术方案章节、接口、模块或片段）不得生成任务；若是前置依赖，只能记录为 risk / open question 或依赖说明。
- 每个 task 必须同时引用 AC ID、selected scope 或 technical source、仓库探索证据、`allowed_files` 和 verification command。
- task 的 `scope` 字段必须能说明它如何落在 selected scope 内。

## Task Item Contract

每个任务项必须同时包含机器可检字段和面向 `ship-build` 的执行简报。机器字段用于 validator / preflight，执行简报用于让 build agent 明确目标、上下文、边界和验收。

标准格式：

```markdown
### FE-AUTH-001: 新增登录信息
- status: TODO
- project: web
- scope: 登录状态恢复
- allowed_files:
  - src/store/auth.ts
- depends_on:
- ac_refs:
  - AC-AUTH-001
- contract_refs:
  - GET /api/me
- verification_command: pnpm test
- done_evidence:
  - pending

任务目标：
新增登录信息。

上下文：
前端是 React，登录状态在 src/store/auth.ts。后端接口是 GET /api/me。仓库探索证据必须写明具体代码路径、接口、状态源或数据源。

约束：
不要改后端接口。不要重写鉴权系统。保留现有 localStorage key。

验收：
pnpm test 通过。刷新页面后不再跳回登录页。未登录用户仍然正常跳转登录页。

输出：
直接修改 allowed_files 中列出的代码，并说明改了哪些文件。
```

强制规则：

- `任务目标 / 上下文 / 约束 / 验收 / 输出` 五个段落缺一不可。
- `上下文` 必须包含仓库探索证据，不能只写需求背景。
- `约束` 必须列出禁止改动、兼容要求或范围边界；没有特殊约束时也要写“无额外约束，仍遵守 allowed_files”。
- `验收` 必须能回到 AC refs 和 verification command。
- `输出` 必须说明 build 完成后要直接修改代码、更新 evidence，并汇报改动文件。
- `allowed_files` 仍是修改范围事实源；`上下文` 中出现的文件不自动进入可修改范围。

## Part 1: Frontend

frontend 子段遵循前端计划规则：

- Contract Tasks 必须排在所有页面/组件任务之前
- 覆盖类型、API layer、Mock、共享组件、页面、集成测试
- 每个任务至少关联一个 AC
- 每个任务必须能看出目标项目；project_group 下优先写 `project: web`
- 每个任务可在一次 AI 对话中完成并验证

`frontend-plan.md` 必须至少包含：

1. 实施概览
2. 接口对齐任务
3. 任务清单（按页面/组件分组）
4. 依赖关系图
5. 执行顺序建议

## Part 2: Backend

backend 子段遵循后端计划规则：

- Infrastructure Tasks 必须排在所有业务任务之前
- 覆盖脚手架、数据库、路由骨架、中间件、业务域、集成测试、契约测试
- 每个任务至少关联一个 AC 或 Domain / API ID
- 每个任务必须能看出目标项目；project_group 下优先写 `project: api`
- 每个任务可在一次 AI 对话中完成并验证

`backend-plan.md` 必须至少包含：

1. 实施概览
2. 基础设施任务
3. 任务清单（按业务域分组）
4. 依赖关系图
5. 执行顺序建议

## Part 3: Sync

sync 子段是新增要求，必须显式检查：

- 前后端 contract tasks 是否都位于时间线前部
- 前端 API client / mock 与后端 endpoint stub/checkpoint 是否对齐
- `ship-build` 所需的联调 checkpoint 是否在两份 plan 中都能找到
- 所有 AC 至少被一侧任务覆盖，关键 AC 需要能映射到前后端协同路径
- 不存在明显互相等待的循环依赖

建议在两份计划中都加入共享 checkpoint，例如：
- `C1`: 基础 URL / 错误格式锁定
- `C2`: 真实接口可替换 mock
- `C3`: 契约一致性确认

## Output Rules

- 不合并成单一 `delivery-plan.md`
- `ship-plan-review` 继续评审 `project_scope` 对应的计划文档
- `ship-build` 继续消费 `project_scope` 对应的计划文档

## Verification

退出前逐项确认：

```markdown
- [ ] `project_scope` 已确认；`fullstack` 检查两份 plan，`backend_only` 只检查 backend-plan.md，`frontend_only` 只检查 frontend-plan.md
- [ ] 实际产出的 plan frontmatter 已设置 `stage: ship-delivery-plan` 和对应 `artifact_role`
- [ ] frontend-plan.md 中所有页面/组件已拆解为任务（非 frontend scope 标记为 `na`）
- [ ] backend-plan.md 中所有业务域/接口已拆解为任务（非 backend scope 标记为 `na`）
- [ ] project_group 下所有任务都显式包含 `project:` 或任务标题中的目标项目
- [ ] 每个任务都包含 `任务目标 / 上下文 / 约束 / 验收 / 输出` 执行简报
- [ ] 实际产出的 plan contract-first 顺序已明确
- [ ] 实际产出的 plan 依赖关系无循环
- [ ] fullstack 已完成 sync，checkpoint 与 AC 覆盖一致；单侧 scope 已将 sync 标记为 `na`
- [ ] 实际产出的 plan `stage_status` 都已正确置为 `ready`
```
