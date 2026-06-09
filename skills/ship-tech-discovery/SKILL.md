---
name: ship-tech-discovery
description: "Ship solo workflow understand stage. Use before implementation to inspect existing code, tests, configs, docs, dependencies, and runtime constraints with evidence."
---

# Ship Tech Discovery

目标：产出 `context-map.md`，确保后续设计和编码基于仓库事实，而不是猜测。

## Inputs

- `brief.md`、bug 现象、代码路径、日志或技术方案片段。
- 当前仓库文件、测试、配置、依赖和已有文档。

## Process

1. 定位相关模块、入口、调用链、测试和配置。
2. 记录现有行为与目标行为的差异。
3. 找出可复用、需要扩展、不能碰、风险未知的区域。
4. 若涉及第三方 API / 新库 / 版本差异，查官方文档或可靠来源。
5. 写出实现约束和推荐方向。

## Output: context-map.md

```markdown
---
stage: ship-tech-discovery
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Context Map

## Relevant Files
## Current Behavior
## Constraints
## Existing Tests
## Reuse / Extend / Avoid
## Risks
## Recommended Direction
```

## Completion Criteria

- 关键文件和现有行为有路径证据。
- 明确哪些文件可改、哪些只能读、哪些风险未知。
- 后续 contract 或 plan 不再依赖“猜测”。
