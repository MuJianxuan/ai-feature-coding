---
name: ai-repo-investigation
description: "AI 仓库证据勘察技能。Activation restricted: use only when the user explicitly names `ai-repo-investigation`, or `ai-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary debugging, repo investigation, root-cause analysis, or design prep."
---

# AI Repo Investigation

## 目标

在写方案或改代码前，先找出真实链路。输出应能支撑后续 `design.md` 和 `tasks.md`，而不是停留在猜测。

## 共享契约

执行前必须遵守 `../ai-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-repo-investigation`，或明确要求使用 AI Feature Workflow 的仓库勘察阶段。
2. `ai-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 debugging / code tracing 自动升级成 AI Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `ai-repo-investigation`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `ai-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `ai-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: ai-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入仓库勘察阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md` 已存在，并包含当前阶段要服务的 scope / acceptance criteria。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `investigation.md` 前后都要检查工作区状态。
- 先查证据再结论；不得用猜测替代文件路径、函数、接口或数据来源。
- 发现需求 scope 与真实代码链路不匹配时，按 contract 的 `Scope change protocol` 记录，不要直接扩大后续设计范围。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 搜索顺序

1. 先确认当前工作目录、项目结构、关键配置和技术栈。
2. 用 `rg` / `rg --files` 找入口、接口、store、DB、测试、相似实现。
3. 顺调用链读文件：入口 -> service/use case -> persistence/API -> event/state -> UI/consumer。
4. 对涉及数据的需求，区分 raw source、aggregated source、cache、derived state。
5. 对涉及协议/API 的需求，核对 request shape、response shape、stream 行为、错误处理、日志和持久化。
6. 对涉及 UI 的需求，核对用户入口、状态来源、刷新触发、loading/error/empty state。

## 记录格式

在 `investigation.md` 中记录：

- 已查文件：路径 + 关键行/函数 + 结论。
- 真实链路：按执行顺序列出。
- 数据来源：source of truth、派生数据、缓存、写入点、读取点。
- 相似实现：可复用模式和不能复用的原因。
- 风险与未知：区分已证实、推断、未验证。
- 对设计的约束：必须保留的兼容性、性能、权限、事务或运行时语义。

## 禁止

- 禁止用“可能”“应该”替代证据。
- 禁止只看前端或只看后端就下结论。
- 禁止发现一个症状后停止排查同类路径。

## 输出

更新 `investigation.md`。如果关键链路、数据来源和已查文件证据齐备，将 frontmatter `stage_status` 标记为 `ready`、`evidence_complete: true`；如果受外部条件阻塞，将 `stage_status` 标记为 `blocked`、`evidence_complete: false` 并写明证据。每次写入 `investigation.md` 都必须同步更新 `updated_at`。输出下一步建议后停止。
