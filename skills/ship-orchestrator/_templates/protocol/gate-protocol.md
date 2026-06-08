# Gate Protocol

本协议定义 ship-orchestrator 的硬门禁（Hard Gate）和软门禁（Soft Gate）规则。

## 硬门禁（Hard Gate）

### 适用阶段

1. `ship-define-review`
2. `ship-design-review`
3. `ship-plan-review`

### 执行规则

#### 1. 生成 review 文档

生成 `review-<stage>.md` 文档，包含以下必填字段：
- `reviewer`：执行评审的角色（AI / 用户 / 两者）
- `checklist`：评审检查项列表，每项标注 pass/fail/na
- `issues`：发现的问题列表，含严重级别和处理建议
- `review_status`：pending / approved / rejected / revision_needed
- `user_sign_off`：用户确认文本
- `signed_at`：用户确认时间戳
- `conditions`：必须解决的条件列表（如有）

#### 2. 通过条件

只有 `review_status=approved` 且 `user_sign_off`、`signed_at` 非空时，才允许推进。

#### 3. 失败处理

- 若 `rejected`：回退到对应的产出阶段重新执行
- 若 `revision_needed`：列出必须解决的问题，解决后重新提交评审

### 门禁文档 frontmatter 规范

每个评审产物必须包含 frontmatter，字段约定：
- `stage`：所属阶段标识
- `gate_type`：固定为 `hard`
- `review_status`：`pending / approved / rejected / revision_needed`
- `reviewer`：评审者标识
- `reviewed_at`：评审时间
- `reviewed_documents`：本轮评审涉及文档
- `revision_count`：重审次数
- `user_sign_off`：用户签字文本
- `signed_at`：签字时间戳（ISO 8601）
- `conditions`：若 `revision_needed`，列出待解决条件

调度器读取 frontmatter 后才判定门禁结果，正文内容仅作参考不影响判定。

### 硬门禁不可跳过

- 硬门禁失败：必须回退，不可跳过，不可强制通过
- hard gate 永远不可通过 `skip_log` 跳过或强制通过
- 必须产生正式 review 文档并满足 `approved + user_sign_off + signed_at`
- 连续两次门禁失败：建议用户重新审视需求或方案

## 软门禁（Soft Gate）

### 适用阶段

所有非硬门禁的阶段间过渡。

### 执行规则

#### 1. 检查上游文档 frontmatter

检查上游文档 frontmatter 中 `stage_status` 字段。

#### 2. 通过条件

- `stage_status: ready` 或 `complete` → 允许推进
- `stage_status: draft` 时先读取 `soft_gate_class` 与 `blocking_gaps`
- `soft_gate_class: soft_optional` 且 `blocking_gaps` 为空 → 可在用户明确确认后强制推进，并写入 `meta.yml.skip_log`
- `soft_gate_class: soft_blocking` 且 `blocking_gaps` 非空 → 不可推进，不可通过 `skip_log` 绕过；只能补材料、缩 scope 或显式转场景
- 若 `meta.yml.stages.<stage>.status` 为 `in_progress/blocked`，但 artifact 已 `ready`，以 artifact frontmatter 为事实源并回写 `meta.yml`
- 上游文档不存在 → 阻断，路由回上游阶段

#### 3. 失败处理

- `soft_optional` 失败：警告用户风险后，可由用户明确确认强制推进（记录到 `meta.yml.skip_log`）
- `soft_blocking` 失败：不可强制推进；必须先解决 `blocking_gaps`
- 评审产物缺失：阻断推进，路由回评审阶段重新生成

## 门禁失败处理总结

| 门禁类型 | 失败处理 | 是否可跳过 | 是否可强制通过 |
|---------|---------|-----------|--------------|
| 硬门禁 | 必须回退 | 否 | 否 |
| 软门禁 `soft_optional` | 警告风险后用户可选择强制推进 | 仅 `soft_optional` 可记录 skip_log | 是（记录 skip_log） |
| 软门禁 `soft_blocking` | 补材料、缩 scope 或显式转场景 | 否 | 否 |

## 三个硬门禁的具体规则

### ship-define-review

#### 入口条件

- `requirements.md` 存在且 `stage_status: ready`
- 场景 E（技术方案选区入口）跳过此门禁

#### 检查项

1. Requirements 质量检查
2. AC 完整性检查（Domain ID、可验证性）
3. Open Questions 和 Assumptions 风险评估
4. Scope 边界清晰度
5. 待确认问题是否有阻塞项
6. D + backend_only：Phase 1 P1-6 判定契约级材料是否缺失

#### 出口条件

- `review_status: approved`
- `user_sign_off` 非空
- `signed_at` 非空

#### 特殊规则

