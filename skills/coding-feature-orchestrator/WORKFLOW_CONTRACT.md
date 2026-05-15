# Coding Feature Workflow Contract

本文件是 `coding-feature-orchestrator` 与各阶段 skill 的共享契约。所有 `coding-*` skill 必须优先遵守本契约；如果本文件和单个 `SKILL.md` 冲突，以更严格、更不容易误触发的规则为准。

统一术语：本套件称为 **Coding Feature Workflow**。历史文档或用户请求中的 “skills workflow / 技能工作流” 仅作为 alias；新文档和输出优先使用 “Coding Feature Workflow”。

## 1. Activation contract

Coding Feature Workflow 是 explicit opt-in，不参与普通工作流自动触发。

允许启动的情况只有两类：

1. `direct_explicit`：用户在当前请求中明确写出某个 skill 名，例如 `coding-feature-orchestrator`、`coding-task-planning`。
2. `routed_invocation`：`coding-feature-orchestrator` 显式路由到目标阶段 skill，并提供完整 route payload。

禁止启动的情况：

- 普通“帮我实现功能 / 调查代码 / 写设计 / 拆任务 / 测试验证”。
- 普通 debugging、root-cause analysis、repo audit、UI 修改、配置修改。
- 只有历史上下文曾经提过 Coding Feature Workflow，但当前请求没有显式继续。

## 2. Route contract

被动路由必须包含以下字段：

```yaml
activation_source: coding-feature-orchestrator
feature_dir: .docs/feature-YYYYMMDD-short-name
stage_evidence:
  reason: "命中哪个阶段推断规则"
  files:
    - path: .docs/feature-YYYYMMDD-short-name/requirements.md
      finding: "stage_status: ready"
```

阶段 skill 的行为：

- 如果是 `direct_explicit` 但缺少 `feature_dir`：停止，提示用户提供已有目录，或改用 `coding-feature-orchestrator`。
- 如果是 `direct_explicit` 且已有 `feature_dir`：仍必须执行本阶段的 upstream metadata gate；不得只因为文件存在就绕过上一阶段的 `ready`、`evidence_complete`、设计审批或 `task_count` 校验。
- 如果是 `routed_invocation` 但缺少 `activation_source`、`feature_dir` 或 `stage_evidence` 任一字段：拒绝启动。
- 不得自己猜测 feature 目录。
- 不得自己创建上游阶段文档来绕过前置检查。

路由执行机制：

- 如果运行环境支持真实 skill handoff，`coding-feature-orchestrator` 输出完整 route payload，并交给目标阶段 skill 执行。
- 如果运行环境没有自动 handoff，但可读取本仓库 `skills/<stage-skill>/SKILL.md`，`coding-feature-orchestrator` 必须读取目标阶段 skill 的 `SKILL.md`，按其规则执行这一阶段，然后停止。
- 如果目标阶段 skill 不存在或不可读，`coding-feature-orchestrator` 停止，不伪执行阶段；只输出 route payload、缺失文件路径和下一步建议。
- 无论采用哪种方式，都必须遵守 Gate policy：默认一次只推进一个阶段。

## 3. Document metadata contract

每个 feature 阶段文档必须包含 YAML frontmatter。阶段文档只包括：`discovery.md`、`requirements.md`、`design.md`、`tasks.md`、`verification.md`、`handoff.md`。

通用字段：

```yaml
feature_stage: discovery # discovery / requirements / design / tasks / verification / handoff
stage_status: draft # 按阶段限制：discovery/requirements/design/tasks 使用 draft/ready/blocked；verification/handoff 使用 draft/blocked/complete
updated_at: "2026-05-09T00:00:00+08:00"
evidence_complete: false
project_context: unknown # unknown / existing_project / empty_project
project_context_evidence: ""
```

`updated_at` 在模板中可以为空字符串；一旦任何阶段写入或更新文档，必须使用 ISO 8601 + timezone，例如 `2026-05-09T20:30:00+08:00`。

阶段文档 metadata 写入规则：

