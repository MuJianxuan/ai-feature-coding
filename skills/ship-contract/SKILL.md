---
name: ship-contract
description: "Ship solo workflow design stage. Defines the smallest stable contract for APIs, events, CLI, UI state, data shapes, or behavior invariants before planning implementation."
---

# Ship Contract

目标：写 `contract.md`，定义实现必须遵守的最小稳定边界。不是所有任务都需要 HTTP API；refactor 可以写 invariant contract，docs 可以写 `contract_forms: [none]`。

## Contract Forms

- `http`：REST/RPC 请求、响应、错误码。
- `event`：消息、队列、webhook、payload。
- `cli`：命令、参数、退出码、stdout/stderr。
- `ui-state`：页面状态、交互、空态、错误态。
- `data`：字段、迁移、约束、兼容策略。
- `invariant`：重构前后必须保持的行为。
- `none`：文档或极小改动，无独立 contract。

## Process

1. 读取 `brief.md` 和 `context-map.md`。
2. 选择最少 contract forms。
3. 对每个 AC 写对应边界或不变量。
4. 标注兼容性、错误处理、权限/安全、数据迁移影响。
5. 不为“以后可能需要”设计额外扩展点。

## Output: contract.md

```markdown
---
stage: ship-contract
stage_status: ready
updated_at: ""
contract_forms: [invariant]
blocking_gaps: []
evidence: []
---

# Contract

## Forms
## Boundaries
## Data / State
## Error Handling
## Compatibility
## AC Mapping
```

## Completion Criteria

- 每条 AC 都能映射到边界、不变量或明确的“不适用”。
- 没有过度抽象或 speculative design。
- 可以拆成实现 slices。
