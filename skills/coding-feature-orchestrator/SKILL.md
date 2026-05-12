---
name: coding-feature-orchestrator
description: "Coding Feature Workflow 总调度技能。Activation restricted: use only when the user explicitly names `coding-feature-orchestrator`, explicitly asks to use/start this Coding Feature Workflow or 技能工作流. Do not auto-trigger for ordinary feature requests, repo audits, coding, debugging, design, planning, or closeout."
---

# Coding Feature Orchestrator

## 目标

把一个需求从输入资料推进到可验证交付。本 skill 是 Coding Feature Workflow 的调度入口，不依赖仓库根部额外 workflow 文档。

需求工作目录默认是 `.docs/feature-YYYYMMDD-short-name/`。模板由本 skill 自带，位于当前 skill 目录下的 `assets/feature-template/`。

## Activation policy

本 skill 是 explicit opt-in，不参与普通 Agent 工作流的自动触发。只有满足以下条件，才允许进入本 skill：

- 用户在当前请求中明确写出 `coding-feature-orchestrator`，或明确要求“使用/启动这套 Coding Feature Workflow / 技能工作流”。

本 skill 自身不接受其他 skill 的被动路由；需要调度时必须由用户显式启动本 skill。

不满足以上条件时：

- 禁止把普通“帮我实现功能 / 调查代码 / 写技术方案 / 拆任务 / 验证收口”解读为触发本 skill。
- 禁止创建或选择 `.docs/feature-*` 目录。
- 如果用户确实想进入本流程，提示其显式指定本 skill 或“这套 Coding Feature Workflow”。

## Workflow contract

本工作流的完整契约维护在 `WORKFLOW_CONTRACT.md`。执行前优先遵守该契约中的：

- activation contract：显式触发与被动路由边界。
- route contract：阶段 skill 必须收到的路由字段。
- document metadata：阶段文档 frontmatter 与 `stage_status` 语义。
- gate policy：默认一次只推进一个阶段。
- safety policy：禁止破坏性操作和仓库状态变更。
- design approval / scope change / service startup：设计审批、scope 变更和启动服务前检查。

完整正反例可按需读取 `references/golden-examples.md`；正常执行时不必加载。

## 入口模式

仅在 `Activation policy` 已满足后，才识别用户意图并决定是否创建目录、读取目录或只做审计。

### NEW_FEATURE

模式条件（仅在 `Activation policy` 已满足后判断）：

- 用户给出新的产品需求、PRD、截图、会议纪要、口头需求或接口草案。
- 用户没有指定已有 `.docs/feature-*` 目录。

执行：

1. 生成短名：从需求主题提取英文 kebab-case short-name；无法可靠提取时，用 1 个问题让用户确认。
2. 创建目录：`.docs/feature-YYYYMMDD-short-name/`。
3. 从 `assets/feature-template/` 复制完整模板到新目录。
4. 将用户提供的原始需求资料保存或索引到 `resource/`；如果资料已是仓库文件，只在 `resource/README.md` 记录路径、来源、更新时间和用途。
5. 更新 `requirements.md` 的背景、目标、初始 scope 和待确认问题。
6. 路由到 `coding-requirement-intake`。

### CONTINUE_FEATURE

模式条件（仅在 `Activation policy` 已满足后判断）：

- 用户明确指定已有需求目录。
- 用户说继续实现、继续任务、处理下一项、从某个 feature 目录恢复。

执行：

1. 确认指定目录存在；不存在时只报告缺失，不自动创建同名目录，除非用户明确这是新需求。
2. 读取指定目录下的 `requirements.md`、`investigation.md`、`design.md`、`tasks.md`、`verification.md`、`handoff.md`。
3. 根据“阶段推断”判断当前阶段。
4. 路由到对应阶段 skill，并显式传入该 feature 目录路径。
5. 不创建新目录，不猜测切换到其他 feature 目录。

### INSPECT_FEATURES

模式条件（仅在 `Activation policy` 已满足后判断）：

- 用户没有给新需求资料。
- 用户没有指定需求目录。
- 仓库中存在多个 `.docs/feature-*` 目录。

执行：

1. 列出候选 feature 目录。
2. 对每个目录做轻量状态摘要：当前阶段、是否有 `BLOCKED`、下一步建议。
3. 要求用户指定目录后再继续。
4. 不修改文件，不创建目录。
5. 禁止自行选择“看起来最新”或“最可能”的目录。

### AD_HOC_AUDIT

模式条件（仅在 `Activation policy` 已满足后判断）：

- 用户要求检查当前流程状态、审计目录、看做到哪一步、找缺口。

