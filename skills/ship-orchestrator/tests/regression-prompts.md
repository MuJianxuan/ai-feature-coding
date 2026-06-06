# Ship Workflow Regression Prompts

这些 prompts 用于人工或自动回归验证 skill 行为是否仍符合 workflow 协议。每条 prompt 的期望行为都应能由脚本或产物字段复核。

## 1. Product Provided Entry

```text
启动 ship-orchestrator，为"登录安全增强"开启完整工作流：已有 PRD 和原型，先整理需求。
```

期望：

- scenario = `product_provided`
- `ship-discover` / `ship-shape` skipped
- current_stage = `ship-define`
- 不直接把 raw PRD inbox 标记为 ready

## 2. Unsigned Gate

```text
继续 .docs/feature-demo，review-define.md 已 approved，但还没有用户签字。
```

期望：

- `stage_transition_check.py --target-stage ship-tech-discovery` 不允许推进
- `workflow_doctor.py` 报告 gate sign-off blocker

## 3. Requirements Quality

```text
检查 requirements.md：stage_status=ready，但 AC 没有 Domain ID，待确认问题还有阻塞项。
```

期望：

- `validate_requirements.py` 报错
- `validate_feature_artifacts.py` 同步报告需求质量 blocker

## 4. Delivery Plan DAG

```text
检查 frontend-plan.md / backend-plan.md：两个任务互相 depends_on。
```

期望：

- `validate_delivery_plan.py` 报告 `task_dependency_cycle`

## 5. Build Preflight

```text
准备进入 ship-build，frontend-plan.md 中有两个 DOING 任务。
```

期望：

- `build_task_preflight.py` 报告 `doing_count_invalid`

## 6. Handoff Evidence

```text
准备关闭 feature，verification.md 中 AC-AUTH-001 为 PASS 但没有证据。
```

期望：

- `validate_handoff.py` 报告 `pass_ac_missing_evidence`

## 7. Backend Only Scope Evidence

```text
创建 backend_only feature，但没有提供 project_scope_evidence。
```

期望：

- `feature_meta_runtime.py` 拒绝创建单侧 scope
- `validate_feature_artifacts.py` 报告 `missing_project_scope_evidence`

## 8. Scope Artifact Rejection

```text
backend_only feature 目录里出现 frontend-plan.md，或 frontend_only 目录里出现 backend-design.md。
```

期望：

- `validate_feature_artifacts.py` 报告 `scope_forbidden_artifact`

## 9. Technical Plan File + Section Entry

```text
启动 ship-orchestrator，基于 resource/order-export-tech-design.md 的 3.2 订单导出异步任务章节生成 delivery plan。
```

期望：

- scenario = `technical_plan_provided`
- `project_context = existing_project`
- `technical_plan_source.selected_scope` 非空
- `current_stage = ship-tech-discovery`
- `ship-discover` / `ship-shape` / `ship-define` / `ship-define-review` skipped
- `stages.ship-define.generation_mode = technical_plan`（用于 derived requirements index 兼容标识）

## 10. Technical Plan Pasted Excerpt Entry

```text
这是技术方案片段，只计划 POST /api/v1/orders/export 这一部分，先探索仓库再生成 plan：
<粘贴内容>
```

期望：

- `technical_plan_source.selection_mode = pasted_excerpt`
- 粘贴内容归档为 `resource/technical-plan-excerpt.md`
- `technical_plan_source.pasted_excerpt_file` 非空
- 不创建 raw PRD inbox
- 初始化后直接进入 `ship-tech-discovery`

## 11. Technical Plan Rejects New Project

```text
这是一个全新项目，但我有技术方案，按其中 3.2 章节直接生成计划。
```

期望：

- `feature_meta_runtime.py init --scenario technical_plan_provided --project-context new_project` 拒绝创建
- 报错说明必须是 `existing_project`

## 12. Technical Plan Missing Selected Scope

```text
我有技术方案文件 resource/design.md，按方案生成计划。
```

期望：

- `validate_feature_artifacts.py` 报告 `missing_selected_scope`
- orchestrator 要求用户补充章节名、接口名、模块名或直接粘贴片段

## 13. Technical Plan Direct Delivery Plan Blocked

```text
技术方案选区已提供，跳过设计评审，直接生成 ship-delivery-plan。
```

期望：

- `stage_transition_check.py --target-stage ship-delivery-plan` 不允许推进
- 缺少 `review-design.md approved + user_sign_off + signed_at` 时阻塞

## 14. Technical Plan Plan Contains Unselected Task

```text
selected scope 是 3.2 订单导出，但 backend-plan.md 中生成了订单导入任务。
```

期望：

- `validate_delivery_plan.py` 报告 task 脱离 selected scope
- 未选中内容不得作为实现任务进入 plan

## 15. Technical Plan Init Does Not Create Raw PRD Inbox

```text
使用 technical_plan_provided 初始化 feature。
```

期望：

- 创建 `resource/README.md`
- 不创建 raw PRD inbox 模板形式的 `requirements.md`
- `current_stage = ship-tech-discovery`

## 16. Technical Plan Ready Tech Discovery Requires Derived Requirements

```text
technical_plan_provided 的 tech-research.md 和 tech-selection.md 都是 ready，但缺少 derived requirements.md。
```

期望：

- `validate_tech_discovery.py` 报告 `missing_derived_requirements_index`
- 不允许进入 `ship-contract`

## 17. Technical Plan Requirements Source Index

```text
requirements.md 是 generation_mode: technical_plan 且 stage_status: ready，但没有 selected scope 来源索引。
```

期望：

- `validate_requirements.py` 报告 `technical_plan_missing_source_index`
