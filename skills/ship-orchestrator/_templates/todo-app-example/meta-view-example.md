# TODO Web App — meta.yml 视图示例

本文件展示运行时 `meta.yml` 的推荐展示方式，用来说明：

- `current_stage` 是内部事实源
- `macro_stage` 是默认对外展示视图
- 用户默认应看到“大阶段 + 当前目标 + 下一次决策”，而不是细阶段名列表

## 运行时索引示例

```yaml
feature_name: "TODO Web App"
feature_id: "feature-20260522-todo-app"
created_at: "2026-05-22T10:00:00+08:00"
updated_at: "2026-05-22T16:30:00+08:00"

current_stage: "ship-design-review"

macro_stage:
  current: "design"
  label: "Design"
  summary: "接口契约与前后端方案已完成，正在等待设计评审结论。"
  next_user_decision: "确认 design review 是否通过；若不通过，先修复评审问题。"

pipeline_mode: "standard"
project_context: "new_project"
project_context_evidence: "范本项目，从空目录启动。"
```

## 用户默认看到的内容

```text
当前阶段: Design
当前目标: 接口契约与前后端方案已经完成，正在进入设计评审
下一次需要你的动作: 确认 design review 是否通过
```

## 高级/诊断模式看到的内容

```text
macro_stage.label: Design
current_stage: ship-design-review
upstream_ready:
- api-contract.md
- frontend-design.md
- backend-design.md
```

## 映射规则

| `current_stage` | `macro_stage.current` | 对外标签 |
|-----------------|-----------------------|----------|
| `ship-intake` | `define` | `Define` |
| `ship-intake-review` | `define` | `Define` |
| `ship-tech-discovery` | `design` | `Design` |
| `ship-contract` | `design` | `Design` |
| `ship-frontend-design` | `design` | `Design` |
| `ship-backend-design` | `design` | `Design` |
| `ship-design-review` | `design` | `Design` |
| `ship-delivery-plan` | `build` | `Build` |
| `ship-plan-review` | `build` | `Build` |
| `ship-build` | `build` | `Build` |
| `ship-verify` | `build` | `Build` |
| `ship-handoff` | `close` | `Close` |

## 使用建议

- 给用户展示进度时，默认使用 `macro_stage`
- 做断点恢复、门禁校验、直接调用阶段 skill 时，使用 `current_stage`
- `macro_stage.summary` 应描述当前目标，不要简单重复细阶段名
- `macro_stage.next_user_decision` 应明确指出下一次需要用户确认的动作