- 每次写入或更新阶段文档时，必须同步更新该文档 frontmatter 的 `updated_at`。
- `evidence_complete: true` 只表示该阶段文档的证据和内容足以进入下一阶段，通常只与 `stage_status: ready` 或 `stage_status: complete` 同时出现。
- `stage_status: draft` 或 `stage_status: blocked` 时，`evidence_complete` 必须保持或更新为 `false`，并在正文写明缺口、阻塞证据或待确认条件。
- `tasks.md` 的 `task_count` 必须等于真实任务数量；每次新增、拆分、删除或因批准后的 scope 变更调整真实任务时都必须同步更新。
- 同一次操作触碰多个阶段文档时，每个被修改的阶段文档都必须各自更新 metadata。
- `project_context` 必须在 discovery 阶段确定，并在后续阶段文档中保持一致；`stage_status: ready` 或 `complete` 前不能仍为 `unknown`。
- `project_context_evidence` 必须记录判定依据，例如用户明确说明、仓库探测结果、manifest/src/test 缺失证据或已有项目入口证据。

`design.md` 额外包含设计审批字段：

```yaml
approval_status: pending # pending / approved / blocked
approved_by: ""
approved_at: ""
approval_evidence: ""
```

辅助文档 `README.md`、`resource/README.md` 和 `sql/*.sql` 不参与阶段推断。它们可以有自己的 metadata，但不得使用 `feature_stage` 或 `stage_status`，应使用 `doc_type` / `doc_status` 等辅助字段，避免被 orchestrator 当成 feature 阶段文档。

`stage_status` 语义：

- `draft`：阶段产物尚未达到下一阶段输入质量。
- `ready`：阶段产物可作为下一阶段输入。
- `blocked`：阶段缺少外部条件，不能继续自动推进。
- `complete`：验证或交付收口已完成。

阶段级合法状态：

| 阶段文档 | 合法 `stage_status` |
| --- | --- |
| `discovery.md` | `draft` / `ready` / `blocked` |
| `requirements.md` | `draft` / `ready` / `blocked` |
| `design.md` | `draft` / `ready` / `blocked` |
| `tasks.md` | `draft` / `ready` / `blocked` |
| `verification.md` | `draft` / `blocked` / `complete` |
| `handoff.md` | `draft` / `blocked` / `complete` |

`complete` 只允许用于验证和交付收口阶段；`requirements`、`design`、`tasks` 完成后应标记为 `ready`，不能标记为 `complete`。`verification.md` 和 `handoff.md` 不使用 `ready`，未收口时保持 `draft` 或 `blocked`。

阶段完成时必须更新 metadata：

- `coding-feature-discovery`：按 `project_context` 完成项目上下文调研、必要外部调研、方案方向、模糊点清单和关键问题逐问逐答完成时，把 `discovery.md` 标记为 `ready`。
- `coding-requirement-intake`：在 `discovery.md stage_status: ready` 后规格化 PRD；必须按业务域建模，并让每条 acceptance criteria 绑定真实 `Domain ID`；无阻塞且 acceptance criteria 可验证时，把 `requirements.md` 标记为 `ready`。
- `coding-technical-design`：在 `requirements.md stage_status: ready` 后按 acceptance criteria 做技术上下文与架构依据调研、澄清未明确点并设计方案；`existing_project` 要求真实链路、数据来源和已查文件，`empty_project` 要求 bootstrap architecture、脚手架依据和首个可运行目标；方案比较和验证策略齐备且方案可拆任务时，把 `design.md` 标记为 `ready`，并保持 `approval_status: pending`；依赖业务决策时标记为 `blocked`。
- `coding-task-planning`：只在 `design.md stage_status: ready` 且 `approval_status: approved` 后拆任务；如果当前用户请求明确批准设计，必须先补齐审批字段再拆任务。任务必须先按业务域 / acceptance criteria 切垂直切片，再在每个业务域内按技术依赖排序；每个真实任务必须绑定 `Domain ID` 和至少一个 AC。真实任务写入后，把 `tasks.md` 标记为 `ready` 并更新 `task_count`。
- `coding-verification-closeout`：只有所有 in-scope acceptance criteria 都有真实验证证据且结果为 `PASS` 时，才把 `verification.md` 标记为 `complete`、`evidence_complete: true`；存在 `FAIL`、`BLOCKED` 或未覆盖项时，保持或更新为 `draft/blocked`、`evidence_complete: false` 并写清证据。交付摘要、变更范围、配置 / SQL / 部署事项、复核入口、验证结论和残余风险齐备后，才把 `handoff.md` 标记为 `complete`；无相关配置、SQL、部署或数据修复时也必须显式写“无”。

## 4. Placeholder policy

模板中的以下内容不算有效阶段内容：

