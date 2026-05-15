---
name: coding-task-planning
description: "Coding 任务拆解技能。Activation restricted: use only when the user explicitly names `coding-task-planning`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary planning, TODO creation, or implementation breakdown requests."
---

# Coding Task Planning

## 目标

把技术设计拆成 AI 可以逐项执行的任务清单。`tasks.md` 是编码执行的唯一驱动文件。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-task-planning`，或明确要求使用 Coding Feature Workflow 的任务拆解阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通任务拆解自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-task-planning`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入任务拆解阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md`、`requirements.md` 和 `design.md` 已存在。
- `discovery.md stage_status: ready` 且 `discovery.md evidence_complete: true`。
- `requirements.md stage_status: ready` 且 `requirements.md evidence_complete: true`。
- `design.md` 的 `stage_status: ready`。
- `design.md stage_status: ready` 且 `design.md evidence_complete: true`。
- `discovery.md`、`requirements.md`、`design.md` 的 `project_context` 均为 `existing_project` 或 `empty_project`，且相互一致。
- `design.md approval_status: approved`；如果 metadata 仍是 `pending` 但当前用户请求明确批准设计或明确要求进入任务拆解，先补齐审批字段；否则停止并报告等待设计审批。
- `approved_by`、`approved_at`、`approval_evidence` 已补齐，且 `approved_at` 是 ISO 8601 + timezone。
- 上述 `discovery.md`、`requirements.md`、`design.md` 的 `updated_at` 均已写入 ISO 8601 + timezone。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `tasks.md` 前后都要检查工作区状态。
- 只把已批准且 `stage_status: ready` 的 `design.md` 拆成任务，不得擅自扩 scope；发现 scope 变化时按 contract 的 `Scope change protocol` 回流处理。
- 发现影响任务边界、验收方式、数据/API/UI 行为或风险验证的新澄清问题时，先逐一询问用户；回答影响上游产物时回流更新对应文档。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 拆解规则

1. 拆解前先做任务级头脑风暴：识别依赖顺序、按业务域 / acceptance criteria 切出的可独立验证垂直切片、潜在阻塞和可并行边界。
2. 每项任务只覆盖一个清晰目标，能独立完成和验证。
3. 先按业务域垂直切片组织，再在每个业务域内按依赖顺序排序：schema/config -> backend/domain -> API/adapter -> frontend/state -> tests/docs。
4. 每项规划期任务必须写：
   - `status`: `TODO` / `DOING` / `DONE` / `BLOCKED`
   - 业务域：引用 `requirements.md` 业务域建模中的 `Domain ID`；`cross-domain` 任务必须列出服务的所有业务域。
   - 输入：依赖的 discovery、requirements、design 证据或文件。
   - 输出：预期改动文件或行为。
   - 完成判定：可执行命令、接口响应、UI 行为或数据状态。
   - 关联模块/文件：尽量列路径或搜索关键词。
   - 执行要点：关键实现顺序、复用点或注意事项。
   - 风险：可能影响的兼容性、数据、权限或性能。
   - 交付记录：规划期可以为空或写“待执行”；任务进入 `DONE` 时必须由执行阶段补齐真实记录。
5. `输入` 必须引用至少一个真实 AC；不得创建没有业务域和 AC 归属的纯技术任务。
6. 不把“验证全部功能”作为单个大任务；验证也要按业务域、AC 和风险拆分。
7. 如果发现设计不可拆或范围过大，回到 `design.md` 缩小边界。
8. 如果用户刚刚明确批准设计但 metadata 仍是 `pending`，先把 `design.md` 的审批字段补齐，再拆任务。
9. 如果任务依赖第三方库、框架、OpenAI/API 或版本行为，只引用 discovery / design 中已有外部证据；缺证据时回到相应阶段补证，不在任务中凭空假设。

## 推荐任务模板

```markdown
### T01 - <任务名>

- status: TODO
- 业务域：
- 输入：
- 输出：
- 关联模块/文件：
- 执行要点：
- 完成判定：
- 风险：
- 交付记录：
```

## 输出

更新 `tasks.md`，并在 frontmatter 将 `stage_status` 标记为 `ready`、`evidence_complete: true`、`task_count` 更新为真实任务数量，同时同步更新 `updated_at`。如果本阶段因用户刚刚批准设计而写入 `design.md` 审批字段，也必须同步更新 `design.md` 的 `updated_at`，并保持 `design.md evidence_complete: true`。除非用户明确要求，否则不要开始编码。输出下一步建议后停止。
