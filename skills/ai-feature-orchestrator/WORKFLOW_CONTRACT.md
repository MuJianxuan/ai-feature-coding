# AI Feature Workflow Contract

本文件是 `ai-feature-orchestrator` 与各阶段 skill 的共享契约。所有 `ai-*` skill 必须优先遵守本契约；如果本文件和单个 `SKILL.md` 冲突，以更严格、更不容易误触发的规则为准。

统一术语：本套件称为 **AI Feature Workflow**。历史文档或用户请求中的 “skills workflow / 技能工作流” 仅作为 alias；新文档和输出优先使用 “AI Feature Workflow”。

## 1. Activation contract

AI Feature Workflow 是 explicit opt-in，不参与普通 Codex 工作流自动触发。

允许启动的情况只有两类：

1. `direct_explicit`：用户在当前请求中明确写出某个 skill 名，例如 `ai-feature-orchestrator`、`ai-task-planning`。
2. `routed_invocation`：另一个已经合法触发的 skill 显式路由到目标 skill，并提供完整 route payload。

禁止启动的情况：

- 普通“帮我实现功能 / 调查代码 / 写设计 / 拆任务 / 测试验证”。
- 普通 debugging、root-cause analysis、repo audit、UI 修改、配置修改。
- 只有历史上下文曾经提过 AI Feature Workflow，但当前请求没有显式继续。

## 2. Route contract

被动路由必须包含以下字段：

```yaml
activation_source: ai-feature-orchestrator
feature_dir: .docs/feature-YYYYMMDD-short-name
stage_evidence:
  reason: "命中哪个阶段推断规则"
  files:
    - path: .docs/feature-YYYYMMDD-short-name/requirements.md
      finding: "stage_status: ready"
```

阶段 skill 的行为：

- 如果是 `direct_explicit` 但缺少 `feature_dir`：停止，提示用户提供已有目录，或改用 `ai-feature-orchestrator`。
- 如果是 `routed_invocation` 但缺少 `activation_source`、`feature_dir` 或 `stage_evidence` 任一字段：拒绝启动。
- 不得自己猜测 feature 目录。
- 不得自己创建上游阶段文档来绕过前置检查。

## 3. Document metadata contract

每个 feature 阶段文档必须包含 YAML frontmatter。阶段文档只包括：`requirements.md`、`investigation.md`、`design.md`、`tasks.md`、`verification.md`、`handoff.md`。

通用字段：

```yaml
feature_stage: requirements # requirements / investigation / design / tasks / verification / handoff
stage_status: draft # draft / ready / blocked / complete
updated_at: "2026-05-09T00:00:00+08:00"
evidence_complete: false
```

`updated_at` 在模板中可以为空字符串；一旦任何阶段写入或更新文档，必须使用 ISO 8601 + timezone，例如 `2026-05-09T20:30:00+08:00`。

`design.md` 额外包含设计审批字段：

```yaml
approval_status: pending # pending / approved / blocked
approved_by: ""
approved_at: ""
approval_evidence: ""
```

辅助文档 `README.md`、`resource/README.md` 和 `sql/*.sql` 不参与阶段推断。它们可以有自己的 metadata，但不得被 orchestrator 当成 feature 阶段文档。

`stage_status` 语义：

- `draft`：阶段产物尚未达到下一阶段输入质量。
- `ready`：阶段产物可作为下一阶段输入。
- `blocked`：阶段缺少外部条件，不能继续自动推进。
- `complete`：验证或交付收口已完成。

阶段完成时必须更新 metadata：

- `ai-requirement-intake`：无阻塞且 acceptance criteria 可验证时，把 `requirements.md` 标记为 `ready`。
- `ai-repo-investigation`：真实链路、数据来源、已查文件齐备时，把 `investigation.md` 标记为 `ready`。
- `ai-technical-design`：方案可拆任务时，把 `design.md` 标记为 `ready`，并保持 `approval_status: pending`；依赖业务决策时标记为 `blocked`。
- `ai-task-planning`：只在 `design.md stage_status: ready` 且 `approval_status: approved` 后拆任务；如果当前用户请求明确批准设计，必须先补齐审批字段再拆任务。真实任务写入后，把 `tasks.md` 标记为 `ready` 并更新 `task_count`。
- `ai-verification-closeout`：验收映射完成后，把 `verification.md` 标记为 `complete`；交付摘要齐备后，把 `handoff.md` 标记为 `complete`。

## 4. Placeholder policy

模板中的以下内容不算有效阶段内容：

- 空表格。
- `UNSET`。
- `<...>` 占位符。
- 示例代码块或说明文字。
- `task_count: 0`。
- `approval_status: pending` 不是设计批准。

阶段推断不能只 grep 某个词。必须结合 metadata、表格真实行、任务条目和证据内容判断。

## 5. Task status contract

`tasks.md` 中真实任务使用以下状态：

