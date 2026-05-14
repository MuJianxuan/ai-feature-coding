---
name: coding-verification-closeout
description: "Coding 验证收口技能。Activation restricted: use only when the user explicitly names `coding-verification-closeout`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary testing, verification, QA, release notes, or handoff requests."
---

# Coding Verification Closeout

## 目标

证明需求已经按 scope 交付，或清楚说明还剩什么风险和阻塞。验证不是跑一个命令，而是把 acceptance criteria 和实际证据对齐。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-verification-closeout`，或明确要求使用 Coding Feature Workflow 的验证收口阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 testing / QA / handoff 自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-verification-closeout`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入验证收口阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md`、`requirements.md`、`investigation.md`、`design.md` 和 `tasks.md` 已存在。
- `verification.md` 和 `handoff.md` 已由 orchestrator/template 准备好。
- `discovery.md stage_status: ready` 且 `discovery.md evidence_complete: true`。
- `requirements.md stage_status: ready` 且 `requirements.md evidence_complete: true`。
- `investigation.md stage_status: ready` 且 `investigation.md evidence_complete: true`。
- `design.md stage_status: ready` 且 `design.md evidence_complete: true`。
- `design.md approval_status: approved`，且 `approved_by`、`approved_at`、`approval_evidence` 已补齐。
- `tasks.md stage_status: ready` 且 `tasks.md evidence_complete: true`。
- `task_count` 与真实任务数量一致。
- 不存在 `TODO` 或 `DOING` 任务；仍有未执行任务时回到 `coding-implementation-execution`。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `verification.md` / `handoff.md` 前后都要检查工作区状态。
- 验证必须映射 acceptance criteria，失败或未覆盖项必须写入残余风险。
- 需要启动服务或预览时，必须按 contract 的 `Service startup and port-check protocol` 记录端口、进程、日志和停止方式。
- 本阶段完成后必须停下，输出交付状态和用户最短复核路径；不得自行提交或归档。

## 验证顺序

1. 读取 `discovery.md` 的关键问题、方案方向和外部调研结论，确认验收没有遗漏早期澄清出的边界。
2. 读取 `requirements.md` 的 acceptance criteria。
3. 读取 `investigation.md` 的真实调用链、数据来源、相似实现、风险与未知，确认验证覆盖 source of truth 而不是只验证派生表现。
4. 读取 `tasks.md`，确认所有 in-scope 任务为 `DONE` 或有明确 `BLOCKED` 说明。
5. 按 `design.md` 的验证策略，并结合 `investigation.md` 的真实链路和数据来源，执行 targeted checks。
6. 对每条验收标准记录证据：命令、日志、截图路径、接口响应摘要、数据查询或手工步骤。
7. 检查相关同类路径是否需要回归。
8. 汇总无法验证的项目和原因。

## 文档更新

`verification.md` 记录：

- 验收标准映射表
- 执行过的命令和结果
- 手工验证步骤
- 未覆盖场景
- 回归风险

`handoff.md` 记录：

- 交付摘要
- 变更文件和影响范围
- 配置、SQL、部署或数据操作
- 用户复核入口
- 后续建议

## 完成定义

- in-scope acceptance criteria 都有验证结论。
- 失败或未覆盖项不能被隐藏，必须写入残余风险。
- 如果需要用户验收，给出最短复核路径，不要求用户自行翻找。

## 输出

更新 `verification.md` 和 `handoff.md`，每次写入都必须同步更新对应 frontmatter 的 `updated_at`。只有所有 in-scope acceptance criteria 都有真实验证证据且结果为 `PASS` 时，才将 `verification.md` frontmatter `stage_status` 标记为 `complete`、`evidence_complete: true`；存在 `FAIL`、`BLOCKED`、未覆盖项或无法解释的验证缺口时，保持或更新为 `stage_status: draft/blocked`、`evidence_complete: false`，并在正文写明证据和残余风险。交付摘要、变更范围、用户复核入口、验证结论和残余风险齐备时，将 `handoff.md` frontmatter `stage_status` 标记为 `complete`、`evidence_complete: true`；否则保持 `evidence_complete: false`。输出交付状态后停止。
