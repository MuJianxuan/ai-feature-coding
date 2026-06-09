---
name: ship-spec
description: "Optional Ship utility for lightweight workspace conventions. Use to read, reference, or propose reusable coding specs without turning them into workflow stages."
---

# Ship Spec

`ship-spec` 是 utility，不是 runtime stage。它帮助个人开发者沉淀和复用项目规则，但不打断当前 slice。

## Use When

- 需要读取已有 `.docs/spec` 规范。
- 某个模式会重复出现，值得沉淀。
- review 或 verify 发现同类问题反复发生。

## Default Layout

```text
.docs/spec/
├── INDEX.md
├── frontend/
├── backend/
└── shared/
```

## Rules

- build 中途不要为了“顺手整理”打断当前 slice 写规范。
- 新规范默认作为 proposal 写入 handoff，用户确认后再落地。
- 引用规范时记录 `spec_id` 和文件路径。
- 没有规范时记录 warning，不阻塞轻量流程。

## Proposal Format

```markdown
## Spec Proposal
- spec_id:
- reason:
- repeated evidence:
- suggested location:
- draft rule:
```
