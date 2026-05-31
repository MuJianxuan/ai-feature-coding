# Review Gate Reference

三道 hard gate（`ship-define-review`、`ship-design-review`、`ship-plan-review`）共用本协议。阶段 SKILL 只补充阶段专属 checklist，不重新定义 gate 字段。

## Frontmatter

```yaml
---
stage: <ship-define-review | ship-design-review | ship-plan-review>
gate_type: hard
review_status: pending
reviewer: ""
reviewed_at: ""
reviewed_documents: []
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
required_changes: []
---
```

规则：

- 只有 `review_status: approved` 且 `user_sign_off`、`signed_at` 非空时，允许推进。
- 子代理起草 gate 草案时，`review_status` 必须保持 `pending`，`user_sign_off` 与 `signed_at` 必须为空。
- `required_changes` 用于 `rejected` / `revision_needed`，每项必须能定位到上游 artifact。

## Finding Table

每条 finding 至少包含：

| 字段 | 说明 |
|------|------|
| `id` | `C-001` / `M-001` / `m-001` |
| `severity` | Critical / Major / Minor |
| `location` | 文档名 + 章节或行号 |
| `description` | 具体问题 |
| `fix_owner` | requirements / contract / frontend-design / backend-design / delivery-plan / verification / handoff |
| `required_change` | 必须修改的内容 |

## Decision Rules

- 有 Critical finding：不得 approved。
- 有未处理 Major finding：默认 `revision_needed`，除非用户明确接受风险并写入 conditions / risk record。
- Minor finding 不阻塞，但必须记录。
- 用户签字不可代替 review 内容；签字只确认 gate 决策。
