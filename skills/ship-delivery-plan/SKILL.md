---
name: ship-delivery-plan
description: "Ship solo workflow planning stage. Breaks the work into small implementation slices with allowed files, verification commands, dependencies, and rollback notes."
---

# Ship Delivery Plan

目标：产出 `plan.md`，让 `ship-build` 可以一次只做一个明确 slice。

## Inputs

- `brief.md`
- `context-map.md`
- `contract.md`
- 用户约束和仓库事实

## Process

1. 按依赖顺序拆 slices。
2. 每个 slice 必须小到能单独验证。
3. 为每个 slice 写目标、允许文件、AC refs、验证命令。
4. 标注依赖、风险、回滚方式。
5. 选择第一个可执行 slice，置为 `DOING` 前先确认没有越界。

## Output: plan.md

```markdown
---
stage: ship-delivery-plan
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Delivery Plan

## Slice S-001: <title>
- status: TODO
- ac_refs: [AC-001]
- allowed_files:
  - src/example.ts
- verification_command: pnpm test src/example.test.ts
- rollback: revert this slice changes

### 任务目标
### 上下文
### 约束
### 验收
### 输出
```

## Completion Criteria

- 至少有一个可执行 slice。
- 每个 slice 有 `allowed_files` 和 `verification_command`。
- 同一时刻最多一个 `DOING`。
- 如果发现需要扩大文件范围，先更新 plan，不直接改。
