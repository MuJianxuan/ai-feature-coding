---
name: ship-design-review
description: "ShipKit hard gate. Reviews technical design for consistency across API contract, frontend and backend. Produces review-design.md. Use after ship-frontend-design and ship-backend-design complete."
---

# 设计评审 (Design Review)

## Overview

设计评审是硬门禁阶段，负责统一评审 `api-contract.md`、`frontend-design.md`、`backend-design.md` 三份技术方案，确保前后端契约一致性，消除设计阶段的不一致与遗漏。

核心目标：
- 三方交叉验证：API 契约 ↔ 前端设计 ↔ 后端设计
- 发现接口不一致、数据模型偏差、遗漏覆盖等问题
- 产出 `review-design.md`，记录评审结论与修改要求
- 用户明确批准后方可通过门禁

## When to Use

- `project_scope` 对应的设计文档已完成（stage_status: ready）
- `api-contract.md` 已定稿
- 准备进入实施计划阶段前的最后检查点

## When NOT to Use

- 前端或后端设计尚未完成 —— 等待设计阶段完成
- 仅修改了一个接口的小变更 —— 使用轻量 diff review
- 纯 UI 样式调整，不涉及接口变更 —— 无需本阶段
- 需求尚未通过评审 —— 先完成 `ship-define-review`

## Gate Protocol

本阶段为 **硬门禁 (Hard Gate)**，遵循以下规则：

1. **不可跳过**：无论团队多赶时间，设计评审不可省略
2. **必须用户签字**：AI 可以执行评审，但最终通过/拒绝决定权在用户
3. **阻塞后续**：`review_status` 不为 `approved` 时，禁止进入 plan 阶段
4. **修改后重审**：如果状态为 `revision_needed`，修改后必须重新执行评审流程

### 状态流转

```
pending → approved     (用户确认通过)
pending → rejected     (存在 Critical 问题，需重新设计)
pending → revision_needed  (存在 Major 问题，需修改后重审)
revision_needed → pending  (修改完成，重新提交评审)
```

## Delegation Boundary

本阶段的质量门禁检查执行者由 orchestrator 基于 delegation 配置决定：

- `current_context`：主代理直接执行设计评审并写 `review-design.md`
- `gate_check_subagent`：子代理执行设计评审并直接写正式 `review-design.md` 草案

配置解释：

- `node_overrides[ship-design-review]` 优先于 `delegation.default_mode`
- `assistive_subagent` 在本阶段解释为 `gate_check_subagent`
- `parallel_subagent` 在本阶段无效；记录 warning 后回退到 `default_mode`，仍无法解析则回退 `current_context`

约束：

- 若由子代理起草，frontmatter 中的 `review_status` 必须保持 `pending`
- 若由子代理起草，`user_sign_off`、`signed_at` 必须保持为空
- 主代理必须重新读取正式草案、复核检查结果并按需要修订
- 只有主代理可以把 `review_status` 改成 `approved / rejected / revision_needed`
- 子代理不可替用户做 `approved / rejected / revision_needed` 决策

## Scope Adaptation

本阶段根据 `project_scope` 调整评审范围：

| project_scope | 评审文档 | 交叉验证维度 |
|---------------|---------|-------------|
| `fullstack` | api-contract.md + frontend-design.md + backend-design.md | Contract↔Frontend, Contract↔Backend, Frontend↔Backend |
| `backend_only` | api-contract.md + backend-design.md | Contract↔Backend only |
| `frontend_only` | api-contract.md + frontend-design.md | Contract↔Frontend only |

入口条件调整：

- `fullstack`：`frontend-design.md` AND `backend-design.md` 均 `stage_status: ready`
- `backend_only`：`backend-design.md` ready（`ship-frontend-design.status = skipped`）
- `frontend_only`：`frontend-design.md` ready（`ship-backend-design.status = skipped`）

Review Checklist 调整：

- 缺失侧的检查项标记为 `na`（不适用），不计入 pass/fail
- `reviewed_documents` 只列出实际评审的文档
- 交叉验证从三方降为双方时，`Frontend ↔ Backend` 维度标记为 `na`

