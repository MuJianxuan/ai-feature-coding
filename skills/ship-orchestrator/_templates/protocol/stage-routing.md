# Stage Routing Protocol

本协议定义 ship-orchestrator 的 14 个内部执行阶段及其路由规则。

## 阶段视图

### 对外视图（5 个大阶段）

```
[Discover →] Define → Design → Build → Close
```

- `Discover` 是条件性大阶段，只在场景 A/C 出现，或场景 B/D 通过 UIUX Material Gate 插入 `ship-shape` 时出现

### 内部阶段序列（14 个执行阶段）

```
[ship-discover → ship-shape →]
ship-define → ship-define-review [硬门禁]
→ ship-tech-discovery
→ ship-contract → ship-frontend-design → ship-backend-design
→ ship-design-review [硬门禁]
→ ship-delivery-plan
→ ship-plan-review [硬门禁]
→ ship-build → ship-verify → ship-handoff
```

**前 2 个阶段是条件性的**：
- `ship-discover`：只在场景 A/C 出现
- `ship-shape`：默认随 A/C 出现；场景 B/D 默认跳过，但若 UIUX Material Gate 中用户显式授权生成线框，可临时插入

## Macro Stage 映射

| Macro Stage | 包含的 Canonical Stages |
|-------------|------------------------|
| `Discover`（条件性） | `ship-discover`, `ship-shape` |
| `Define` | `ship-define`, `ship-define-review` |
| `Design` | `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `Build` | `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `Close` | `ship-handoff` |

## 各阶段入口/出口条件

| 阶段 | 入口条件 | 出口产物 | 出口条件 |
|------|---------|---------|---------|
| ship-discover | 场景 A/C 确认启动 | product-brief.md | frontmatter stage_status: ready |
| ship-shape | product-brief.md ready + feature 有 UI + 无外部 UIUX；或 UIUX Material Gate 授权插入 | design-brief.md + resource/wireframes/ | stage_status: ready + 3+ 变体验证通过 |
| ship-define | NEW_FEATURE 确认启动（场景 B/D）或 ship-discover/ship-shape 完成；场景 E 跳过 | requirements.md | frontmatter stage_status: ready |
| ship-define-review | requirements.md 存在且 stage_status: ready；场景 E 跳过 | review-define.md | review_status: approved + user_sign_off/signed_at |
| ship-tech-discovery | review-define.md review_status: approved；或场景 E 已提供 technical_plan_source selected scope | tech-research.md + tech-selection.md；场景 E 同时派生 requirements.md index | 两份产物均 `stage_status: ready`；场景 E 还要求 derived `requirements.md.stage_status: ready` |
| ship-contract | tech-selection.md ready | api-contract.md | stage_status: ready |
| ship-frontend-design | api-contract.md ready；不要求 backend-design 已完成 | frontend-design.md | stage_status: ready |
| ship-backend-design | api-contract.md ready；不要求 frontend-design 已完成 | backend-design.md | stage_status: ready |
| ship-design-review | `project_scope` 对应设计文档 ready（fullstack: frontend+backend；backend_only: backend；frontend_only: frontend） | review-design.md | review_status: approved + user_sign_off/signed_at |
| ship-delivery-plan | review-design.md review_status: approved | `project_scope` 对应 plan（fullstack: frontend+backend+sync；backend_only: backend；frontend_only: frontend） | 对应 plan `stage_status: ready`，fullstack 还要求 sync 完成 |
| ship-plan-review | `project_scope` 对应 plan ready | review-plan.md | review_status: approved + user_sign_off/signed_at |
| ship-build | review-plan.md review_status: approved | 代码产物 | 所有 task 完成 |
| ship-verify | `ship-build` 已完成，且对应 scope 的 plan task 全部 DONE | verification.md | `stage_status: ready` |
| ship-handoff | verification.md stage_status: ready | handoff.md + verification.md | `handoff.md` 完成且 `verification.md stage_status: complete` |