**D + backend_only 材料类型确认**：
- 若 `project_scope = backend_only` 且 `scenario = prd_direct`
- PRD 应包含契约级材料：OpenAPI / endpoint list / 接口文档 / API spec / message protocol / 消息协议 / CLI spec / SDK / request-response 等
- 若只有产品文档无技术规约，Phase 1 P1-6 判定 Critical
- `validate_feature_artifacts.py` 报告 `backend_contract_material_missing`
- 不允许 `review_status=approved`
- 默认建议降级为 B（interview 模式）补足契约信息

### ship-design-review

#### 入口条件

`project_scope` 对应设计文档 ready：
- fullstack: `frontend-design.md` + `backend-design.md` 均 ready
- backend_only: `backend-design.md` ready
- frontend_only: `frontend-design.md` ready

#### 检查项

1. 设计完整性检查
2. 前后端设计一致性（fullstack）
3. Contract 实现覆盖度
4. 技术选型合理性
5. Open Questions 和 Risk 影响评估
6. Scope freeze 准备

#### 出口条件

- `review_status: approved`
- `user_sign_off` 非空
- `signed_at` 非空

#### 特殊规则

**Scope Freeze**：
- `ship-design-review` 通过时自动冻结 scope
- 写入 `scope_freeze` 到 `meta.yml`：
  ```yaml
  scope_freeze:
    status: frozen
    frozen_scope: backend_only
    frozen_at: "2026-06-08T12:00:00Z"
    frozen_by_gate: ship-design-review
    user_sign_off: "用户确认签字文本"
  ```
- 冻结后若需变更 scope，必须 reopen `ship-design-review`

### ship-plan-review

#### 入口条件

`project_scope` 对应 plan ready：
- fullstack: `frontend-plan.md` + `backend-plan.md` + `sync-plan.md`（可选） 均 ready
- backend_only: `backend-plan.md` ready
- frontend_only: `frontend-plan.md` ready

#### 检查项

1. Plan 完整性检查
2. Task DAG 无环检查
3. AC 覆盖度检查
4. Task brief 完整性（任务目标、上下文、约束、验收、输出）
5. Allowed files 明确性
6. Verification command 可执行性
7. Evidence 要求清晰度
8. Scope freeze 一致性

#### 出口条件

- `review_status: approved`
- `user_sign_off` 非空
- `signed_at` 非空

#### 特殊规则

**Build 授权**：
- 只有 `ship-plan-review` 通过后，才允许进入 `ship-build`
- 通过条件必须同时满足：
  - `review_status: approved`
  - `user_sign_off` 非空
  - `signed_at` 非空
  - `stage_transition_check.py --target-stage ship-build` 通过
  - `build_task_preflight.py` 通过

## 门禁验证脚本

### stage_transition_check.py

检查是否允许推进到目标阶段：
```bash
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-build --json
```

检查项：
- 上游阶段产物存在且 ready
- 硬门禁通过（review_status: approved + user_sign_off + signed_at）
- Scope freeze 一致性（若目标阶段需要）

### build_task_preflight.py

检查 ship-build 前置条件：
```bash
python3 skills/ship-orchestrator/scripts/build_task_preflight.py <feature_dir> --project-scope backend_only --json
```

检查项：
- Plan 文件存在
- 恰好一个 DOING task
- DOING task 有 allowed_files
- DOING task 有 AC refs
- DOING task 有 verification command
- DOING task 有完整 task brief（任务目标、上下文、约束、验收、输出）

### implementation_preflight.py

统一 build 前置检查（包装上述两个脚本）：
```bash
python3 skills/ship-orchestrator/scripts/implementation_preflight.py <feature_dir> --project-scope backend_only --json
```

检查项：
- `meta.yml` 存在且 current_stage 合法
- `stage_transition_check.py --target-stage ship-build` 允许
- `review-plan.md` 为 `review_status: approved`
- `review-plan.md.user_sign_off` 非空
- `review-plan.md.signed_at` 非空
- `build_task_preflight.py` 通过
- exactly one `DOING` task

输出示例：
```json
{
  "allowed": false,
  "current_stage": "ship-tech-discovery",
  "required_stage": "ship-build",
  "issues": [
    {
      "code": "implementation_before_plan_review",
      "message": "ship-build requires approved review-plan.md with user sign-off"
    }
  ]
}
```

## 场景 E 的门禁裁剪

### 跳过的门禁

场景 E（技术方案选区入口）跳过：
- `ship-define-review` hard gate

### 保留的门禁

场景 E 仍必须通过：
- `ship-design-review` hard gate
- `ship-plan-review` hard gate

### 特殊检查

场景 E 在进入 `ship-contract` 前必须完成：
- `selected_scope_ac_confirmation`
- derived `requirements.md.stage_status: ready`
- `technical_plan_source.selected_scope_ac_confirmation.status=confirmed`
