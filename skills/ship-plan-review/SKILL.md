---
name: ship-plan-review
description: "Optional Ship review checklist for delivery plans. Use to check slice size, dependencies, allowed files, verification commands, and rollback notes; not a default hard gate."
---

# Ship Plan Review

支持 skill，用于检查 `plan.md` 是否适合个人开发者逐 slice 执行。

## Check

- 每个 slice 是否小到可单独验证。
- 是否有唯一 DOING slice。
- `allowed_files` 是否过宽或缺失。
- `verification_command` 是否具体。
- AC refs、依赖、rollback 是否清楚。
- 是否包含无关重构或未来功能。

## Output

```markdown
---
review_stage: ship-plan-review
review_status: pass
updated_at: ""
---

# Plan Review

## Verdict
## Slice Issues
## Dependency Issues
## Verification Gaps
## Recommended Fixes
```

## Boundary

本 skill 不要求 `user_sign_off`，也不阻止轻量流程继续；Critical 问题必须修复、缩 scope 或记录风险接受。
