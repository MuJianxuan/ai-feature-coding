---
name: ship-verify
description: "Ship solo workflow verification stage. Runs targeted checks, reviews diffs, maps evidence to acceptance criteria, and identifies residual risks before handoff."
---

# Ship Verify

目标：产出 `verification.md`，证明改动满足 AC，或明确哪里失败、阻塞、需接受风险。

## Inputs

- `brief.md` AC
- `plan.md` slices
- `build-log.md`
- 测试、构建、lint、截图、手工验证输出

## Process

1. 汇总已运行的验证命令和结果。
2. 必要时补跑最小相关测试，再考虑更广测试。
3. 对照每条 AC 写 PASS / FAIL / BLOCKED / N/A。
4. Review diff：确认没有越界改动、调试代码、无关格式化或未说明风险。
5. 写残余风险和建议。

## Output: verification.md

```markdown
---
stage: ship-verify
stage_status: ready
updated_at: ""
blocking_gaps: []
evidence: []
---

# Verification

## Commands
## AC Mapping
| AC | Result | Evidence |
|---|---|---|
## Diff Review
## Residual Risks
```

## Completion Criteria

- 每条 AC 有结果和证据。
- 失败或阻塞项没有被隐藏。
- 无法运行的验证有明确原因和替代证据。
- 可以进入 `ship-handoff`。