- 空表格。
- `UNSET`。
- `<...>` 占位符。
- 示例代码块或说明文字。
- `task_count: 0`。
- `approval_status: pending` 不是设计批准。

阶段推断不能只 grep 某个词。必须结合 metadata、表格真实行、任务条目和证据内容判断。

## 4.1 Project context contract

Coding Feature Workflow 同时支持已有项目功能迭代和从 0 创建项目，但必须显式记录项目上下文：

- `existing_project`：仓库中存在可调研的项目结构、manifest、源码入口、测试或业务链路。Discovery 必须做仓库广扫；Design 必须记录仓库勘探、真实链路、数据来源、相似实现和 source of truth。
- `empty_project`：当前需求是新建项目 / 空项目 / 从 0 scaffold。Discovery 不强制仓库广扫，改为记录技术栈候选、官方脚手架、基础依赖、项目结构、测试框架、lint/format、启动命令、打包或部署约束等调研证据。Design 不强制既有代码链路，改为记录 bootstrap architecture、目录结构、初始化命令、核心模块边界、配置/env、测试策略和首个可运行目标。
- `unknown`：只允许存在于 draft 阶段。进入 ready/complete 前必须由用户确认或仓库证据确定为 `existing_project` 或 `empty_project`。

判定规则：

1. 用户明确说“空项目 / 从 0 创建 / 新建项目 / scaffold project”时，可以标记 `empty_project`，但如果仓库已有明显 manifest、源码入口或历史 feature 目录，必须先报告冲突证据并确认。
2. 自动探测只能作为建议：缺少 manifest、源码入口、测试和业务代码时建议 `empty_project`；存在这些证据时建议 `existing_project`。
3. 自动探测不能静默覆盖用户意图；冲突时停止并只问一个确认问题。
4. 后续阶段发现上下文判定错误时，按 scope change / clarification 回流更新相关阶段文档。

可执行状态检查器：

- `scripts/inspect_feature_state.py <feature_dir>` 是阶段推断的 stdlib-only 辅助检查器。
- 输出必须包含 `state`、`next_skill`、`blocking`、`complete`、`reason` 和 `evidence`。
- Orchestrator 执行时仍以 `SKILL.md` 和本 contract 为准；维护时必须让脚本和文档规则保持一致。

## 5. Task status contract

`tasks.md` 中真实任务使用以下状态：

- `TODO`：真实任务已规划但未开始。
- `DOING`：真实任务正在执行或需要恢复。
- `DONE`：真实任务完成且完成判定通过。
- `BLOCKED`：真实任务缺少外部条件。

只有满足以下条件的任务才算真实任务：

- 标题包含稳定任务 ID，例如 `T01 - ...`。
- 规划期有非空 `业务域`、`输入`、`输出`、`完成判定`、`关联模块/文件`、`执行要点`、`风险`。
- `业务域` 必须引用 `requirements.md` 业务域建模中的真实 `Domain ID`；`输入` 必须引用至少一个真实 AC。
- `DONE` 任务必须补齐真实且结构化的 `交付记录`，至少包含：改动文件、验证命令或验证证据、结果、残余风险；“已完成”这类弱描述不能算完成证据。
- 不是模板说明、空表格或示例代码块。
- 同一 `tasks.md` 中真实任务 ID 不能重复；同时只能存在一个真实 `DOING` 任务，否则恢复目标不唯一，必须停止整理任务状态。

## 6. Upstream metadata gate

阶段 skill 在 `direct_explicit` 或 `routed_invocation` 下都必须执行相同的 upstream metadata gate：

- `coding-requirement-intake`：要求 `discovery.md stage_status: ready` 且 `discovery.md evidence_complete: true`。
- `coding-technical-design`：要求 `discovery.md`、`requirements.md` 均为 `stage_status: ready` 且 `evidence_complete: true`。
- `coding-task-planning`：要求 `discovery.md`、`requirements.md`、`design.md` 均为 `stage_status: ready` 且 `evidence_complete: true`；同时要求 `design.md approval_status: approved`，并补齐 `approved_by`、`approved_at`、`approval_evidence`。
- `coding-implementation-execution`：要求 `discovery.md`、`requirements.md`、`design.md`、`tasks.md` 均为 `stage_status: ready` 且 `evidence_complete: true`；要求 `design.md approval_status: approved`；要求 `tasks.md task_count` 与真实任务数量一致，且至少存在一个真实 `TODO` 或 `DOING` 任务。
- `coding-verification-closeout`：要求 `discovery.md`、`requirements.md`、`design.md`、`tasks.md` 均为 `stage_status: ready` 且 `evidence_complete: true`；要求 `design.md approval_status: approved`；要求 `tasks.md task_count` 与真实任务数量一致，且不存在 `TODO` 或 `DOING` 任务。

