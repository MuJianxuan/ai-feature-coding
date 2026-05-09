# AI Skills Onboarding 实践指南

> 适用对象：第一次使用、维护或接入本仓库 `skills/ai-*` 工作流的人。
>
> 核心目标：让使用者明确知道**什么时候可以启动 AI Feature Workflow、启动后每一步如何推进、如何避免普通任务误触发、如何验证配置没有漂移**。

## 1. 一句话理解 AI Feature Workflow

这是一套 **explicit opt-in / orchestrator-routed-only** 的 **AI Feature Workflow**。

也就是说：

- 普通“帮我写代码 / 查 bug / 设计方案 / 拆任务 / 做验证”不会自动触发 AI Feature Workflow。
- 只有用户明确指定 `ai-feature-orchestrator` 或某个阶段 skill，才允许启动。
- 阶段 skill 被动触发时，必须由合法上游显式路由，并携带完整 route payload。
- 默认一次只推进一个阶段；跨阶段继续需要用户再次确认。

## 2. Source of truth

维护或排查时优先看这些文件：

| 文件 | 用途 |
| --- | --- |
| `skills/ai-feature-orchestrator/WORKFLOW_CONTRACT.md` | 全局契约：activation、route、metadata、gate、safety、resume、smoke-test 规则。 |
| `skills/ai-feature-orchestrator/SKILL.md` | 总调度入口：入口模式、阶段推断、阶段路由、停止点。 |
| `skills/*/SKILL.md` | 各阶段 skill 的 activation policy、route contract、preflight、阶段行为。 |
| `skills/*/agents/openai.yaml` | 运行时触发策略，必须保持 `allow_implicit_invocation: false`。 |
| `skills/ai-feature-orchestrator/assets/feature-template/` | 新 feature 目录模板。 |
| `skills/ai-feature-orchestrator/references/golden-examples.md` | Happy path、blocked、resume、verification failed 的行为样例。 |
| `skills/ai-feature-orchestrator/scripts/validate_ai_skills.py` | AI Feature Workflow 的 smoke test。 |

## 3. 角色与阶段

| 阶段 | Skill | 主要产物 | 进入条件 |
| --- | --- | --- | --- |
| 总调度 | `ai-feature-orchestrator` | 阶段判断、route payload | 用户显式要求启动 AI Feature Workflow。 |
| 需求澄清 | `ai-requirement-intake` | `requirements.md` | 需求 scope / acceptance criteria 未稳定。 |
| 仓库勘察 | `ai-repo-investigation` | `investigation.md` | 需要真实代码链路、数据来源、接口证据。 |
| 技术设计 | `ai-technical-design` | `design.md` | requirements 和 investigation 已 ready。 |
| 设计审批 | orchestrator / user gate | `design.md approval_status` | design ready 后等待用户明确批准。 |
| 任务拆解 | `ai-task-planning` | `tasks.md` | design 已 ready 且 `approval_status: approved`。 |
| 编码执行 | `ai-implementation-execution` | 代码改动、任务交付记录 | tasks 中存在真实 `TODO` / `DOING` 任务。 |
| 验证收口 | `ai-verification-closeout` | `verification.md`、`handoff.md` | in-scope tasks 已完成或有明确 blocked 说明。 |

## 4. 正确启动方式

### 4.1 新 feature

推荐说法：

```text
使用 ai-feature-orchestrator，为这个需求启动一条新的 AI Feature Workflow：<需求描述>
```

期望行为：

1. Orchestrator 创建 `.docs/feature-YYYYMMDD-short-name/`。
2. 从 `assets/feature-template/` 复制模板。
3. 写入初始需求资料索引。
4. 路由到 `ai-requirement-intake`。
5. 完成一个阶段后停下，等待用户确认是否继续。

### 4.2 继续已有 feature

推荐说法：

```text
使用 ai-feature-orchestrator，继续 .docs/feature-YYYYMMDD-short-name/
```

期望行为：

1. Orchestrator 读取该目录下的阶段文档。
2. 基于 frontmatter 和真实内容判断当前阶段。
3. 生成 route payload。
4. 路由到一个阶段 skill。
5. 阶段完成后停下。

### 4.3 直接调用阶段 skill

可以，但必须提供已有 `feature_dir`。

示例：

```text
使用 ai-task-planning，基于 .docs/feature-20260509-example/ 的 design.md 拆 tasks.md
```

如果只说：

```text
使用 ai-task-planning
```

但没有提供 `feature_dir`，阶段 skill 应该停止并提示补充目录，不能自己猜目录。

## 5. 禁止启动的普通场景

下面这些请求**不应触发**AI Feature Workflow：

| 用户请求 | 应采取的行为 |
| --- | --- |
| “帮我查一下这个 bug” | 走普通 debugging，不启动 `ai-repo-investigation`。 |
| “帮我实现这个功能” | 走普通开发流程，不启动 `ai-implementation-execution`。 |
| “写个技术方案” | 走普通方案写作，不启动 `ai-technical-design`。 |
| “拆一下任务” | 走普通任务拆解，不启动 `ai-task-planning`。 |
| “跑一下测试并总结” | 走普通验证，不启动 `ai-verification-closeout`。 |