## 并行规则

### Frontend / Backend Design 并行

- `ship-frontend-design` 和 `ship-backend-design` 是 **sibling stages**，可并行执行
- fullstack 下任一侧启动只依赖 `api-contract.md ready`
- 另一侧不作为启动前置
- `ship-design-review` 才统一收口两侧设计产物

### Tech Discovery 内部顺序

固定顺序：`research → selection`

### Delivery Plan 内部顺序

固定顺序：`frontend → backend → sync`

### Build 任务顺序

- 正式任务保持单 `DOING`
- 只读准备、验证和证据支线才允许辅助委派

### Verify 并行

- 可按 backend unit / backend integration / backend contract / frontend component / frontend E2E 分轨并行
- 但 `verification.md` 仍由主上下文统一归档

## 硬门禁（Hard Gate）

### 三个硬门禁阶段

1. `ship-define-review`
2. `ship-design-review`
3. `ship-plan-review`

### 硬门禁通过条件

必须同时满足：
- `review_status: approved`
- `user_sign_off` 非空
- `signed_at` 非空

### 硬门禁失败处理

- 硬门禁失败：必须回退，不可跳过，不可强制通过
- `rejected`：回退到对应的产出阶段重新执行
- `revision_needed`：列出必须解决的问题，解决后重新提交评审
- 连续两次门禁失败：建议用户重新审视需求或方案

## 软门禁（Soft Gate）

### 适用阶段

所有非硬门禁的阶段间过渡。

### 软门禁通过条件

- 检查上游文档 frontmatter 中 `stage_status` 字段
- `stage_status: ready` 或 `complete` → 允许推进
- `stage_status: draft` 时先读取 `soft_gate_class` 与 `blocking_gaps`
- `soft_gate_class: soft_optional` 且 `blocking_gaps` 为空 → 可在用户明确确认后强制推进，并写入 `meta.yml.skip_log`
- `soft_gate_class: soft_blocking` 且 `blocking_gaps` 非空 → 不可推进，不可通过 `skip_log` 绕过；只能补材料、缩 scope 或显式转场景
- 若 `meta.yml.stages.<stage>.status` 为 `in_progress/blocked`，但 artifact 已 `ready`，以 artifact frontmatter 为事实源并回写 `meta.yml`
- 上游文档不存在 → 阻断，路由回上游阶段

### 软门禁失败处理

- `soft_optional` 的强制推进必须记录到 `meta.yml.skip_log`
- `soft_blocking` 不可通过 `skip_log` 绕过；必须先关闭 `blocking_gaps`
- hard gate 永远不可通过 `skip_log` 跳过或强制通过

## 场景与路由规则

### 场景 A/C（零到一 / 迭代增强）

**完整路径**（14 阶段）：
```
ship-discover → ship-shape → ship-define → ship-define-review
→ ship-tech-discovery → ship-contract
→ ship-frontend-design / ship-backend-design
→ ship-design-review → ship-delivery-plan
→ ship-plan-review → ship-build → ship-verify → ship-handoff
```

**可能的跳过**：
- `ship-shape` 跳过条件：
  - feature 不涉及 UI
  - 或 `backend_only` scope
  - 或场景 C 且已有 UIUX 基线

### 场景 B/D（产品提供 / PRD 直通）

**默认路径**（跳过 Discover，12 阶段）：
```
ship-define → ship-define-review
→ ship-tech-discovery → ship-contract
→ ship-frontend-design / ship-backend-design
→ ship-design-review → ship-delivery-plan
→ ship-plan-review → ship-build → ship-verify → ship-handoff
```

**可能的插入**：
- UIUX Material Gate 在 `project_scope = fullstack | frontend_only` 且用户授权生成线框时，插入 `ship-shape`：
  ```
  ship-shape → ship-define → ...
  ```
