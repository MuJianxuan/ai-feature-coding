---
name: ship-delivery-plan
description: "ShipKit stage. Combines frontend and backend planning into one delivery planning stage. Use after ship-design-review completes."
---

# 交付计划 (Delivery Plan)

## Overview

本阶段将“前端计划”和“后端计划”合并为一个交付计划阶段。它仍然保留两份独立计划产物，但统一在一个 skill 内完成，并在阶段内做双向依赖校对。

保留的产物：
- `frontend-plan.md`
- `backend-plan.md`

核心原则：
- **Contract-First**：接口对齐任务和 checkpoint 先定义
- **Frontend-First Within Stage**：默认先写前端计划，再写后端计划
- **Cross-Checked**：阶段末必须做一次前后端计划一致性校验
- **Project-Explicit**：project_group 需求下，每个任务必须写明目标 `project:`，或在任务标题中显式标明目标项目

## When to Use

- `ship-design-review` 已通过
- `api-contract.md`、`frontend-design.md`、`backend-design.md` 已稳定
- 即将进入 `ship-plan-review`
- `technical_plan_provided` 场景下，仅为 `technical_plan_source.selected_scope` 生成任务，且每个任务可追溯到 selected scope、AC ID 和仓库探索证据

## When NOT to Use

- `ship-design-review` 尚未通过
- 设计文档仍在变化
- 仅有单端工作且无需双侧协同计划
- `technical_plan_provided` 场景下，任务会覆盖未选中技术方案内容

## Stage Contract

本阶段属于单 stage 双产物：

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
- `frontend-plan.md.stage_status = ready`
- `backend-plan.md.stage_status = ready`
- 已完成一次 cross-check，确认 contract task / 依赖 / AC 覆盖一致

## Process

```
1. 读取 review-design.md + api-contract.md + frontend-design.md + backend-design.md
   verify: 上游设计已通过且可用
2. 执行 frontend 子段
   verify: frontend-plan.md ready
3. 执行 backend 子段
   verify: backend-plan.md ready
4. 执行 sync 子段
   verify: 两份计划的 contract task、checkpoint、AC 覆盖与依赖关系一致
5. 写回 task_count 与阶段摘要
   verify: 两份文档 frontmatter 和 meta 索引一致
```

## Delegation Boundary

本阶段属于 `forbidden` 节点，**禁止启动任何子代理**，包括辅助委派与只读支线。

- 阶段内固定顺序保持 `frontend -> backend -> sync`
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
- `ship-plan-review` 继续评审两份计划文档
- `ship-build` 继续消费两份计划文档

## Verification

退出前逐项确认：

```markdown
- [ ] frontend-plan.md frontmatter 已设置 `stage: ship-delivery-plan` 和 `artifact_role: frontend-plan`
- [ ] backend-plan.md frontmatter 已设置 `stage: ship-delivery-plan` 和 `artifact_role: backend-plan`
- [ ] frontend-plan.md 中所有页面/组件已拆解为任务
- [ ] backend-plan.md 中所有业务域/接口已拆解为任务
- [ ] project_group 下所有任务都显式包含 `project:` 或任务标题中的目标项目
- [ ] 两份计划的 contract-first 顺序已明确
- [ ] 两份计划的依赖关系无循环
- [ ] sync 子段已完成，checkpoint 与 AC 覆盖一致
- [ ] 两份文档的 `stage_status` 都已正确置为 `ready`
```
