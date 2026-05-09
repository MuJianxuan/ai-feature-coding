---
name: ai-feature-orchestrator
description: "AI 需求开发总调度技能。Activation restricted: use only when the user explicitly names `ai-feature-orchestrator`, explicitly asks to use/start this AI feature workflow or skills workflow, or another legally activated skill explicitly routes here. Do not auto-trigger for ordinary feature requests, repo audits, coding, debugging, design, planning, or closeout."
---

# AI Feature Orchestrator

## 目标

把一个需求从输入资料推进到可验证交付。本 skill 是 AI 需求开发工作流的 source of truth，不依赖仓库根部额外 workflow 文档。

需求工作目录默认是 `.docs/feature-YYYYMMDD-short-name/`。模板由本 skill 自带，位于当前 skill 目录下的 `assets/feature-template/`。

## Activation policy

本 skill 是 explicit opt-in，不参与普通 Codex 工作流的自动触发。只有满足以下任一条件，才允许进入本 skill：

1. 用户在当前请求中明确写出 `ai-feature-orchestrator`，或明确要求“使用/启动这套 AI feature workflow / skills workflow / 技能工作流”。
2. 另一个已经合法触发的 skill 在当前上下文中显式路由到本 skill。

不满足以上条件时：

- 禁止把普通“帮我实现功能 / 调查代码 / 写技术方案 / 拆任务 / 验证收口”解读为触发本 skill。
- 禁止创建或选择 `.docs/feature-*` 目录。
- 应回到普通 Codex 工作流；如果用户确实想进入本流程，提示其显式指定本 skill 或“这套 AI feature workflow”。

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
6. 路由到 `ai-requirement-intake`。

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

按顺序检查，命中即停止：

1. `requirements.md` 缺失，或缺少 in-scope / out-of-scope / acceptance criteria：路由到 `ai-requirement-intake`。
2. `requirements.md` 存在 `BLOCKING` 待确认问题：继续 `ai-requirement-intake`，不要进入设计。
3. `investigation.md` 缺失，或没有真实调用链、数据来源、已查文件：路由到 `ai-repo-investigation`。
4. `design.md` 缺失，或没有影响范围、目标链路、风险回滚、验证策略：路由到 `ai-technical-design`。
5. `design.md` 标记 `DESIGN_BLOCKED`：先处理设计阻塞，不进入任务拆解。
6. `tasks.md` 缺失，或任务没有输入、输出、完成判定、关联模块/文件：路由到 `ai-task-planning`。
7. `tasks.md` 存在 `BLOCKED`：报告阻塞任务、已查证据和需要的外部条件；除非用户指定，否则不要跳到其他任务。
8. `tasks.md` 存在 `DOING`：路由到 `ai-implementation-execution`，优先恢复该任务。
9. `tasks.md` 存在 `TODO`：路由到 `ai-implementation-execution`，执行下一项或用户指定项。
10. 所有 in-scope 任务为 `DONE`，但 `verification.md` 未完成 acceptance criteria 映射：路由到 `ai-verification-closeout`。
11. `verification.md` 完成但 `handoff.md` 缺少交付摘要、复核入口或残余风险：路由到 `ai-verification-closeout`。
12. 全部完成：输出交付状态，不重复执行。

## 阶段路由

- `ai-requirement-intake`：澄清需求、scope、acceptance criteria、资料索引。
- `ai-repo-investigation`：查真实代码链路、数据来源、接口行为、相似实现。
- `ai-technical-design`：写技术方案、影响范围、API/DB 变更、风险、回滚和验证策略。
- `ai-task-planning`：把方案拆成可执行、可验证、按依赖排序的 `tasks.md`。
- `ai-implementation-execution`：按 `tasks.md` 执行代码修改并维护任务状态。
- `ai-verification-closeout`：验收映射、回归检查、交付总结和残余风险收口。

路由到任何阶段 skill 时，都必须带上 feature 目录路径和当前阶段判断证据，避免阶段 skill 重新猜目录。

路由消息必须显式包含：

- `activation_source: ai-feature-orchestrator`
- `feature_dir: <相对或绝对路径>`
- `stage_evidence: <命中阶段推断的文件和事实>`

没有上述显式路由信息时，阶段 skill 必须拒绝以“被动触发”身份启动。

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
