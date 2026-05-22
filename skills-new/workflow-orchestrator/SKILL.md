---
name: workflow-orchestrator
description: "完整开发工作流总控 skill。仅在用户明确要求使用这套 workflow 或点名 `workflow-orchestrator` 时使用。适用于基于 PRD、原型、UIUX、Figma、墨刀等资料，推进需求评审、技术方案、前后端实施计划、编码执行、测试验收和实施汇报。"
---

# Workflow Orchestrator

## 目标

把一项需求从输入资料推进到可验收交付。该 workflow 采用显式触发、阶段门禁和证据驱动方式运行。

默认工作目录：

```text
.docs/workflows/workflow-YYYYMMDD-short-name/
```

模板位于：

```text
skills-new/workflow-orchestrator/assets/workflow-template/
```

共享契约位于：

```text
skills-new/workflow-orchestrator/WORKFLOW_CONTRACT.md
```

## Activation policy

只允许以下两种启动方式：

1. 用户明确写出 `workflow-orchestrator`
2. 用户明确要求“使用这套完整开发 workflow / 技能工作流”

不满足时：

- 不自动进入该 workflow
- 不创建 `.docs/workflows/` 目录
- 不把普通编码、调试、设计、拆任务请求升级成该 workflow

## 入口模式

### 1. NEW_WORKFLOW

适用：

- 用户给出新的需求资料，但未指定已有工作目录

执行：

1. 从需求主题提取 `short-name`
2. 创建 `.docs/workflows/workflow-YYYYMMDD-short-name/`
3. 从 `assets/workflow-template/` 复制模板
4. 将用户资料移动到创建的需求目录
4. 将用户资料索引到 `source-index.md`
5. 根据阶段推断进入 `product-requirements`

### 2. CONTINUE_WORKFLOW

适用：

- 用户指定已有工作目录
- 用户要求继续某个 workflow

执行：

1. 读取目录内阶段文档
2. 基于 `WORKFLOW_CONTRACT.md` 做 gate 判定
3. 只路由到一个最合适的阶段

### 3. INSPECT_WORKFLOWS

适用：

- 用户要求查看 workflow 状态，但没有指定目录

执行：

1. 列出 `.docs/workflows/` 下目录
2. 汇报每个目录的当前阶段、gate 状态和阻塞
3. 等待用户指定继续对象

### 4. AUDIT_ONLY

适用：

- 用户只想审计当前 workflow 设计和产物是否完整

执行：

1. 只读检查阶段文档
2. 输出缺口、阻塞、下一步建议
3. 不自动推进阶段

## 阶段路由

### `product-requirements`

负责：

- 需求资料吸收
- 仓库现状调研
- 业务域建模
- AC 制定
- `requirements-gate.md`

### `technical-solution`

负责：

- 技术最新信息获取
- 技术选型与架构选型
- `greenfield_project` / `existing_project` 分岔
- 前后端技术方案
- 页面 / API / 数据模型映射
- `solution-gate.md`

### `implementation-planning`

负责：

- `frontend-plan.md`
- `backend-plan.md`
- `plan-gate.md`
- 初始化 `task-ledger.md`

### `implementation-execution`

负责：

- 按 task ledger 一次执行一个任务
- 记录交付证据
- 维护任务状态

### `verification-handoff`

负责：

- 前后端测试
- 验收标准映射
- 代码审查接入
- 实施计划验收汇报
- `handoff.md`

## Gate policy

- 默认一次只推进一个阶段
- gate 未通过时，不得越级进入后续阶段
- 只有用户明确要求连续推进时，才允许在完成当前阶段后继续下一阶段

## 目录结构

参见模板目录。至少包含：

- `source-index.md`
- `requirements.md`
- `requirements-gate.md`
- `tech-research.md`
- `solution.md`
- `solution-gate.md`
- `frontend-plan.md`
- `backend-plan.md`
- `plan-gate.md`
- `task-ledger.md`
- `verification.md`
- `handoff.md`

## 约束

- 文档用中文写，保留 technical English names
- 启动服务前先检查端口和已有进程
- 不删除文件，不做 git 状态变更，除非用户明确许可
- 先查仓库和文档，再问用户

