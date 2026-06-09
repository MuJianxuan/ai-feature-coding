# Ship Solo Scope Detection

Scope detection 用来防止个人开发时不知不觉扩大任务。

## Scope Fields

```yaml
scope:
  in_scope: []
  out_of_scope: []
  assumptions: []
  accepted_risks: []
```

## Rules

- In scope 必须能映射到 AC 或验证方式。
- Out of scope 用于明确不做什么。
- Assumptions 必须可验证或可被用户确认。
- Accepted risks 只记录用户明确接受的风险；没有则保持空。

## Scope Changes

如果 build 中发现必须扩大范围：

1. 停止修改。
2. 说明为什么当前 `allowed_files` 或 AC 不够。
3. 更新 `plan.md` 和 `meta.yml.scope`。
4. 让用户确认扩大、缩小或拆成 follow-up。

不再使用设计评审冻结 scope 的默认模式；需要 strict mode 时，用 `accepted_risks` 和 handoff 记录风险接受。
