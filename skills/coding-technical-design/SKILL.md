---
name: coding-technical-design
description: "Coding 技术设计技能。Activation restricted: use only when the user explicitly names `coding-technical-design`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary architecture, design, planning, or proposal work."
---

# Coding Technical Design

## 目标

基于 `requirements.md` 和 `investigation.md` 产出能直接拆任务的技术方案。设计必须解释为什么这样改，以及如何验证它真的满足需求。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-technical-design`，或明确要求使用 Coding Feature Workflow 的技术设计阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通技术方案讨论自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-technical-design`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入技术设计阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md`、`requirements.md` 和 `investigation.md` 已存在。
- `discovery.md stage_status: ready`。
- `requirements.md stage_status: ready`。
- `requirements.md evidence_complete: true`。
- `discovery.md evidence_complete: true`。
- `investigation.md stage_status: ready`。
- `investigation.md evidence_complete: true`。
- `discovery.md`、`requirements.md` 和 `investigation.md` 的 `updated_at` 均已写入 ISO 8601 + timezone。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `design.md` 前后都要检查工作区状态。
- 设计必须基于 `discovery.md`、`requirements.md` 与 `investigation.md` 的证据，不得引入无关重构。
- 发现 scope 变化时按 contract 的 `Scope change protocol` 记录并停止，不得把未确认变更直接写进方案。
- 发现影响交付的新澄清问题时，先逐一询问用户；回答影响需求、链路或方案时回流更新上游文档后再继续。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 输入检查

开始前确认：

- `requirements.md` 有可验证 acceptance criteria。
- `discovery.md` 有仓库广扫、必要外部调研、方案方向和关键问题澄清记录。
- `investigation.md` 有真实代码链路和数据来源。
- 阻塞问题不存在，或已被明确标为不会影响当前设计。

## 设计内容

`design.md` 至少包含：

- 方案摘要：一句话说明核心改动。
- 头脑风暴与取舍：基于 discovery / investigation 证据列出可行方案、不可行方案和推荐理由。
- 影响范围：模块、文件、接口、数据表、配置、权限、任务、UI。
- 目标链路：改动后的调用链或数据流。
- API 变更：endpoint、request、response、错误码、兼容性。
- 数据变更：DDL、DML、迁移、回滚、幂等性。
- 状态与并发：事务边界、缓存刷新、stream/event、异步任务。
- 错误处理与日志：异常传播、可观测字段、PII 处理。
- 风险和降级：已知风险、回滚策略、灰度或开关。
- 验证策略：单测、集成、手工验证、数据校验、UI 验证。
- 外部证据引用：如方案依赖第三方库、框架、OpenAI/API 或版本行为，引用 discovery / investigation 中的 Context7 或官方文档结论。

## 决策原则

- 优先沿用仓库已有模式，不引入不必要的新抽象。
- 方案要服务当前 scope，不做无关重构。
- 涉及数据库时，需求目录 `sql/` 先放草案，最终脚本再按项目规范落正式目录。
- 涉及接口或协议时，显式写清兼容对象和 breaking change。

## 输出

更新 `design.md`。如果方案仍依赖未确认业务决策，在文档顶部标记 `DESIGN_BLOCKED`，并将 frontmatter `stage_status` 标记为 `blocked`、`evidence_complete: false`、`approval_status` 标记为 `blocked`；如果设计可直接拆任务，将 `stage_status` 标记为 `ready`、`evidence_complete: true`，但保持 `approval_status: pending`，等待用户明确批准后才能进入 `coding-task-planning`。每次写入 `design.md` 都必须同步更新 `updated_at`。输出下一步建议后停止。