除非用户明确写出 skill 名或“使用这套 AI Feature Workflow / 技能工作流”。

## 6. Route payload 规范

被动路由到阶段 skill 时必须包含：

```yaml
activation_source: ai-feature-orchestrator
feature_dir: .docs/feature-YYYYMMDD-short-name
stage_evidence:
  reason: "命中哪个阶段推断规则"
  files:
    - path: .docs/feature-YYYYMMDD-short-name/requirements.md
      finding: "stage_status: ready"
```

阶段 skill 收到被动调用后先检查：

1. `activation_source` 是否是合法上游。
2. `feature_dir` 是否明确且存在。
3. `stage_evidence` 是否说明为什么进入本阶段。
4. 本阶段所需前置文档是否存在。

缺任一项：停止，不猜、不补、不继续。

## 7. Feature 目录结构

新 feature 默认目录：

```text
.docs/feature-YYYYMMDD-short-name/
├── README.md
├── requirements.md
├── investigation.md
├── design.md
├── tasks.md
├── verification.md
├── handoff.md
├── resource/
│   └── README.md
└── sql/
    ├── DDL.sql
    ├── DML.sql
    └── ROLLBACK.sql
```

每个阶段文档都应有 frontmatter，例如：

```yaml
---
feature_stage: requirements
stage_status: draft
updated_at: ""
evidence_complete: false
---
```

`updated_at` 在模板中可以为空；一旦阶段被更新，必须使用 ISO 8601 + timezone，例如 `2026-05-09T20:30:00+08:00`。

`design.md` 额外包含审批字段：

```yaml
approval_status: pending
approved_by: ""
approved_at: ""
approval_evidence: ""
```

`README.md`、`resource/README.md` 和 `sql/*.sql` 是辅助资料，不参与阶段推断。

`stage_status` 语义：

| 状态 | 含义 |
| --- | --- |
| `draft` | 阶段产物未完成，不能作为下一阶段输入。 |
| `ready` | 阶段产物已满足下一阶段输入条件。 |
| `blocked` | 存在外部阻塞，停止推进并报告证据。 |
| `complete` | 验证或交付收口完成。 |

## 8. 阶段推进实践

### 8.1 Requirement Intake

目标：把输入需求变成可验证、可追踪的 `requirements.md`。

完成标准：

- 背景、目标、in-scope、out-of-scope 清晰。
- Acceptance Criteria 可被测试、接口响应、日志、UI 行为或数据状态验证。
- 待确认问题区分 blocking / non-blocking。
- 如果还有阻塞，`stage_status: blocked`。
- 如果需求稳定，`stage_status: ready`。

停止点：输出下一阶段建议，不自动进入 investigation。

### 8.2 Repo Investigation

目标：找出真实代码链路、数据来源、接口行为和相似实现。

完成标准：

- `investigation.md` 记录已查文件、关键函数、结论。
- 写清调用链 / 数据流。
- 区分 source of truth、cache、derived state。
- 风险标注为已证实、推断或未验证。
- 证据齐备后 `stage_status: ready`。

停止点：输出下一阶段建议，不自动进入 design。

### 8.3 Technical Design

目标：把 requirements + investigation 转成可拆任务的方案。

完成标准：

- 写清影响范围、目标链路、API / DB / 状态 / 并发 / 日志 / 回滚。
- 明确兼容性和 breaking change。
- 写出验证策略。
- 如果依赖业务决策，`stage_status: blocked`。
- 如果可拆任务，`stage_status: ready`，但 `approval_status: pending`。

停止点：输出下一阶段建议，等待用户明确批准设计，不自动进入 task planning。

### 8.4 Task Planning

目标：把已批准设计拆成原子、可验证、按依赖排序的任务。

前置条件：

- `design.md stage_status: ready`。
- `design.md approval_status: approved`；如果用户刚刚明确批准设计，先补齐 `approved_by`、`approved_at`、`approval_evidence`。

完成标准：

每个真实任务必须包含：

- 稳定 ID，例如 `T01 - ...`。
- `status`。
- 输入。
- 输出。
- 关联模块 / 文件。
- 执行要点。
- 完成判定。
- 风险。
- 交付记录。

更新：

- `tasks.md` 的 `stage_status: ready`。
- `task_count` 改为真实任务数量。

停止点：不自动开始编码。

### 8.5 Implementation Execution

目标：一次只执行一个真实 `TODO` 或 `DOING` 任务。

开始前：

- 读取 requirements / investigation / design / tasks / verification。
- 检查工作区状态。
- 不覆盖用户未提交改动。
- 将当前任务标记为 `DOING`。
- 如果需要启动服务，先记录端口、已有进程、启动日志和停止方式。
- 如果发现 scope 变化，按 `Scope change protocol` 停止并请求确认。

完成后：

- 执行任务完成判定。
- 通过则标记 `DONE`。
- 记录改动文件、验证命令、结果、残余风险。
- 更新 `verification.md` 中对应检查项。

停止点：完成一个任务后停下，不自动执行下一个任务。

### 8.6 Verification Closeout