- `TODO`：真实任务已规划但未开始。
- `DOING`：真实任务正在执行或需要恢复。
- `DONE`：真实任务完成且完成判定通过。
- `BLOCKED`：真实任务缺少外部条件。

只有满足以下条件的任务才算真实任务：

- 标题包含稳定任务 ID，例如 `T01 - ...`。
- 有非空 `输入`、`输出`、`完成判定`、`关联模块/文件`。
- 不是模板说明、空表格或示例代码块。

## 6. Gate policy

默认一次只推进一个阶段。

允许的单步推进：

- `ai-feature-orchestrator` 判断阶段并路由到一个阶段 skill。
- 一个阶段 skill 完成当前阶段文档更新，然后停止并输出下一步建议。
- `ai-implementation-execution` 一次只执行一个 `TODO` / `DOING` 任务。
- 用户明确“批准设计 / 继续任务拆解 / 继续下一阶段”时，可以把 `design.md approval_status` 更新为 `approved`，但仍只进入 `ai-task-planning` 这一个阶段。

禁止的自动推进：

- 阶段 skill 完成后自行调用下一阶段。
- 编码完成一个任务后自行执行下一个任务。
- 验证完成后自行 git commit / 归档 / 发布。

只有用户明确说“连续推进”“继续下一阶段”“继续执行下一项任务”时，才允许进入下一步。

## 7. Design approval contract

设计审批是 `design.md` 到 `tasks.md` 的硬门禁：

1. `ai-technical-design` 只能把设计写到 `stage_status: ready`，默认 `approval_status: pending`，然后停止。
2. 如果用户明确批准设计或明确要求进入任务拆解，`ai-feature-orchestrator` 或 `ai-task-planning` 必须先记录：
   - `approval_status: approved`
   - `approved_by: user`
   - `approved_at: <ISO 8601 + timezone>`
   - `approval_evidence: <用户原话摘要>`
3. 如果 `design.md` 未批准，`ai-task-planning` 必须停止并报告等待设计审批，不能把 `stage_status: ready` 等同于已批准。
4. 如果用户要求修改设计，应回到 `ai-technical-design`，不得在 `tasks.md` 中绕过设计变更。

## 8. Safety policy

所有阶段必须遵守：

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入前后检查工作区状态。
- 启动服务前先确认端口与已有进程状态。
- 文档用中文写，保留 technical English names、路径、API 名。
- 缺少账号、密钥、业务决策、外部权限时才问用户；提问必须附已查证据。

## 9. Service startup and port-check protocol

任何阶段需要启动服务、预览或后台进程时，必须先在阶段文档或输出中记录：

1. 目标命令、预期端口和用途。
2. 端口占用检查结果；常用命令形态为 `lsof -nP -iTCP:<port> -sTCP:LISTEN`，如果项目有既定脚本则优先用项目脚本。
3. 已有进程判断：PID、command、是否属于当前项目。
4. 启动日志摘要和停止方式。

如果端口已被无关进程占用，停止并请求用户确认；不得擅自 kill。

## 10. Scope change protocol

任何阶段发现当前工作需要扩大或改变 scope 时：

1. 先记录 `scope_change_candidate`：触发原因、证据、影响的 acceptance criteria、涉及文件、风险。
2. 如果该变更不是当前任务完成判定的必要条件，停止并请求用户确认，不直接修改代码或任务。
3. 用户确认后，按影响范围回流更新 `requirements.md`、`investigation.md`、`design.md` 和 `tasks.md`。
4. 禁止通过在 `tasks.md` 临时新增任务来绕过 requirements / design 的 scope 边界。

## 11. Resume protocol

恢复中断任务时：

1. 读取 `tasks.md` 的 `DOING` 任务、交付记录、完成判定。
2. 检查工作区 diff，区分用户改动和 AI 改动。
3. 对照 `design.md`、`verification.md` 判断缺失证据。
4. 如果 diff 超出当前任务范围，停止并报告风险，不擅自覆盖或回滚。
5. 继续时沿用同一任务记录，不创建重复任务掩盖中断。

## 12. Smoke-test expectations

维护 AI Feature Workflow 时至少检查：

- 所有 `agents/openai.yaml` 的 `allow_implicit_invocation` 为 `false`。
- 所有阶段 skill 都包含 `Activation policy`、`route contract`、`Safety policy`。
- 模板 Markdown 都有 frontmatter。
- 阶段模板 frontmatter 可解析，且包含合法 `feature_stage`、`stage_status`、`updated_at`、`evidence_complete`。
- `design.md` 包含设计审批字段，`tasks.md` 包含 `task_count`。
- 模板不包含会被误判为真实任务或阻塞项的默认行。
- Orchestrator 的 route payload 字段和子 skill preflight 一致。
- Orchestrator 的 blocked 阶段判断顺序不会被 draft/content 判断抢先命中。