- 若 `project_scope = backend_only`，B/D 的 UIUX Material Gate 不得插入 `ship-shape`，必须保持 `ship-shape` 为 skipped

**B 与 D 的区别**：
- B：`ship-define` 走 `generation_mode: interview`（多轮采访）
- D：`ship-define` 走 `generation_mode: prd_direct`（零提问纯提取）

### 场景 E（技术方案选区入口）

**裁剪路径**（跳过 Discover + Define，10 阶段）：
```
ship-tech-discovery → ship-contract
→ ship-frontend-design / ship-backend-design
→ ship-design-review → ship-delivery-plan
→ ship-plan-review → ship-build → ship-verify → ship-handoff
```

**特殊规则**：
- 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate
- `ship-tech-discovery` 开头派生最小 `requirements.md` index
- 进入 `ship-contract` 前必须完成 `selected_scope_ac_confirmation`
- **仍必须通过 `ship-design-review` 和 `ship-plan-review`**

## 范围与路由裁剪

### backend_only

**跳过阶段**：
- `ship-frontend-design`
- `ship-shape`

**保留阶段**：
- 所有其他阶段，包括：
  - `ship-contract`
  - `ship-backend-design`
  - `ship-design-review`
  - `ship-delivery-plan`
  - `ship-plan-review`

**UIUX Gate 约束**：
- `backend_only` 下不允许 UIUX Material Gate 插入 `ship-shape`，即使场景 B/D 缺少 UIUX 材料，也应按后端契约材料缺口处理

### frontend_only

**跳过阶段**：
- `ship-backend-design`

**保留阶段**：
- 所有其他阶段，包括：
  - `ship-contract`
  - `ship-frontend-design`
  - `ship-design-review`
  - `ship-delivery-plan`
  - `ship-plan-review`

### fullstack

无跳过阶段，完整执行。

## 路由决策流程

```
用户输入 / 阶段完成回调
    ↓
读取 meta.yml.current_stage
    ↓
检查当前阶段 status
    ↓
判断是否满足出口条件
    ↓
    ├→ 不满足 → 路由回当前阶段继续执行
    ↓
    └→ 满足 → 确定下一阶段
                ↓
            检查下一阶段入口条件
                ↓
                ├→ 不满足 → 报告缺失门禁，阻塞推进
                ↓
                └→ 满足 → 检查是否跳过（场景 + scope）
                            ↓
                            ├→ 跳过 → 标记 skipped，继续检查下下阶段
                            ↓
                            └→ 不跳过 → 更新 current_stage，路由到目标阶段 skill
```

## 阶段回调协议

阶段 skill 完成后必须回调 orchestrator：
1. 先读取对应产物 frontmatter，确认事实状态
2. 将 `meta.yml` 中对应阶段状态回写为摘要状态（如 `ready` / `approved` / `completed`）
3. 更新 `current_stage` 为下一阶段 canonical stage id
4. 若当前阶段为双产物阶段，同步刷新对应 `current_part`
5. 同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`
6. 若发现 `meta.yml` 与产物 frontmatter 不一致，优先修正 `meta.yml`
7. 若进入特定阶段，先刷新 `meta.yml.spec_context` 再传递上下文
8. 若命中配置驱动节点或子代理决策节点，先读取 `meta.yml.delegation` 判定执行方式
9. 若当前阶段存在 unresolved blocking `ship-grill-me` question，不得推进下一阶段

## 恢复时的路由判断

CONTINUE_FEATURE 模式下，根据 `current_stage` 和该阶段 `status` 判断恢复点：
- `status: completed` → 检查门禁后推进到下一阶段
- `status: in_progress` → 恢复当前阶段（传递已有产物作为上下文）
- `status: approved / ready` → 检查门禁后推进到下一阶段
- `status: blocked` → 报告阻塞原因，询问用户决策（解除阻塞 / 切换 feature / 终止）
- `status: pending` → 路由到该阶段重新启动