目标：把 acceptance criteria 和实际证据一一对齐。

完成标准：

- `verification.md` 有验收标准映射表。
- 每条 AC 都有 PASS / FAIL / BLOCKED 结论。
- 失败或未覆盖项写入残余风险。
- `handoff.md` 包含交付摘要、变更范围、配置 / SQL / 部署事项、用户复核入口。
- 如需启动服务或预览，验证记录中应包含端口检查和进程信息。
- 验证完成后 `verification.md stage_status: complete`。
- 交付信息齐备后 `handoff.md stage_status: complete`。

停止点：输出交付状态，不自动 commit / push / 发布。

## 9. Resume 实践

当 AI Feature Workflow 中断或 `tasks.md` 存在 `DOING`：

1. 先读 `tasks.md` 的 `DOING` 任务、交付记录、完成判定。
2. 检查 git diff，区分用户改动和 AI 改动。
3. 对照 `design.md` 和 `verification.md` 找缺失证据。
4. 如果 diff 超出任务范围，停止并报告风险。
5. 不创建重复任务掩盖中断状态。

推荐恢复请求：

```text
使用 ai-feature-orchestrator，恢复 .docs/feature-YYYYMMDD-short-name/ 的当前 DOING 任务
```

## 10. Scope Change 实践

任一阶段发现 scope 变化时，不要直接扩大实现范围。先记录：

1. 触发原因和证据。
2. 影响的 acceptance criteria。
3. 涉及文件和风险。
4. 建议回流更新的阶段文档。

只有用户确认后，才更新 requirements / investigation / design / tasks。

## 11. Smoke Test

每次修改 AI Feature Workflow 后运行：

```bash
python3 skills/ai-feature-orchestrator/scripts/validate_ai_skills.py
```

当前 smoke test 会检查：

- 所有 `agents/openai.yaml` 的 `allow_implicit_invocation` 是 `false`。
- Orchestrator 包含 workflow contract、阶段停止点、安全策略。
- 子 skill 包含 activation policy、route contract、安全策略。
- 模板 Markdown 都有 frontmatter。
- 阶段模板 metadata 可解析，`tasks.md` 包含 `evidence_complete`，`design.md` 包含审批字段。
- 模板不包含容易误判的 fake `TODO` / fake `AC-01` / fake `T01` / fake blocking placeholder。
- Orchestrator blocked 判断顺序正确，不会被 draft/content 判断抢先命中。
- golden examples 文件存在并覆盖 happy path、blocked、resume、verification failed。

## 12. Onboarding Checklist

新人上手时按这个顺序：

1. 阅读 `WORKFLOW_CONTRACT.md`，理解 explicit-only 和 route contract。
2. 阅读 `ai-feature-orchestrator/SKILL.md`，理解入口模式和阶段推断。
3. 阅读一个子 skill，例如 `ai-task-planning/SKILL.md`，确认 direct / routed 两种启动模式。
4. 查看 `assets/feature-template/`，理解 feature 目录结构。
5. 查看 `references/golden-examples.md`，理解正常推进、阻塞、恢复和失败验证。
6. 运行 smoke test。
7. 用只读方式模拟一个已有 feature 目录的阶段判断。
8. 真正执行时，一次只推进一个阶段，并在阶段结束后等待用户确认。

## 13. 常见反模式

| 反模式 | 后果 | 正确做法 |
| --- | --- | --- |
| 普通 bug 排查自动触发 `ai-repo-investigation` | 缺少 feature dir，文档链路混乱。 | 只有显式指定 skill 才触发。 |
| 子 skill 自己创建 `.docs/feature-*` | 绕过 orchestrator，阶段资料不完整。 | 新建只能由 orchestrator 做。 |
| 只 grep `TODO` 判断任务 | 模板占位导致误判。 | 结合 frontmatter、真实任务结构和 task_count。 |
| 一个阶段完成后自动进下一阶段 | 违反一次一步原则。 | 输出下一步建议，等待用户确认。 |
| 编码时跳过 `tasks.md` | 任务状态和交付证据断裂。 | 只能执行真实 `TODO` / `DOING` 任务。 |
| 验证失败但写成完成 | 交付不可复核。 | FAIL / BLOCKED 必须写入残余风险。 |
| `design.md ready` 就直接拆任务 | 绕过用户审批。 | 必须等 `approval_status: approved`。 |
| 启动服务前不查端口 | 可能占用或误杀无关进程。 | 先记录端口和已有进程。 |

## 14. 维护建议

- 修改任一 `SKILL.md` 后同步检查 `WORKFLOW_CONTRACT.md` 是否需要更新。
- 修改 template 后运行 smoke test，避免引入会误判的 placeholder。
- 修改 route 字段时，同步更新 orchestrator、子 skill、contract、smoke test。
- 修改设计审批、scope change 或服务启动规则时，同步更新 contract、相关阶段 skill、onboarding guide 和 golden examples。
- 新增阶段 skill 时，必须补齐：
  - `Activation policy`
  - `启动模式与 route contract`
  - `前置检查`
  - `Safety policy`
  - 输出 metadata 更新规则
  - smoke test 断言
