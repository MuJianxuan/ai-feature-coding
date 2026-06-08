# Scope Detection Protocol

本协议定义 ship-orchestrator 如何判定项目范围（project_scope）。

## 三种范围

| 范围 | 入口信号 | 跳过阶段 |
|------|---------|---------|
| `fullstack`（默认） | 用户描述涉及前后端、或未明确声明 | 无 |
| `backend_only` | 用户明确说"纯后端""只做 API""不涉及前端" | `ship-shape`, `ship-frontend-design` |
| `frontend_only` | 用户明确说"纯前端""只做 UI""不涉及后端" | `ship-backend-design` |

## 判定规则

### 默认策略

- 信号歧义时默认 `fullstack`
- 此时必须显式询问用户是否要落成单侧 scope
- 在用户确认前不得写回单侧 `project_scope`

### 证据要求

用户可在启动确认时声明 scope，也可在 `ship-tech-discovery` 完成后由 orchestrator 基于明确证据确认 scope。

**证据要求**：仅当以下四类证据都指向单侧时，才允许回写 `meta.yml.project_scope` 和 `project_scope_evidence`：
1. `tech_stack`：技术栈信息
2. 现有 surface：现有接口或组件表面
3. consumer/entrypoint：消费者或入口点
4. 项目边界：项目边界定义

若证据不足或存在双侧迹象，默认保持 `fullstack`，并要求用户显式确认；不得仅凭某个 `tech_stack` 字段为空就下结论。

### 范围变更规则

- scope 变更只允许在 `ship-design-review` 之前
- 一旦通过设计评审，scope 冻结，并写入：
  - `scope_freeze.status=frozen`
  - `frozen_scope`
  - `frozen_at`
  - `frozen_by_gate: ship-design-review`
  - `user_sign_off`
- 设计评审通过后如确需变更 scope，必须：
  - reopen `ship-design-review`
  - 说明 `reopen_reason`
  - 重新跑受影响的 contract/design/plan
  - 不得静默修改 `project_scope`

## 范围与阶段映射

### `backend_only`

**跳过阶段**：
- `stages.ship-frontend-design.status = skipped`
- `stages.ship-shape.status = skipped`

**保留阶段**：
- `ship-contract`：默认保留（形态可能是 REST/gRPC/消息/CLI/SDK）
- `ship-backend-design`：必须执行
- `ship-design-review`：必须执行
- `ship-delivery-plan`：必须执行
- `ship-plan-review`：必须执行

### `frontend_only`

**跳过阶段**：
- `stages.ship-backend-design.status = skipped`

**保留阶段**：
- `ship-contract`：默认保留（形态可能不同）
- `ship-frontend-design`：必须执行
- `ship-design-review`：必须执行
- `ship-delivery-plan`：必须执行
- `ship-plan-review`：必须执行

### `fullstack`

**无跳过阶段**，所有阶段按标准流程执行。

## backend_only 不等于跳过治理

`backend_only` 跳过 UI shaping 与 frontend design，但不裁剪上游治理：
- 不跳过 `ship-contract`
- 不跳过 `ship-backend-design`
- 不跳过 `ship-design-review`
- 不跳过 `ship-delivery-plan`
- 不跳过 `ship-plan-review`

用户确认"只做接口"不等于授权跳过设计和计划。

## 范围冻结协议

### 冻结时机

- `ship-design-review` 通过时自动冻结
- 写入 `scope_freeze` 到 `meta.yml`

### 冻结字段

```yaml
scope_freeze:
  status: frozen
  frozen_scope: backend_only  # 冻结时的 project_scope
  frozen_at: "2026-06-08T12:00:00Z"
  frozen_by_gate: ship-design-review
  user_sign_off: "用户确认签字文本"
```

### 冻结校验

- `stage_transition_check.py --target-stage ship-delivery-plan` 会检查 scope_freeze
- 若 `project_scope` 与 `frozen_scope` 不一致，阻塞推进
- `validate_feature_artifacts.py` 报告 `scope_freeze_mismatch`

### 冻结后变更

若确需变更 scope：
1. reopen `ship-design-review`
2. 说明 `reopen_reason`
3. 更新 `frozen_scope`
4. 重新跑受影响的 contract/design/plan
5. 重新通过 `ship-design-review`

不得静默修改 `project_scope`。

## 范围与产物映射

### backend_only

`ship-delivery-plan` 只生成：
- `backend-plan.md`

不生成：
- `frontend-plan.md`

### frontend_only

`ship-delivery-plan` 只生成：
- `frontend-plan.md`

不生成：
- `backend-plan.md`

### fullstack

`ship-delivery-plan` 生成：
- `frontend-plan.md`
- `backend-plan.md`
- `frontend-plan.md` / `backend-plan.md` 内的 sync 子段（若需要前后端同步；不生成独立 `sync-plan.md`）

## 范围验证

### 产物验证

`validate_feature_artifacts.py` 检查：
- `backend_only` 目录里不应出现 `frontend-plan.md` 或 `frontend-design.md`
- `frontend_only` 目录里不应出现 `backend-plan.md` 或 `backend-design.md`
- 报告 `scope_forbidden_artifact`

### 证据验证

若 `project_scope` 为单侧（`backend_only` 或 `frontend_only`）：
- 必须提供 `project_scope_evidence`
- 包含四类证据：tech_stack、surface、consumer、边界

缺少证据时：
- `validate_feature_artifacts.py` 报告 `missing_project_scope_evidence`
- `feature_meta_runtime.py` 拒绝创建单侧 scope

## 启动确认中的范围说明

NEW_FEATURE 启动确认必须标明识别到的范围：
- `fullstack`：无跳过阶段
- `backend_only`：
  - 显式列出："将跳过 `ship-shape` 与 `ship-frontend-design`"
  - 明确：B/D 的 UIUX Material Gate 在 `backend_only` 下不得插入 `ship-shape`
  - 强调：**不跳过 `ship-contract`、`ship-backend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`**
- `frontend_only`：
  - 显式列出："将跳过 `ship-backend-design`"
  - 强调：**不跳过 `ship-contract`、`ship-frontend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`**
