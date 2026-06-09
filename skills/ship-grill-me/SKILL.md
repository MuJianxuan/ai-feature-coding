---
name: ship-grill-me
description: "Optional Ship support skill for one-question-at-a-time decision grilling. Use when exactly one blocking product, scope, risk, or trade-off question must be resolved before the next safe action."
---

# Ship Grill Me

一次只问一个真正阻塞的问题。能从仓库、文档、测试、日志或现有产物查到答案时，先查，不问用户。

## Use When

- 需要用户做业务取舍。
- 需要用户接受风险或缩 scope。
- 下一步有两个合理方向，且选择会改变实现。

## Output

```markdown
Decision branch:
Question:
Why it matters:
Recommended answer:
Evidence checked:
If user chooses A:
If user chooses B:
Blocking status: blocking | non_blocking | resolved
```

## Boundaries

- 不修改 `meta.yml`。
- 不替用户批准 review。
- 不连续抛出一串问题。
- 不问能从仓库事实中自行确认的问题。
