---
name: ship-handoff
description: "Ship solo workflow close stage. Produces a concise delivery summary with changed files, verification evidence, known risks, and next actions."
---

# Ship Handoff

目标：写 `handoff.md`，让个人开发者清楚知道这次完成了什么、如何验证、还有什么风险。

## Inputs

- `brief.md`
- `plan.md`
- `build-log.md`
- `verification.md`
- git diff / 测试输出 / 用户接受的风险

## Process

1. 总结变更范围。
2. 列出关键文件和行为变化。
3. 摘要验证命令与结果。
4. 列出 FAIL / BLOCKED / accepted risk。
5. 给出下一步：继续下一个 slice、提交、部署、补测试或停止。

## Output: handoff.md

```markdown
---
stage: ship-handoff
stage_status: complete
updated_at: ""
blocking_gaps: []
evidence: []
---

# Handoff

## Summary
## Changed Files
## Verification
## Known Risks
## Follow-ups
## Suggested Next Action
```

## Completion Criteria

- 用户能用 handoff 判断是否可以停下或继续。
- 验证证据和残余风险清楚。
- 后续建议具体，不泛泛而谈。
