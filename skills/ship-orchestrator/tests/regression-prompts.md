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

## 13b. Technical Plan Direct Coding Blocked

```text
这是技术方案片段，只计划 POST /api/v1/orders/export 这一部分。初始化后直接按方案改代码实现。
```

期望：

- 初始化后 `current_stage = ship-tech-discovery`
- 不修改业务源码、测试、配置、迁移、脚本或构建文件
- orchestrator 报告 Source Code Edit Barrier 阻塞
- 只有 `implementation_preflight.py --files <paths...>` 通过后，才允许进入 `ship-build` 编码；单独运行 `stage_transition_check.py` 或 `build_task_preflight.py` 不构成源码修改授权

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

## 18. UIUX Gate Inserted Shape

```text
B 场景，用户有 PRD 但无设计稿，涉及 UI，用户授权生成线框。
```

期望：

- `ship-shape activation_mode=uiux_material_gate_insert`
- `uiux_gate_user_sign_off` / `uiux_gate_signed_at` 非空
- `ship-discover` 仍为 skipped

## 19. Technical Plan AC Confirmation

```text
E 场景，技术方案 selected scope 无明确 AC。
```

期望：

- derived requirements 保持 draft，直到用户确认 `selected_scope_ac_confirmation`
- ready 时 `selected_scope_ac_confirmed=true`

## 20. Raw Inbox Recovery

```text
B/D 已创建 raw requirements.md，但用户要求进入设计。
```

期望：

- 阻塞在 ship-define normalize
- validator 报告 `raw_inbox_past_define` 或 `raw_inbox_marked_structured`

## 21. Evolve Baseline Required

```text
C 场景未给旧 feature/code/现有功能。
```

期望：

- 不创建目录，先询问 baseline

## 22. Inserted Shape Transition Blocks Define

```text
B 场景已有 PRD、无 UIUX，用户授权生成线框；ship-shape.status=pending，尚无 design-brief.md。
```

期望：

- `stage_transition_check.py --target-stage ship-define` 不允许推进
- `checked_previous_stages` 包含 `ship-shape`
- 缺少 `design-brief.md.stage_status=ready` 时阻塞

## 23. D Backend Only Contract Material Gate

```text
D + backend_only，PRD 只有产品描述，没有 OpenAPI / endpoint list / interface doc / message protocol / CLI spec / SDK / request-response。
```

期望：

- `ship-define-review` Phase 1 P1-6 判定 Critical
- validator 报告 `backend_contract_material_missing`
- 不允许 `review_status=approved`

## 24. E Startup Summary Order

```text
启动 ship-orchestrator，基于 resource/order-export-tech-design.md 的 3.2 章节生成计划。
```

期望启动摘要顺序：

- 技术方案来源与 selected scope
- `ignored_source_policy: out_of_scope`
- 跳过 `ship-define` / `ship-define-review`
- 直接进入 `ship-tech-discovery` 并做 repository scan
- 派生最小 requirements index
- contract 前完成 `selected_scope_ac_confirmation`
- 完成 contract 和裁剪后的 design
- delivery-plan 前通过 `ship-design-review`

## 25. UIUX Material Coverage

```text
B 场景提供一个 Figma 链接但无法访问，或只提供两张截图。
```

期望：

- 不把“有链接”直接判为 sufficient
- inaccessible 要求补材料或授权 `ship-shape`
- partial / screenshot_only 可继续，但 `requirements.md` 或 `design-brief.md` 必须记录 UIUX risk/open question

## 26. Inserted Shape Normalize Order

```text
B/D 先创建 raw requirements.md，之后用户补 PRD，并授权生成线框。
```

期望：

- 回到 `ship-define` 时先 normalize raw inbox
- `design-brief.md` 作为 UIUX source，不覆盖 PRD source
- `generation_mode` 保持 B=`interview`、D=`prd_direct`

## 27. Scope Freeze Drift

```text
ship-design-review 已 approved 后，把 project_scope 从 fullstack 改成 backend_only。
```

期望：

- `validate_feature_artifacts.py` 报告 `scope_freeze_mismatch`
- `stage_transition_check.py --target-stage ship-delivery-plan` 阻塞
- 需要 reopen design-review 并重跑受影响 contract/design/plan

## 28. E AC Source Completeness

```text
technical_plan_provided 的 requirements.md ready，但 AC 行没有 source locator 或 selected scope 边界。
```

期望：

- `validate_requirements.py` 报告 `technical_plan_ac_missing_source_locator` 或 `technical_plan_ac_missing_scope_boundary`
- delivery-plan 任务不得引用未确认 AC ID
- validator 报告 `evolve_source_missing`

## 29. Discover Pre-Ready Grill

```text
启动 ship-orchestrator，我只有一句话想法，帮我在 product brief ready 前 grill 一下方案选择。
```

期望：

- 识别为场景 A，`ship-grill-me` 只作为 `ship-discover.pre-ready` 辅助质询 hook
- 不把 `ship-grill-me` 写入 canonical stage order、`current_stage` 或 `meta.yml.stages`
- 只在产品方向草稿形成后逐题提问，并给出 recommended answer
- blocking grill question 未 resolved 时 `product-brief.md.stage_status` 保持 draft

## 30. Shape Direction Grill

```text
已有 3 个 UI 线框方案，使用 ship-grill-me 帮我选方向，但不要进入 define。
```

