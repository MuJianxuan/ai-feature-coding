# Ship Solo Feature Initialization

新版工作项默认初始化到 `.docs/ship/<work-id>/`。

## Directory

```text
.docs/ship/<work-id>/
├── meta.yml
├── intent.md
├── brief.md
├── context-map.md
├── contract.md
├── plan.md
├── build-log.md
├── verification.md
├── handoff.md
├── reviews/
└── resource/
```

只在需要时创建 artifact；不要提前填充空文档制造噪音。

## Meta Defaults

- `schema_version: 3`
- `work_mode: feature | bugfix | refactor | ui | docs | release`
- `flow_policy.strictness: lightweight`
- `flow_policy.review_skills_are_optional: true`
- `current_stage` 使用 8 个 runtime stage 之一
- 支持 skill 状态写入 `support_skills`，不写入 `stages`

## Initialization Steps

1. 生成 work id：`ship-YYYYMMDD-<short-name>`。
2. 复制 `meta.yml.template`。
3. 填写 work title、mode、stage、macro_stage。
4. 如果已有用户材料，放入 `resource/` 并在当前 artifact evidence 中引用。
5. 根据 mode 选择起点：feature/discover，bugfix/refactor/understand，docs/define，release/verify。