任一 gate 不满足时，停止并报告具体文档、字段和值；不要临时补造上游阶段内容，不要自行改状态以通过 gate。

## 7. Gate policy

默认一次只推进一个阶段。

允许的单步推进：

- `coding-feature-orchestrator` 判断阶段并路由到一个阶段 skill。
- 一个阶段 skill 完成当前阶段文档更新，然后停止并输出下一步建议。
- `coding-implementation-execution` 一次只执行一个 `TODO` / `DOING` 任务。
- 用户明确“批准设计 / 继续任务拆解 / 继续下一阶段”时，可以把 `design.md approval_status` 更新为 `approved`，但仍只进入 `coding-task-planning` 这一个阶段。

禁止的自动推进：

- 阶段 skill 完成后自行调用下一阶段。
- 编码完成一个任务后自行执行下一个任务。
- 验证完成后自行 git commit / 归档 / 发布。

只有用户明确说“连续推进”“继续下一阶段”“继续执行下一项任务”时，才允许进入下一步。

## 8. Design approval contract

设计审批是 `design.md` 到 `tasks.md` 的硬门禁：

1. `coding-technical-design` 只能把设计写到 `stage_status: ready`，默认 `approval_status: pending`，然后停止。
2. 如果用户明确批准设计或明确要求进入任务拆解，`coding-feature-orchestrator` 或 `coding-task-planning` 必须先记录：
   - `approval_status: approved`
   - `approved_by: user`
   - `approved_at: <ISO 8601 + timezone>`
   - `approval_evidence: <用户原话摘要>`
   - `updated_at: <ISO 8601 + timezone>`
3. 如果 `design.md` 未批准，`coding-task-planning` 必须停止并报告等待设计审批，不能把 `stage_status: ready` 等同于已批准。
4. 如果用户要求修改设计，应回到 `coding-technical-design`，不得在 `tasks.md` 中绕过设计变更。

## 9. Safety policy

所有阶段必须遵守：

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入前后检查工作区状态。
- 启动服务前先确认端口与已有进程状态。
- 文档用中文写，保留 technical English names、路径、API 名。
- 缺少账号、密钥、业务决策、外部权限时才问用户；提问必须附已查证据。

## 10. Service startup and port-check protocol

任何阶段需要启动服务、预览或后台进程时，必须先在阶段文档或输出中记录：

1. 目标命令、预期端口和用途。
2. 端口占用检查结果；常用命令形态为 `lsof -nP -iTCP:<port> -sTCP:LISTEN`，如果项目有既定脚本则优先用项目脚本。
3. 已有进程判断：PID、command、是否属于当前项目。
4. 启动日志摘要和停止方式。

如果端口已被无关进程占用，停止并请求用户确认；不得擅自 kill。

## 11. Scope change protocol

任何阶段发现当前工作需要扩大或改变 scope 时：

1. 先记录 `scope_change_candidate`：触发原因、证据、影响的 acceptance criteria、涉及文件、风险。
2. 如果该变更不是当前任务完成判定的必要条件，停止并请求用户确认，不直接修改代码或任务。
3. 用户确认后，按影响范围回流更新 `discovery.md`、`requirements.md`、`design.md` 和 `tasks.md`。
4. 禁止通过在 `tasks.md` 临时新增任务来绕过 requirements / design 的 scope 边界。

## 12. Clarification, brainstorming, and research protocol

`discovery.md` 是需求前置发现阶段：

1. 先确定 `project_context`；`existing_project` 先做仓库广扫，`empty_project` 先做官方脚手架、技术栈和架构调研；再按需使用 Context7 或官方文档验证第三方库、框架、OpenAI/API、版本行为或不确定实现。
2. 以头脑风暴方式列出 2-3 个方案方向、适用条件、风险和取舍，但不得写成最终 design。
3. 列出全部已识别模糊点、边界情况和未明确行为。
4. 凡影响 scope、acceptance criteria、用户路径、数据/API/UI 行为、风险验证或任务拆解的问题，都必须标为 `BLOCKING` 并逐一询问。
5. 每次只问一个最高优先级关键问题；用户回答后记录问答、结论和更新位置，再继续下一个关键问题。
6. `discovery.md ready` 只表示可以进入 PRD 规格化，不表示最终技术设计已批准。

