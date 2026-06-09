---
name: ship-define-review
description: "Optional Ship review checklist for briefs and requirements. Use when the user asks to review scope/AC quality or when the task is risky; it is not a default hard gate."
---

# Ship Define Review

支持 skill，用于检查 `brief.md` 或需求描述是否足够进入理解/设计。新版中它不是 hard gate，不要求用户签字。

## Check

- Goal 是否具体。
- In Scope / Out of Scope 是否能防止 scope creep。
- AC 是否可验证。
- 权限、安全、数据一致性、边界条件是否有遗漏。
- blocking gaps 是否真的不能通过仓库探索解决。

## Output

```markdown
---
review_stage: ship-define-review
review_status: pass
updated_at: ""
---

# Define Review

## Verdict
pass | needs_revision | blocked

## Findings
- severity: major
  evidence: brief.md#...
  recommendation: ...

## Required Before Next Step
```

## Boundary

`pass` 表示 checklist 通过，不代表用户签字。Critical / Major 问题应修复、缩 scope 或让用户明确接受风险。
