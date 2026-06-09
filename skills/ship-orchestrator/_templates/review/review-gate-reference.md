# Ship Review Checklist Reference

新版 ShipKit 中，`ship-define-review`、`ship-design-review`、`ship-plan-review` 是可选 review checklist，不是默认 runtime stage，也不是 hard gate。

## Frontmatter

```yaml
---
review_stage: ship-plan-review
review_status: pass          # pass | needs_revision | blocked
updated_at: ""
reviewer: agent              # agent | user | subagent
findings: []
---
```

兼容旧字段时允许出现 `user_sign_off`、`signed_at`、`confirmation_id`，但它们不再是默认推进条件。若用户明确要求 strict mode，可把这些字段作为风险接受证据记录。

## Finding Format

```yaml
- severity: critical          # critical | major | minor
  evidence: "file/path or command"
  recommendation: "specific fix"
```

## Runtime Rule

- Review checklist 不写入 `meta.yml.current_stage`。
- `pass` 表示 AI 检查通过，不等于用户签字。
- Critical finding 必须修复、缩 scope，或由用户明确接受风险。
- 子代理可以起草 review，但最终风险接受由主上下文向用户确认。
