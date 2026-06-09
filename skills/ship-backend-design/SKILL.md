---
name: ship-backend-design
description: "Optional Ship support skill for complex backend design. Use when a task needs deeper domain, data, transaction, service, job, queue, permission, or deployment design before planning."
---

# Ship Backend Design

支持 skill，不是默认 runtime stage。小后端改动直接走 `ship-contract → ship-delivery-plan`；复杂后端才调用本 skill。

## Use When

- 涉及数据库迁移、事务、一致性、权限、安全、worker、MQ、cron。
- 多模块或多服务协作。
- 现有 backend surface 需要谨慎复用或扩展。

## Output

`backend-design.md` 或 `resource/backend-design.md`：

- Domain / service boundaries
- Data model and migration notes
- Contract-to-implementation map
- Transaction and consistency strategy
- Runtime jobs/events/queues
- Security and observability notes
- Risks and rollback notes

## Completion Criteria

- 设计能直接拆 slices。
- 数据和事务风险明确。
- 每个关键决定有代码、文档或用户确认依据。