期望：

- 使用 `ship-shape.pre-selection`，不推进到 `ship-define`
- 浏览器验证缺失时不得用 grill 风险接受掩盖
- 选择理由写入 `Direction Grill Notes`
- blocking UX state gap 未 resolved 时 `design-brief.md` 不得 ready

## 31. Define Pre-Ready Grill

```text
requirements.md 已成稿，ready 前用 ship-grill-me 逐题确认 scope 和 AC。
```

期望：

- 使用 `ship-define.pre-ready`
- `Grill Confirmation Log` 记录 Question、Recommended Answer、User Decision、Impact、Status
- `validate_feature_artifacts.py` 对 unresolved blocking grill question 报告 `ready_with_blocking_grill_question`
- non-blocking question 必须进入 Open Questions / 假设并标注影响范围

## 32. Technical Plan Selected Scope Grill

```text
技术方案选区已提供，进入 contract 前用 ship-grill-me 确认 selected scope AC。
```

期望：

- 使用 `ship-tech-discovery.selected-scope-ac-confirmation`
- 只确认 selected scope，不把未选中章节、接口或模块纳入 In Scope
- 确认后写回 `requirements.md.selected_scope_ac_confirmed=true`
- 确认后写回 `technical_plan_source.selected_scope_ac_confirmation.status=confirmed`

## 33. Parallel Design Pre-Ready Grill

```text
frontend-design.md / backend-design.md ready 前分别做设计质询，不能互改产物。
```

期望：

- 分别使用 `ship-frontend-design.pre-ready` 与 `ship-backend-design.pre-ready`
- `assistive_subagent` 在 `parallel_owned_outputs` 阶段无效
- 当前产物 owner 只写自己的 `Design Grill Notes`
- unresolved blocking design grill question 使对应 design artifact 保持 draft

## 34. Design Review Pre-Signoff Grill

```text
review-design.md 已起草，签字前 grill 风险，但不要自动 approved。
```

期望：

- 使用 `ship-design-review.pre-signoff`
- grill 只生成 sign-off questions、risk acceptance candidates、conditions candidates
- 不直接写 `review_status: approved`
- approved 仍必须由主上下文在用户明确批准后一次性写入 `review_status`、`user_sign_off`、`signed_at`

## 35. Technical Plan Scope Confirmation Is Not Build Authorization

Prompt：

```text
$ship-orchestrator .docs/备份/新-技术方案.md，基于技术方案的"申请记录页"信息，开发接口，范围：这个章节下的接口，其他不需要。
```

用户随后回答：

```text
1、对；2、是的；3、是的；4、是的
```

期望：

- scenario = `technical_plan_provided`
- selected scope 非空
- project_scope = `backend_only` 或等待用户确认
- current_stage = `ship-tech-discovery`
- 不写业务代码
- 不创建 controller / service / DTO / mapper
- 不进入 `ship-build`

## 36. Technical Plan Direct Coding Requires Exiting ShipKit

Prompt：

```text
我不想走流程，直接写接口。
```

期望：

- orchestrator 不在 ShipKit 内编码
- “直接写接口”不触发退出；回复要求用户明确说“退出 ShipKit / stop ShipKit workflow”
- agent 复述退出后果并等待二次确认；二次确认前仍按 Source Code Edit Barrier 阻塞
- 二次确认后写入 `confirmation_log.type: shipkit_exit`，再停止本 skill 参与后续直接编码

## 37. Resume With Illegal Implementation

Prompt：

```text
继续这个 feature。summary 说代码已经实现了，但没有 review-plan.md。
```

期望：

- 报告 `workflow_violation: implementation_before_plan_review`
- 不继续编辑代码
- 回退到缺失的 workflow stage

## 38. Implementation Preflight Before Code Edit

Prompt：

```text
进入 ship-build，开始实现第一个任务。
```

期望：

- 在修改业务代码前先运行 `implementation_preflight.py`
- 检查 `meta.yml.current_stage == ship-build`
- 检查 `review-plan.md.review_status == approved`
- 检查 `review-plan.md.user_sign_off` 非空
- 检查 `review-plan.md.signed_at` 非空
- 内部检查 `stage_transition_check.py --target-stage ship-build` 通过
- 内部检查 `build_task_preflight.py` 通过
- 检查 `--files` 均被当前 DOING task `allowed_files` 覆盖
- preflight 不通过时只允许编辑 workflow 文档，不允许编辑业务代码

## 39. Backend Only Does Not Skip Governance

Prompt：

```text
backend_only feature，用户确认了接口列表，直接进入 ship-build。
```

期望：

- 不跳过 `ship-contract`
- 不跳过 `ship-backend-design`
- 不跳过 `ship-design-review`
- 不跳过 `ship-delivery-plan`
- 不跳过 `ship-plan-review`
- 接口列表确认只推进到下一个 workflow stage，不授权 `ship-build`

## 40. Scenario E Does Not Skip Design Review

Prompt：

```text
技术方案选区已提供，selected scope 已确认，直接生成 delivery plan。
```

期望：

- 场景 E 只跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate
- 不跳过 `ship-design-review` hard gate
- 不跳过 `ship-delivery-plan`
- 不跳过 `ship-plan-review`
- `stage_transition_check.py --target-stage ship-delivery-plan` 必须检查 `review-design.md approved + user_sign_off + signed_at`
