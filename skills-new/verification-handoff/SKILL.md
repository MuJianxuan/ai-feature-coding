---
name: verification-handoff
description: "验收与汇报阶段 skill。仅在用户明确点名 `verification-handoff`，或被 `workflow-orchestrator` 路由时使用。适用于完成前端测试、后端测试、AC 映射、代码审查接入、实施计划验收汇报和最终 handoff。"
---

# Verification Handoff

## 目标

证明交付已满足 scope，或把未满足项和残余风险明确写出。

## 输入要求

- `task-ledger.md` 中不存在 `TODO` 或 `DOING`
- 前后端计划任务都已有交付记录

## 输出

- `verification.md`
- `handoff.md`

## 必须覆盖

- 后端测试
- 前端测试
- AC 映射
- 手工 smoke
- 残余风险
- 用户最短复核路径

## 代码审查

可复用现有 `coding-code-review` 作为 validation call；若调用，审查结果应写入 `verification.md`。