## Cross-Validation Protocol (三方交叉验证)

### 验证维度

| 验证对 | 检查内容 |
|--------|----------|
| Contract ↔ Frontend | 前端调用的每个接口是否在 contract 中定义；请求/响应字段是否匹配 |
| Contract ↔ Backend | 后端实现的每个接口是否与 contract 签名一致；错误码是否覆盖 |
| Frontend ↔ Backend | 前端期望的数据结构与后端返回是否一致；状态流转是否对齐 |

### 验证步骤

```
Step 1: 提取 api-contract.md 中所有接口清单
        → 生成 Interface Registry (接口注册表)

Step 2: 扫描 frontend-design.md 中的接口调用点
        → 逐一比对 Interface Registry
        → 标记：✓ 匹配 / ✗ 不存在 / ⚠ 字段偏差

Step 3: 扫描 backend-design.md 中的 Service 方法
        → 逐一比对 Interface Registry
        → 标记：✓ 匹配 / ✗ 未实现 / ⚠ 签名偏差

Step 4: 交叉比对前后端数据模型
        → 字段名、类型、可选性、枚举值

Step 5: 汇总不一致项，按严重程度分级
```

### 严重程度定义

| 级别 | 定义 | 示例 |
|------|------|------|
| Critical | 接口不存在或根本性不一致，无法正常通信 | 前端调用 `POST /orders` 但 contract 中不存在 |
| Major | 字段/类型不一致，会导致运行时错误 | 前端期望 `userId: string` 但后端返回 `user_id: number` |
| Minor | 命名风格不一致或文档描述模糊，不影响功能 | 前端用 camelCase 但 contract 示例用 snake_case（有转换层） |

## Review Checklist

评审时必须逐项检查：

```markdown
- [ ] API 契约完整覆盖所有 AC（每条验收标准至少有一个接口支撑）
- [ ] 前端页面-接口映射表与 api-contract.md 一致（无幽灵接口、无遗漏接口）
- [ ] 后端 Service 方法覆盖所有接口（contract 中每个接口都有对应实现方案）
- [ ] 数据模型前后端一致（字段名、类型、可选性、枚举值）
- [ ] 错误码体系完整（每个接口的异常路径都有对应错误码）
- [ ] 非功能需求有对应方案（性能、安全、可用性在设计中有体现）
- [ ] 技术选型与需求匹配（选用的库/框架能支撑需求规模）
- [ ] 无循环依赖或架构反模式（Service 层级清晰，无双向调用）
```

## Process

```
┌─────────────────────────────────────────────────────────┐
│                  设计评审流程                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 读取三份设计文档                                      │
│       │                                                 │
│       ▼                                                 │
│  2. 构建 Interface Registry (接口注册表)                  │
│       │                                                 │
│       ▼                                                 │
│  3. 执行三方交叉验证                                      │
│       │                                                 │
│       ▼                                                 │
│  4. 逐项执行 Review Checklist                            │
│       │                                                 │
│       ▼                                                 │
│  5. 汇总问题，按 Critical/Major/Minor 分级                │
│       │                                                 │
│       ▼                                                 │
│  6. 编写修改建议                                         │
│       │                                                 │
│       ▼                                                 │
│  7. 产出 review-design.md                               │
│       │                                                 │
│       ▼                                                 │
│  8. 提交用户审批                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Consistency Check Rules

### Rule 1: 接口存在性验证

前端设计中引用的每个 API endpoint 必须在 `api-contract.md` 中有完整定义。

```
违规示例：
  frontend-design.md: "调用 GET /api/users/{id}/preferences"
  api-contract.md: 无此接口定义
  → Critical: 幽灵接口，前端调用了不存在的接口
```

### Rule 2: 字段一致性验证

同一接口在三份文档中的字段定义必须完全一致。

```
违规示例：
  api-contract.md: response.data.userName (string)
  backend-design.md: UserDTO.user_name (String)
  frontend-design.md: user.username (string)
  → Major: 字段命名不一致，需明确转换规则或统一命名
