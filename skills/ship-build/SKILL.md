---
name: ship-build
description: "Ship solo workflow build stage. Implements one DOING slice at a time with surgical code changes, scoped files, and immediate verification."
---

# Ship Build

目标：按 `plan.md` 一次实现一个 DOING slice，并把结果写入 `build-log.md`。不要顺手重构或扩大范围。

## Entry Conditions

- `plan.md` 存在至少一个 slice。
- 当前 slice 为 `DOING` 或用户明确选择要开始的 slice。
- 当前 slice 有 `allowed_files`、AC refs、`verification_command`。
- 已读取相关现有文件。

## Process

1. 读取当前 DOING slice。
2. 运行或检查 `implementation_preflight.py --files <paths...>`（如本仓库使用该 helper）。
3. 只修改 `allowed_files` 覆盖的文件。
4. 实现最小代码变化。
5. 运行 slice 的验证命令。
6. 验证失败时诊断根因，最多迭代到明确失败原因；不要盲目重试。
7. 更新 `build-log.md` 和 slice evidence。

## Output: build-log.md

```markdown
---
stage: ship-build
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Build Log

## Slice S-001
- changed_files:
- verification_command:
- result:
- notes:
```

## Completion Criteria

- 当前 slice 的代码已完成或明确 blocked。
- 验证命令已运行，或说明无法运行的具体原因。
- 改动没有超出 allowed files；若超出，已获得用户确认并更新 plan。
- 可以进入下一个 slice 或 `ship-verify`。
