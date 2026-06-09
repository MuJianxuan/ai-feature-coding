# Ship Solo Gate Protocol

新版默认使用轻量门禁。门禁是检查清单，不是审批系统。

## Gates

| Gate | Question | Evidence |
|---|---|---|
| Scope | 目标、非目标、AC 是否清楚？ | `brief.md` |
| Reality | 是否读过相关代码、测试、配置和文档？ | `context-map.md` |
| Contract | 边界或不变量是否足够实现？ | `contract.md` |
| Slice | 下一步是否足够小、文件范围是否明确？ | `plan.md` |
| Evidence | 验证是否映射到 AC？ | `verification.md` |
| Close | 风险和 follow-up 是否清楚？ | `handoff.md` |

## Review Checklists

Review skills 只产生 checklist：

```yaml
review_status: pass | needs_revision | blocked
findings:
  - severity: critical | major | minor
    evidence: ""
    recommendation: ""
```

`pass` 不代表用户签字。Critical finding 必须修复、缩 scope，或记录用户接受的风险。

## Strict Mode

如果用户明确要求 strict mode，可以记录：

```yaml
accepted_risks:
  - risk: ""
    accepted_by: user
    accepted_at: ""
```

strict mode 仍不把 review skills 写入 `current_stage`；它只提高风险记录要求。