执行：

1. 只读取和分析，不创建目录，不改代码。
2. 输出当前阶段、缺失文档、阻塞项、下一步建议。
3. 如用户随后要求继续，再按 `CONTINUE_FEATURE` 路由。

## 目录选择规则

- 用户指定 feature 目录时，以用户指定为准。
- 用户给新需求资料时，默认新建 feature 目录，即使仓库中已经有其他 feature 目录。
- 仓库有多个 feature 目录且用户未指定时，只进入 `INSPECT_FEATURES`。
- 仓库没有 `.docs/` 时，只有 `NEW_FEATURE` 才创建 `.docs/`。
- 任何时候都不要把模板目录当成真实 feature 目录。

## 模板定位

把当前 `SKILL.md` 所在目录视为 `SKILL_ROOT`：

```text
SKILL_ROOT/
└── assets/
    └── feature-template/
```

创建新需求目录时，复制 `SKILL_ROOT/assets/feature-template/` 到 `.docs/feature-YYYYMMDD-short-name/`。

## 阶段推断

阶段推断优先读取各阶段文档的 YAML frontmatter；没有 frontmatter 时再按内容结构做 fallback 判断。模板占位内容、空表格、`UNSET`、`<...>`、示例代码块均不算有效内容。

可执行辅助检查器：`scripts/inspect_feature_state.py <feature_dir>` 会按下列规则输出 `state`、`next_skill`、`blocking`、`reason` 和 `evidence`。执行真实流程时仍以本文件和 `WORKFLOW_CONTRACT.md` 为准；维护本套 skill 时必须让该脚本与本节规则保持一致。

`stage_status` 语义：

- `draft`：阶段未完成，继续当前阶段 skill。
- `ready`：阶段产物已满足下一阶段输入条件。
- `blocked`：阶段存在外部阻塞，停止并报告阻塞证据。
- `complete`：收口类阶段已完成。

阶段级合法状态：

- `requirements.md` / `investigation.md` / `design.md` / `tasks.md`：只能使用 `draft` / `ready` / `blocked`；完成当前阶段时标记为 `ready`，不能标记为 `complete`。
- `verification.md` / `handoff.md`：只能使用 `draft` / `blocked` / `complete`；未收口时保持 `draft` 或 `blocked`，不能标记为 `ready`。

按顺序检查，命中即停止：

1. `requirements.md` 缺失，或 `stage_status` 为 `draft`：路由到 `coding-requirement-intake`。
2. `requirements.md` 的 `stage_status` 为 `blocked`，或存在真实阻塞问题：继续 `coding-requirement-intake`，不要进入设计。
3. `requirements.md` 缺少真实 in-scope / out-of-scope / acceptance criteria：路由到 `coding-requirement-intake`。
4. `investigation.md` 缺失：路由到 `coding-repo-investigation`。
5. `investigation.md` 的 `stage_status` 为 `blocked`：停止并报告阻塞证据，不被 draft/content 判断覆盖。
6. `investigation.md` 的 `stage_status` 为 `draft`，或没有真实调用链、数据来源、已查文件：路由到 `coding-repo-investigation`。
7. `design.md` 缺失：路由到 `coding-technical-design`。
8. `design.md` 的 `stage_status` 为 `blocked`，或标记 `DESIGN_BLOCKED`：停止并报告设计阻塞证据，不进入任务拆解。
9. `design.md` 的 `stage_status` 为 `draft`，或没有影响范围、目标链路、风险回滚、验证策略：路由到 `coding-technical-design`。
10. `design.md` 的 `stage_status` 为 `ready`，但 `approval_status` 不是 `approved`，且当前用户请求没有明确批准设计或要求进入任务拆解：停止并提示等待设计审批。
11. 当前用户请求明确批准设计或要求进入任务拆解时，先在 `design.md` 记录 `approval_status: approved`、`approved_by`、`approved_at`、`approval_evidence`，同步更新 `updated_at` 并保持 `evidence_complete: true`，再继续判断。
12. `tasks.md` 缺失：路由到 `coding-task-planning`。
13. `tasks.md` 的 `stage_status` 为 `blocked`：停止并报告任务规划阻塞证据。
14. `tasks.md` 的 `stage_status` 为 `draft`，或任务没有输入、输出、完成判定、关联模块/文件：路由到 `coding-task-planning`。
15. `tasks.md` 的 `task_count` 缺失、不等于真实任务数量，或存在重复真实任务 ID：停止并路由到 `coding-task-planning` 修正任务清单。
16. `tasks.md` 存在真实 `BLOCKED` 任务：报告阻塞任务、已查证据和需要的外部条件；除非用户指定，否则不要跳到其他任务。
17. `tasks.md` 中 `DONE` 任务缺少结构化交付记录（改动文件、验证命令或证据、结果、残余风险）：路由到 `coding-implementation-execution` 补齐交付证据。
18. `tasks.md` 存在多个真实 `DOING` 任务：停止并报告恢复目标歧义，不自行选择任一任务。
19. `tasks.md` 存在一个真实 `DOING` 任务：路由到 `coding-implementation-execution`，优先恢复该任务。
20. `tasks.md` 存在真实 `TODO` 任务：路由到 `coding-implementation-execution`，执行下一项或用户指定项。
21. 所有 in-scope 任务为 `DONE`，但 `verification.md` 未完成 acceptance criteria 映射，或 `stage_status` 不是 `complete`：路由到 `coding-verification-closeout`。
22. `verification.md` 完成但 `handoff.md` 缺少交付摘要、配置 / SQL / 部署事项、复核入口或残余风险，或 `stage_status` 不是 `complete`：路由到 `coding-verification-closeout`。
23. 全部完成：输出交付状态，不重复执行。