```

### Rule 3: 错误码覆盖验证

每个接口的异常路径必须有对应错误码，且前后端对错误码的处理逻辑一致。

```
违规示例：
  api-contract.md: 定义了 ERR_USER_NOT_FOUND (404)
  frontend-design.md: 未处理 404 场景的 UI 状态
  → Major: 前端缺少错误状态处理
```

### Rule 4: 数据流完整性验证

从用户操作到数据持久化的完整链路必须可追踪。

```
验证路径：
  用户操作 → 前端组件 → API 调用 → 后端 Service → 数据层
  每个环节的数据结构变换必须有明确定义
```

### Rule 5: 非功能需求落地验证

requirements.md 中的非功能需求必须在设计方案中有对应实现策略。

```
违规示例：
  requirements.md: "接口响应时间 < 200ms"
  backend-design.md: 无缓存策略、无性能优化方案
  → Major: 非功能需求无落地方案
```

## Output: review-design.md (产物结构)

### Frontmatter

```yaml
---
stage: ship-design-review
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""
reviewed_at: ""
reviewed_documents: ["api-contract.md", "frontend-design.md", "backend-design.md"]
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
---
```

### 核心章节

1. **评审摘要** —— 一段话总结评审结论与整体质量判断
2. **评审 Checklist** —— 逐项标记通过/未通过
3. **一致性检查结果** —— 三方交叉验证的详细结果表
4. **发现的问题** —— 按 Critical / Major / Minor 分级列出
5. **修改建议** —— 针对每个问题给出具体修改方案
6. **用户签字** —— 用户确认评审结论的签字区域

## Anti-Rationalizations

1. **"接口名不一样但意思一样，能跑就行"** —— 命名不一致是 bug 的温床。今天"能跑"，明天换个人维护就是事故。统一命名是零成本的质量保障。
2. **"前后端会在联调时对齐"** —— 联调时发现不一致，修改成本是设计阶段的 5-10 倍。设计评审就是为了避免联调时的返工。
3. **"这个字段后端会自动转换"** —— 隐式转换是最危险的假设。必须在 contract 中显式标注转换规则，否则就是定时炸弹。
4. **"非功能需求后面再优化"** —— 架构层面的性能/安全设计如果不在设计阶段考虑，后期补救的代价是重构级别的。
5. **"设计文档太多了，保持同步太累"** —— 这正是为什么需要评审门禁。三份文档的一致性不靠人记忆，靠流程保障。

## Verification

在标记 `review_status` 之前，必须确认：

```markdown
## 退出检查

- [ ] 已读取并理解 api-contract.md 全部接口定义
- [ ] 已读取并理解 frontend-design.md 全部页面-接口映射
- [ ] 已读取并理解 backend-design.md 全部 Service 设计
- [ ] 三方交叉验证已完成，结果已记录
- [ ] Review Checklist 每项已逐一检查并标注结果
- [ ] 所有发现的问题已按严重程度分级
- [ ] 每个 Critical/Major 问题有具体修改建议
- [ ] review-design.md 已按模板完整输出
- [ ] 已明确告知用户评审结论，等待用户签字确认
- [ ] 等待用户批准时 review_status 保持 pending，正文已记录 recommended_status
- [ ] 若 review_status 为 approved，已一次性写入用户明确批准、user_sign_off 和 signed_at
- [ ] Frontmatter 字段已正确填写
```

### review_status 判定规则

| 条件 | status |
|------|--------|
| 存在 Critical 问题 | `rejected` |
| 存在 Major 问题但无 Critical | `revision_needed` |
| 仅有 Minor 问题或无问题，但尚未获得用户明确批准 | `pending`，正文记录 `recommended_status: approved` |
| 仅有 Minor 问题或无问题 + 用户明确批准 | `approved`，并同时写入 `user_sign_off` 与 `signed_at` |
| 用户明确拒绝 | `rejected` |
