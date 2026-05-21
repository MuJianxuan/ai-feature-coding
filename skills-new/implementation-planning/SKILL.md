---
name: implementation-planning
description: "实施计划阶段 skill。仅在用户明确点名 `implementation-planning`，或被 `workflow-orchestrator` 路由时使用。适用于将 approved 技术方案拆成 `frontend-plan.md`、`backend-plan.md` 和 `plan-gate.md`，明确依赖、并行边界、测试任务和 task ledger。"
---

# Implementation Planning

## 目标

把技术方案拆成真正可执行的前后端计划，而不是只产出一个笼统 TODO 列表。

## 输入要求

- `solution.md stage_status: ready`
- `solution-gate.md gate_status: pass`

## 输出

- `frontend-plan.md`
- `backend-plan.md`
- `plan-gate.md`
- `task-ledger.md`

## 计划规则

- 前端按页面 / 组件 / 交互切片
- 后端按模块 / API / 数据切片
- 必须显式写依赖关系
- 必须把测试任务写进计划
- `task-ledger.md` 只做执行状态源，不替代详细计划文档

## Gate 通过条件

- 两份计划文档都 `stage_status: ready`
- `plan-gate.md gate_status: pass`
- `task-ledger.md task_count` 与真实任务数量一致

