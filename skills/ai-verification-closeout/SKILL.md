---
name: ai-verification-closeout
description: "AI 验证收口技能。Activation restricted: use only when the user explicitly names `ai-verification-closeout`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary testing, verification, QA, release notes, or handoff requests."
---

# AI Verification Closeout

## 目标

证明需求已经按 scope 交付，或清楚说明还剩什么风险和阻塞。验证不是跑一个命令，而是把 acceptance criteria 和实际证据对齐。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-verification-closeout`，或明确要求使用这套 AI feature workflow 的验证收口阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 testing / QA / handoff 自动升级成这套工作流。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `ai-verification-closeout`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `ai-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被工作流路由。此时必须同时收到：
  - `activation_source: ai-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入验证收口阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md`、`design.md` 和 `tasks.md` 已存在。
- `verification.md` 和 `handoff.md` 已由 orchestrator/template 准备好。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `verification.md` / `handoff.md` 前后都要检查工作区状态。
- 验证必须映射 acceptance criteria，失败或未覆盖项必须写入残余风险。
- 本阶段完成后必须停下，输出交付状态和用户最短复核路径；不得自行提交或归档。

## 验证顺序

1. 读取 `requirements.md` 的 acceptance criteria。
2. 读取 `tasks.md`，确认所有 in-scope 任务为 `DONE` 或有明确 `BLOCKED` 说明。
3. 按 `design.md` 的验证策略执行 targeted checks。
4. 对每条验收标准记录证据：命令、日志、截图路径、接口响应摘要、数据查询或手工步骤。
5. 检查相关同类路径是否需要回归。
6. 汇总无法验证的项目和原因。

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

更新 `verification.md` 和 `handoff.md`。验收映射完成时，将 `verification.md` frontmatter `stage_status` 标记为 `complete`；交付摘要、复核入口和残余风险齐备时，将 `handoff.md` frontmatter `stage_status` 标记为 `complete`。输出交付状态后停止。
