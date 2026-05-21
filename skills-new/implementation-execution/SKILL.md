---
name: implementation-execution
description: "编码执行阶段 skill。仅在用户明确点名 `implementation-execution`，或被 `workflow-orchestrator` 路由时使用。适用于基于 `frontend-plan.md`、`backend-plan.md` 和 `task-ledger.md` 执行一个任务、记录交付证据、维护状态与恢复执行。"
---

# Implementation Execution

## 目标

基于计划文档逐项执行代码任务，不擅自扩 scope。

## 输入要求

- `frontend-plan.md stage_status: ready`
- `backend-plan.md stage_status: ready`
- `plan-gate.md gate_status: pass`
- `task-ledger.md` 至少存在一个真实 `TODO` 或 `DOING`

## 执行规则

1. 一次只执行一个任务
2. 先把任务设为 `DOING`
3. 代码、测试、验证证据齐全后才能设为 `DONE`
4. 发现 scope 扩大时停止并回流
5. 启动服务前先做端口检查

## 必填交付记录

- 改动文件
- 验证命令或证据
- 结果
- 残余风险

