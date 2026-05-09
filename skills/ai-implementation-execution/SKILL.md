---
name: ai-implementation-execution
description: "AI 编码执行技能。Activation restricted: use only when the user explicitly names `ai-implementation-execution`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary coding, bug fixing, config edits, or implementation requests."
---

# AI Implementation Execution

## 目标

严格按 `tasks.md` 执行代码修改，不擅自扩大范围。每次执行都留下可复核证据。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-implementation-execution`，或明确要求使用这套 AI feature workflow 的编码执行阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 coding / bugfix / config edit 自动升级成这套工作流。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `ai-implementation-execution`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `ai-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被工作流路由。此时必须同时收到：
  - `activation_source: ai-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入编码执行阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md`、`investigation.md`、`design.md` 和 `tasks.md` 已存在。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；开始前后都要检查工作区状态并区分用户改动和本次改动。
- 启动服务前必须确认端口和已有进程状态。
- 本阶段一次只执行一个 `TODO` / `DOING` 任务；任务完成后必须停下，输出下一步建议。除非用户明确要求连续推进，不得自行执行下一个任务或调用验证收口。

## 开始前

1. 读取 `requirements.md`、`investigation.md`、`design.md`、`tasks.md`。
2. 选择第一个 `TODO` 任务，或用户明确指定的任务。
3. 将任务状态改为 `DOING`，记录开始时间和执行者为 AI。
4. 检查工作区状态。不要覆盖用户已有改动；遇到冲突先读懂再处理。

## 执行规则

- 只改当前任务需要的文件。
- 优先沿用现有架构、helper、类型和测试模式。
- 涉及接口时同步处理 request、response、stream/logging/persistence。
- 涉及数据时同步处理 schema、migration、读写路径、回滚草案。
- 涉及 UI 时同步处理 loading、empty、error、refresh、权限和响应式边界。
- 发现同类 bug 或相邻风险时，先记录在任务风险或新增任务中；只有与当前交付强相关才一并修。

## 完成规则

1. 执行任务的完成判定。
2. 通过则把状态改为 `DONE`，写交付记录：改动文件、验证命令、结果、残余风险。
3. 未通过但可继续排查时继续；确实缺少外部条件时改为 `BLOCKED` 并写明证据。
4. 更新 `verification.md` 中对应检查项。

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
