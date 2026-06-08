---
name: ship-grill-me
description: Assistive questioning skill for ShipKit. Only use as a ShipKit stage hook or explicit advanced diagnostic; never as a workflow entry. It asks one blocking decision question at a time before stage ready/sign-off and never replaces review gates.
---

Interview only the current artifact's unresolved blocking decisions until the next safe workflow action is clear. For each question, provide your recommended answer and cite evidence already checked.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Workflow Boundaries

- `ship-grill-me` 是辅助质询 skill，不是 canonical stage。
- 不修改 `meta.yml`。
- 不修改正式 artifact frontmatter。
- 不替用户 sign off，也不写 hard gate 最终结论。
- 不绕过 validator、review gate 或 stage transition check。
- 在 forbidden stage / node 中不可作为 subagent 启动，包括 `ship-contract`、`ship-tech-discovery.selection`、`ship-delivery-plan` 和任何正式状态推进动作。

## Grill Output

- Decision branch:
- Question:
- Recommended answer:
- Evidence checked:
- User answer:
- Impact on current artifact:
- Blocking status: blocking | non_blocking | resolved

## Question Discipline

- 一次只问一个问题。
- 先说明为什么这个问题阻塞或影响质量。
- 每个问题必须给出 recommended answer。
- 如果用户采纳 recommended answer，将其记录为明确决策。
- 能从仓库、已有 feature 文档、API、DB、页面、权限或测试命令确认的问题，先探索证据，不问用户。
- 只把业务取舍、风险接受、scope 裁剪、无法从证据确认且会影响当前产物的问题交给用户。