后续阶段发现新的澄清问题时：

1. 先记录问题、证据、影响范围和阻塞级别。
2. 逐一询问用户，不得做静默假设。
3. 用户回答后按影响范围回流更新 `discovery.md`、`requirements.md` 或 `design.md`。
4. 外部调研证据集中写入 `discovery.md` 或 `design.md`；`tasks.md` 只引用关键结论和来源。

## 12.1 Business domain contract

阶段仍是 Coding Feature Workflow 的执行引擎；业务域是需求和任务的组织、追踪和验收维度。

`requirements.md` 必须包含真实“业务域建模”表：

- `Domain ID` 使用稳定 ID，例如 `D-AUDIT`、`D-BILLING`。
- 每个业务域必须写清业务能力、Actor / Role、核心 Entity、业务规则 / 边界和关联 AC。
- `Acceptance Criteria` 表必须包含 `业务域` 列，且每条真实 AC 必须引用一个已定义的 `Domain ID`。

`tasks.md` 必须包含真实“业务域垂直切片”表，并满足：

- 每个真实任务必须写 `业务域：<Domain ID>`。
- 每个真实任务的 `输入` 必须引用至少一个真实 AC。
- `cross-domain` 任务允许存在，但必须显式列出服务的 `Domain ID` 和 AC，不能作为无归属技术任务绕过业务域追踪。

`scripts/inspect_feature_state.py` 对业务域执行硬门禁：缺少业务域建模、AC 业务域无效、任务业务域无效或任务未引用 AC 时，不得进入后续阶段。

## 13. Resume protocol

恢复中断任务时：

1. 读取 `tasks.md` 的 `DOING` 任务、交付记录、完成判定。
2. 检查工作区 diff，区分用户改动和 AI 改动。
3. 对照 `design.md`、`verification.md` 判断缺失证据。
4. 如果 diff 超出当前任务范围，停止并报告风险，不擅自覆盖或回滚。
5. 继续时沿用同一任务记录，不创建重复任务掩盖中断。

## 14. Smoke-test expectations

维护 Coding Feature Workflow 时至少检查：

- 所有阶段 skill 的 `SKILL.md` description 字段包含 "Activation restricted" 声明。
- 所有阶段 skill 都包含 `Activation policy`、`route contract`、`Safety policy`。
- 模板 Markdown 都有 frontmatter。
- 阶段模板 frontmatter 可解析，且包含合法 `feature_stage`、`stage_status`、`updated_at`、`evidence_complete`。
- 阶段文档必须遵守阶段级 `stage_status` 枚举：`complete` 只允许 `verification.md` / `handoff.md`，`ready` 不用于 `verification.md` / `handoff.md`。
- 辅助模板 Markdown 可解析，但不得包含 `feature_stage` 或 `stage_status`。
- `design.md` 包含设计审批字段，`tasks.md` 包含 `task_count`。
- 各阶段 skill 的输出规则必须说明 `updated_at` / `evidence_complete` 的更新方式；`coding-task-planning` 必须说明 `task_count` 更新为真实任务数量。
- `coding-verification-closeout` 的 preflight 和验证顺序必须读取 `design.md` 的技术上下文与架构依据、目标链路和 source of truth，避免只验证 `tasks.md` 的纸面链路。
- 模板不包含会被误判为真实任务或阻塞项的默认行。
- Orchestrator 的 route payload 字段和子 skill preflight 一致。
- Orchestrator 的 blocked 阶段判断顺序不会被 draft/content 判断抢先命中。
- 子阶段 skill 的 direct invocation preflight 必须覆盖 upstream metadata gate，不能只检查文件存在。
- `scripts/inspect_feature_state.py` 覆盖初始模板、缺少 `discovery.md`、拒绝误用内置模板目录、等待设计审批、任务恢复、验证收口、完成态，以及 `feature_stage` / `stage_status` 漂移、`ready/complete` metadata 不一致、设计审批证据缺失、`task_count` 缺失或不匹配、重复任务 ID、多个 `DOING`、`DONE` 任务交付记录缺失或弱描述、handoff 缺少配置 / SQL / 部署事项、verification 未覆盖全部 acceptance criteria 等防误推进场景。