## 阶段路由

- `coding-requirement-intake`：澄清需求、scope、acceptance criteria、资料索引。
- `coding-repo-investigation`：查真实代码链路、数据来源、接口行为、相似实现。
- `coding-technical-design`：写技术方案、影响范围、API/DB 变更、风险、回滚和验证策略。
- `coding-task-planning`：把方案拆成可执行、可验证、按依赖排序的 `tasks.md`。
- `coding-implementation-execution`：按 `tasks.md` 执行代码修改并维护任务状态。
- `coding-verification-closeout`：验收映射、回归检查、交付总结和残余风险收口。

路由到任何阶段 skill 时，都必须带上 feature 目录路径和当前阶段判断证据，避免阶段 skill 重新猜目录。

路由消息必须显式包含：

- `activation_source: coding-feature-orchestrator`
- `feature_dir: <相对或绝对路径>`
- `stage_evidence: <命中阶段推断的文件和事实>`

没有上述显式路由信息时，阶段 skill 必须拒绝以“被动触发”身份启动。

## 路由执行机制

本 skill 说“路由到阶段 skill”时，不是只写一句建议，而是必须按当前运行环境选择可执行方式：

1. 如果运行环境支持真实 skill handoff：输出完整 route payload，并交给目标阶段 skill 执行。
2. 如果运行环境没有自动 handoff，但可读取本仓库 `skills/<stage-skill>/SKILL.md`：本 skill 必须读取目标阶段 skill 的 `SKILL.md`，按其规则执行这一阶段，然后停止。
3. 如果目标阶段 skill 不存在或不可读：停止，不伪执行阶段；只输出 route payload、缺失文件路径和下一步建议。

无论采用哪种方式，都必须遵守“默认一次只推进一个阶段”：目标阶段完成后停下，等待用户新的明确确认。

## 阶段停止点

- 默认一次只推进一个阶段：本 skill 可以路由到一个阶段 skill，但该阶段 skill 完成后必须停下并输出下一步建议。
- 跨阶段继续执行前必须有用户新的明确确认，例如“继续下一阶段”或“连续推进”。
- 用户未明确授权连续推进时，禁止阶段 skill 自行调用下一个阶段 skill。
- 只读审计模式只输出状态、缺口和建议，不修改任何文件。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；修改前后都要检查工作区状态。
- 启动服务前必须确认端口和已有进程状态。
- 所有文档用中文写，保留 technical English names、路径、API 名。

## 通用约束

- 文档用中文写，保留 technical English names、路径、API 名。
- 先查证据再决策。不要用猜测替代代码路径、数据来源或接口行为。
- 不要提出可以从仓库中获得答案的问题；先自行搜索、读取文件、执行必要检查。
- 只能从 `tasks.md` 中状态为 `TODO` / `DOING` 或用户明确指定的任务开工。
- 遇到阻塞时，先尝试用仓库、日志、测试、文档自行排查；只有缺少业务意图、账号、密钥、外部权限时才问用户。
- 每次修改后同步更新对应阶段文档，至少记录证据、变更范围、验证结果和残余风险。
- 不删除文件、不切换分支、不提交或推送，除非用户明确许可。

## 输出要求

每次调度后，给出：

- 当前入口模式。
- 使用的 feature 目录。
- 当前阶段判断和证据。
- 下一步调用的 skill。
- 如果需要用户确认，只问一个阻塞问题，并附已查证据。
