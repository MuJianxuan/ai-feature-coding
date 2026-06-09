---
name: ship-define
description: "Ship solo workflow define stage. Turns intent, bug reports, PRDs, or repository findings into a lightweight brief with acceptance criteria, assumptions, and risks."
---

# Ship Define

目标：产出足够实现和验证的 `brief.md`，不是写厚重 PRD。

## Inputs

- `intent.md` 或用户原始需求。
- bug 复现信息、截图、日志、issue、PRD 或代码路径。
- 已确认的范围和非目标。

## Process

1. 归纳一句话目标。
2. 写 In Scope / Out of Scope。
3. 写可验证 AC；小任务 1-3 条即可。
4. 标注假设、风险、需要用户决定的问题。
5. 如果阻塞项能通过读仓库解决，先读仓库；否则问用户。

## Output: brief.md

```markdown
---
stage: ship-define
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Brief

## Goal
## In Scope
## Out of Scope
## Acceptance Criteria
- AC-001: ...
## Assumptions
## Risks
## Questions
```

## Completion Criteria

- 每个 In Scope 项至少有一个 AC 或明确验证方式。
- 非目标足够防止 scope creep。
- 没有核心业务规则、权限、安全、数据一致性类 blocking gap。
- 可以进入 `ship-tech-discovery`。
