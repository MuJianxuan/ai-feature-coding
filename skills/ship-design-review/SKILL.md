---
name: ship-design-review
description: "Optional Ship review checklist for contracts and technical design. Use to check consistency, feasibility, and overengineering risk before planning; not a default hard gate."
---

# Ship Design Review

支持 skill，用于检查 `contract.md`、`context-map.md` 和可选前后端设计是否一致。

## Check

- Contract 是否覆盖 AC。
- 是否过度设计或 speculative abstraction。
- 是否忽略现有代码约束。
- API / event / data / UI state 是否自洽。
- 风险是否能通过 plan slice 验证。

## Output

```markdown
---
review_stage: ship-design-review
review_status: pass
updated_at: ""
---

# Design Review

## Verdict
## Findings
## Overengineering Risks
## Missing Evidence
## Recommendation
```

## Boundary

本 skill 不推进 `meta.yml.current_stage`，不替用户做风险接受决定。
