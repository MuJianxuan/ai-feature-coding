---
name: ship-discover
description: "Ship solo workflow discovery stage. Use when a request is vague, a feature idea needs shaping, or a change needs scope and success criteria before planning."
---

# Ship Discover

目标：把模糊请求变成可以继续推进的 `intent.md`。个人开发者场景下，本阶段要短：只澄清会影响方向、范围或验收的问题。

## Inputs

- 用户原始想法、bug 描述或变更请求。
- 已有截图、PRD、issue、代码路径或旧 feature 文档。
- 仓库中可直接查到的事实。

## Process

1. 判断这是 feature、bugfix、refactor、ui、docs 还是 release。
2. 先查能从仓库得到的事实，不把可验证问题丢给用户。
3. 明确目标用户、当前痛点、期望结果、非目标。
4. 列出 2-3 个可行范围选项，只在确实有取舍时让用户选。
5. 写 `intent.md`，状态为 `ready` 或 `blocked`。

## Output: intent.md

```markdown
---
stage: ship-discover
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Intent

## Goal
## Context Checked
## In Scope
## Out of Scope
## Success Signals
## Open Questions
## Recommended Next Stage
```

## Completion Criteria

- 目标和非目标清楚。
- 用户真正想解决的问题被复述准确。
- 没有会影响方向的 blocking gap。
- 下一阶段是 `ship-define`，或对 bugfix/refactor 可直接到 `ship-tech-discovery`。
