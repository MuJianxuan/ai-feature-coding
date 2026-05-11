---
name: coding-implementation-execution
description: "Coding 编码执行技能。Activation restricted: use only when the user explicitly names `coding-implementation-execution`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary coding, bug fixing, config edits, or implementation requests."
---

# Coding Implementation Execution

## 目标

严格按 `tasks.md` 执行代码修改，不擅自扩大范围。每次执行都留下可复核证据。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-implementation-execution`，或明确要求使用 Coding Feature Workflow 的编码执行阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 coding / bugfix / config edit 自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-implementation-execution`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入编码执行阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md`、`investigation.md`、`design.md`、`tasks.md` 和 `verification.md` 已存在。
- `requirements.md stage_status: ready` 且 `requirements.md evidence_complete: true`。
- `investigation.md stage_status: ready` 且 `investigation.md evidence_complete: true`。
- `design.md stage_status: ready` 且 `design.md evidence_complete: true`。
- `design.md approval_status: approved`，且 `approved_by`、`approved_at`、`approval_evidence` 已补齐。
- `tasks.md stage_status: ready` 且 `tasks.md evidence_complete: true`。
- `task_count` 与真实任务数量一致。
- 至少存在一个真实 `TODO` 或 `DOING` 任务。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；开始前后都要检查工作区状态并区分用户改动和本次改动。
- 启动服务前必须按 contract 的 `Service startup and port-check protocol` 确认端口和已有进程状态。
- 发现当前任务需要扩大 scope 时，按 contract 的 `Scope change protocol` 记录并停止请求确认，不得擅自扩任务。
- 本阶段一次只执行一个 `TODO` / `DOING` 任务；任务完成后必须停下，输出下一步建议。除非用户明确要求连续推进，不得自行执行下一个任务或调用验证收口。

## 开始前

1. 读取 `requirements.md`、`investigation.md`、`design.md`、`tasks.md`、`verification.md`。
2. 加载项目编码规范索引：如果 `.docs/spec/INDEX.md` 存在，读取其内容，了解当前项目已有哪些编码规范文档可供参考。如果 `.docs/spec/INDEX.md` 不存在或 `.docs/spec/` 目录不存在，跳过此步骤。
3. 如果存在真实 `DOING` 任务，优先恢复该任务；否则选择用户明确指定的任务，或第一个真实 `TODO` 任务。
4. 将任务状态改为 `DOING`，记录开始时间和执行者为 AI。
5. 检查工作区状态。不要覆盖用户已有改动；遇到冲突先读懂再处理。

## 执行规则

- 只改当前任务需要的文件。
- 优先沿用现有架构、helper、类型和测试模式。
- 涉及接口时同步处理 request、response、stream/logging/persistence。
- 涉及数据时同步处理 schema、migration、读写路径、回滚草案。
- 涉及 UI 时同步处理 loading、empty、error、refresh、权限和响应式边界。
- 发现同类 bug 或相邻风险时，先记录在任务风险或新增任务中；只有与当前交付强相关才一并修。
- 执行代码修改时，如果 `.docs/spec/INDEX.md` 中有与当前任务相关的规范文档（根据任务涉及的技术栈匹配），读取并遵循该规范的原则和规约。

## 完成规则

1. 执行任务的完成判定。
2. 通过则把状态改为 `DONE`，写结构化交付记录：改动文件、验证命令或验证证据、结果、残余风险；“已完成”这类弱描述不能作为 `DONE` 证据。
3. 未通过但可继续排查时继续；确实缺少外部条件时改为 `BLOCKED` 并写明证据。
4. 每次修改 `tasks.md` 的任务状态、交付记录或风险时，都必须同步更新 `tasks.md updated_at`，并保持 `task_count` 等于真实任务数量。
5. 除非经过 scope change 回流并重新规划任务，否则不要在编码执行阶段改变 `tasks.md stage_status` 或随意调整 `task_count`。
6. 更新 `verification.md` 中对应检查项；每次写入 `verification.md` 都必须同步更新 `updated_at`。如果检查项仍未满足，保持 `verification.md evidence_complete: false`，不要提前标记完成。

## Resume protocol

当任务中断或存在 `DOING` 时：

1. 读取 `tasks.md` 中的 `DOING` 任务、交付记录和完成判定。
2. 检查工作区 diff，区分已有用户改动、本次 AI 改动和未记录改动。
3. 对照 `design.md` 和任务完成判定，确认还缺哪些文件、测试或证据。
4. 如果 diff 与任务范围不一致，先记录风险并停止请求用户确认，不擅自覆盖或回滚。
5. 恢复执行后继续维护同一个任务的交付记录；不得新开重复任务掩盖中断状态。

## 禁止

- 禁止跳过 `tasks.md` 直接凭记忆改代码。
- 禁止删除文件、切换分支、提交或推送，除非用户明确许可。
- 禁止把未验证任务标成 `DONE`。
