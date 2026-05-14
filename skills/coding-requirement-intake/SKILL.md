---
name: coding-requirement-intake
description: "Coding 需求澄清技能。Activation restricted: use only when the user explicitly names `coding-requirement-intake`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary requirement clarification or feature discussion."
---

# Coding Requirement Intake

## 目标

基于已经完成的 `investigation.md`，把用户输入变成可执行、可验证、可追踪的 `requirements.md`。不要急着写方案或代码。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-requirement-intake`，或明确要求使用 Coding Feature Workflow 的需求澄清阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通需求讨论自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-requirement-intake`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入需求澄清阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `investigation.md`、`requirements.md` 和 `resource/README.md` 已由 orchestrator/template 准备好。
- `investigation.md stage_status: ready`。
- `investigation.md evidence_complete: true`。
- `investigation.md updated_at` 已写入 ISO 8601 + timezone。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游准备文件。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入文档前后都要检查工作区状态。
- 只询问仓库无法回答的问题；提问必须附已查证据。
- 用户新增或改变 scope 时，先更新 `requirements.md` 的 in-scope / out-of-scope / acceptance criteria，再让后续阶段重算证据和设计。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 工作流

1. 读取 `investigation.md`，先理解仓库勘查结论、真实调用链、数据来源、相似实现、外部调研和已知风险。
2. 读取当前需求目录下`resource/`目录下的所有文件，找已有业务资料、会议纪要、原型或接口草案。
3. 从仓库中查可回答的问题，例如已有模块、相似功能、路由、数据表、枚举、权限模型等；不得询问能从仓库或 `investigation.md` 得到答案的问题。
4. 用 brainstorming 思路补齐 `requirements.md`：
   - 背景与业务目标
   - in-scope
   - out-of-scope
   - 用户路径或业务流程
   - acceptance criteria
   - 非功能要求
   - 约束与假设
   - 待确认问题
5. 识别所有模糊之处、边界情况和未明确行为，形成具体、明确的问题；每个问题必须写清已查证据、影响的 scope/AC 和需要用户作出的选择。
6. 只询问仓库无法回答的问题。每次提问必须附带已查证据；如果回答仍不清楚，继续澄清直到需求边界稳定。
7. 不进入技术设计，直到 acceptance criteria 可验证且范围边界稳定。

## 质量标准

- 每条验收标准都能被测试、日志、接口响应、UI 行为或数据状态验证。
- out-of-scope 要明确，避免 AI 在实现阶段擅自扩大范围。
- 待确认问题要区分 `BLOCKING` 和 `NON_BLOCKING`。
- 待确认问题必须具体到行为、边界、数据口径、权限、错误处理、兼容性或验证方式，不得用“请确认需求”这类泛问替代。
- 需求结论必须引用 `investigation.md` 的证据；如果和勘查结论冲突，记录冲突并提问，不能静默覆盖。
- 需求资料必须在 `resource/README.md` 建索引，写清文件名、来源、更新时间和用途。

## 输出

更新 `requirements.md` 和 `resource/README.md`。如果仍有阻塞问题，在 `requirements.md` frontmatter 将 `stage_status` 标记为 `blocked`、`evidence_complete: false`，并在“待确认问题”中记录；如果范围和 acceptance criteria 已稳定，将 `stage_status` 标记为 `ready`、`evidence_complete: true`。每次写入 `requirements.md` 或 `resource/README.md` 都必须同步更新对应 frontmatter 的 `updated_at`。输出下一步建议后停止。
