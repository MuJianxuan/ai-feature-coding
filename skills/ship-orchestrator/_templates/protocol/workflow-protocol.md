# Workflow Protocol

> `skills` 的单一共享协议源。凡是涉及阶段标识、门禁字段、状态机、产物 ownership 的说明，以本文件为准；README、orchestrator、各阶段 SKILL 仅做引用和补充，不再各自发明协议。

## 1. Canonical Stage IDs

唯一合法的阶段标识如下：

| 顺序 | Stage ID | 主要产物 |
|------|----------|---------|
| 01 | `ship-intake` | `requirements.md` |
| 02 | `ship-intake-review` | `review-requirement.md` |
| 03 | `ship-research` | `tech-research.md` |
| 04 | `ship-stack` | `tech-selection.md` |
| 05 | `ship-contract` | `api-contract.md` |
| 06 | `ship-frontend-design` | `frontend-design.md` |
| 07 | `ship-backend-design` | `backend-design.md` |
| 08 | `ship-design-review` | `review-design.md` |
| 09 | `ship-frontend-plan` | `frontend-plan.md` |
| 10 | `ship-backend-plan` | `backend-plan.md` |
| 11 | `ship-plan-review` | `review-plan.md` |
| 12 | `ship-build` | 代码 + 任务状态 |
| 13 | `ship-verify` | `verification.md`（测试章节） |
| 14 | `ship-handoff` | `verification.md`（验收结论）+ `handoff.md` |

禁止在 `current_stage`、`meta.yml.stages.*`、门禁协议、路由规则中混用 `requirement-intake`、`api-contract-design`、`implementation`、`acceptance` 等别名。

## 2. Macro Stage View

对外默认展示四个大阶段；它们是展示层和索引层概念，不替代 Canonical Stage IDs。

| Macro Stage | 展示标签 | 包含的 Canonical Stage IDs |
|-------------|----------|----------------------------|
| `define` | `Define` | `ship-intake`, `ship-intake-review` |
| `design` | `Design` | `ship-research`, `ship-stack`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `build` | `Build` | `ship-frontend-plan`, `ship-backend-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `close` | `Close` | `ship-handoff` |

使用规则：

- `current_stage` 仍然只允许写 Canonical Stage IDs。
- `macro_stage` 是 `meta.yml` 中的展示/摘要字段，用于默认用户视图、状态列表和执行摘要。
- 对外默认显示 `macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`；只有在恢复断点、排查阻塞、直接调用具体阶段时，才展开到 `current_stage`。

## 3. Source of Truth

- **阶段文档 frontmatter 是事实源**：阶段是否 `ready` / `draft`、评审是否 `approved`，以对应产物文档 frontmatter 为准。
- **`meta.yml` 是索引层**：服务于 orchestrator 的恢复、列表、汇总、快速路由；允许缓存摘要状态，但不得与文档 frontmatter 形成第二套真相。
- 当 `meta.yml` 与产物 frontmatter 冲突时，**优先信任产物文档**，然后回写修正 `meta.yml`。

## 4. Non-Review Artifact Contract

所有非评审阶段产物的 frontmatter 最小集合：

```yaml
---
stage: <canonical-stage-id>
stage_status: draft  # draft / ready / complete（按阶段适用）
updated_at: ""
evidence_complete: false
---
```

说明：

- `draft`：产物尚未完成，或证据/前置条件不足。
- `ready`：允许进入下一阶段，但不代表所有最终验收已结束。
- `complete`：仅用于最终态产物，如 `verification.md` 在 `ship-handoff` 完成后。

## 5. Review Gate Contract

所有硬门禁评审文档使用同一 frontmatter 协议：

```yaml
---
stage: <ship-intake-review | ship-design-review | ship-plan-review>
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""
reviewed_at: ""
reviewed_documents: []
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
---
```

推进规则：

- 只有 `review_status: approved` 且 `user_sign_off`、`signed_at` 非空时，才允许推进。
- `rejected`：必须回退到上一个产出阶段。
- `revision_needed`：必须修复列出的 Critical / Major 问题后重审。
- `approved` 是 `meta.yml` 可选缓存字段，不是评审文档事实源。

## 6. meta.yml Summary Contract

`meta.yml` 记录 orchestrator 摘要状态时遵循：

- 普通阶段摘要状态：`pending / in_progress / ready / blocked / completed`
- 评审阶段摘要状态：`pending / in_progress / approved / rejected / revision_needed`
- `current_stage` 只允许使用 Canonical Stage IDs
- `macro_stage.current` 只允许使用 `define / design / build / close`
- `macro_stage.label` 只允许使用 `Define / Design / Build / Close`
- `macro_stage.summary` 面向默认用户视图，描述当前目标而不是暴露细阶段名
- `macro_stage.next_user_decision` 记录下一次需要用户确认的动作或门禁

推荐策略：

- 阶段开始时：`in_progress`
- 阶段产物达到可推进条件时：`ready` 或评审结果状态
- orchestrator 成功完成阶段切换后：上一阶段记为 `completed`，下一阶段写入 `current_stage`
- 每次 `current_stage` 变化时，同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`

## 7. Testing / Handoff Ownership

`verification.md` 是跨 13/14 两阶段共享的验收证据文件，ownership 分工如下：

- `ship-verify`：
  - 创建或更新 `verification.md`
  - 负责自动化测试结果、覆盖率、失败分类、环境说明
  - 自动化验证通过后将 `verification.md.stage_status` 置为 `ready`
- `ship-handoff`：
  - 读取 `verification.md`
  - 补齐 AC 映射、手工验证、残余风险、最终验收结论
  - 完成后将 `verification.md.stage_status` 置为 `complete` 或保留 `draft`
  - 产出 `handoff.md`

`ship-build` 只负责任务级验证与 plan 状态，不拥有 `verification.md`。

## 8. Fast-Track Rules

fast-track 是受控子流程，不是“跳过流程直接编码”。

- 最小路径固定为：`ship-intake → ship-intake-review → ship-build → ship-verify → ship-handoff`
- 不允许绕过 `ship-intake-review`
- 若未生成设计/计划文档，必须在启动确认或需求评审中明确记录 fast-track 原因和风险
- 一旦发现需求复杂度上升、接口新增、跨端耦合升高，可随时升级回 standard
