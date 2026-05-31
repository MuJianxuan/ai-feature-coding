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
