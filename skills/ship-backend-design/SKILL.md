---
name: ship-backend-design
description: "ShipKit stage. Designs backend architecture with domain modeling and data layer. Use after ship-contract completes."
---

# 后端技术方案 (Backend Design)

## Overview

后端技术方案阶段基于 requirements.md 的业务域、tech-research.md 的项目事实发现和 api-contract.md 的接口规约，设计后端的整体架构、领域模型、数据层、服务层、运行时边界和交付风险。

核心目标：
- 建立"业务域-服务边界-数据模型"三层设计，保证架构清晰可演进
- 每个接口都能追溯到具体的 Controller/Service/Repository 实现路径
- 数据模型完整支撑接口规约，并结合已有 DB / ORM / migration 发现考虑复用、扩展、事务、一致性与扩展性
- Service / Repository / MQ / Redis / Cron 等方案必须引用相关 backend spec 或显式记录无匹配规范
- 横切关注点（认证、日志、限流、缓存）有统一方案
- 产物同时满足工程实现、技术评审、部署上线和后续 delivery plan 消费

产出物：`backend-design.md`

## When to Use

- api-contract.md 已完成且 stage_status 为 ready
- requirements.md 中的业务域已明确并分配 Domain ID
- 需要设计后端服务的领域模型与数据层
- 涉及数据库表结构、服务边界、事务策略等架构决策

## When NOT to Use

- api-contract.md 尚未完成 —— 接口规约未定无法做映射
- 纯前端项目（无后端） —— 跳过本阶段
- 仅是已有逻辑的重构（无新功能） —— 直接进入实现阶段
- 接入第三方服务为主，无自研后端 —— 简化为集成方案文档

## Domain-Driven Design Approach

后端设计遵循 DDD 思想，但不教条：

```
Bounded Context → 业务域（与 requirements.md 的 Domain ID 对齐）
       │
       ├── Aggregate Root → 聚合根（数据一致性边界）
       ├── Entity / Value Object → 实体与值对象
       ├── Domain Service → 跨实体的业务逻辑
       └── Repository → 数据访问抽象
```

核心原则：
1. **Domain 与代码模块一一对应**：requirements.md 的 D-AUTH-001 → 代码中的 `auth/` 模块
2. **服务边界由聚合定义**：聚合内强一致，跨聚合最终一致
3. **依赖方向单向**：Controller → Service → Repository → DB，不允许反向调用
4. **业务逻辑不下沉到 Controller**：Controller 只做参数校验、调用 Service、返回响应

## Diagram Guidance

复杂后端建议使用 PlantUML source 写入 Markdown 辅助评审，不要求渲染图片入库；简单项目不强制画图，可合并章节或写明“不适用 + 原因”。ER 图不是唯一图示类型，图示必须服务于架构、事务、一致性或运行时边界决策。

推荐图类型：
- system boundary diagram：表达业务入口、核心服务、基础设施和外部系统边界
- component diagram：表达 Runtime Component、模块边界、外部依赖、message / worker 承接关系
- sequence diagram：表达接口调用、服务交互、事务步骤、重试和补偿
- ER style class diagram：表达数据模型、状态字段和表关系
- deployment diagram：表达部署拓扑、队列、存储和第三方系统边界

推荐触发条件：
- 多服务、多模块或第三方依赖协作
- `api-contract.md` 包含 message、cron、cli、sdk 等非 HTTP contract，需要 producer / consumer / job / command handler 承接
- 存在复杂事务、一致性补偿、outbox、DLQ、幂等重试
- 存在权限、租户隔离、PII、审计不可变或部署拓扑风险

每张图下方必须补充：范围、参与方、关键路径、至少一个关键异常路径、未覆盖范围、一致性检查。图中的 Service、Repository、Event、external dependency、storage 名称必须与 Domain Map、Contract-to-Implementation Map 和正文表格一致。

## Process

当 `meta.yml.scenario: technical_plan_provided` 时，backend design 必须按 `technical_plan_source.selected_scope` 裁剪：只覆盖 selected scope 相关服务、数据模型、DB / ORM / migration、worker、MQ、cron、权限、错误处理和验证路径。未选中技术方案内容不得进入本期设计，除非作为依赖风险或 open question 记录。

```
1. 读取 requirements.md、tech-research.md、api-contract.md
   verify: 已理解 Project Reality Scan、Existing Surface Inventory、Requirement-to-Reality Mapping 和接口契约
2. 整理项目背景、范围、目标、非目标、依赖与风险
   verify: 背景、边界、假设、Open Questions 已显式记录
3. 选择架构模式与分层策略
   verify: 选择有 tech-selection.md 依据，并说明方案取舍
4. 业务域 → 模块映射
   verify: 与 requirements.md 的 Domain ID 一一对应
5. 加载 ship-spec 约束
   verify: 已记录匹配的 `spec_id` 或“无匹配规范”
6. 设计系统边界、运行时组件和关键流程图
   verify: Runtime Overview / 关键流程图有 PlantUML 或不适用原因
7. 设计 Existing Backend Surface Plan
   verify: DB / ORM / migration / Service / Repository / MQ / Redis / Cron 已标注 reuse / extend / new / avoid / unknown
8. 设计数据模型与状态/关系图
   verify: 支撑 api-contract.md 所有数据结构和 state enum，且结合已有 DB / ORM / migration 事实
9. 设计服务层（Service + 方法签名）
   verify: 每个 Domain 至少一个 Service
10. 接口实现映射（Controller → Service → Repository）
   verify: api-contract.md 每个接口都有映射
11. 设计服务交互、MQ / worker / cron、事件流与事务一致性
   verify: Runtime Component、Domain Event、Transaction / Consistency 有落点
12. 设计中间件、Security Design 与横切关注点
   verify: AuthN/AuthZ/Tenant/PII/Audit/Abuse 与错误处理覆盖
13. 制定数据库迁移、部署、rollout / rollback 策略
   verify: 含初始化脚本、升级脚本规范、上线和回滚结论
14. 制定后端非功能方案与 ready checklist
   verify: 缓存/限流/监控/observability/capacity/alerting/dependencies/Q&A 各有结论
14.5 Pre-Ready Design Grill
   verify: 若启用 `ship-grill-me`，service boundary、数据模型、事务一致性、权限审计和 migration / rollback risk 已逐题确认；blocking question 已 resolved
```

## Delegation Boundary

本阶段是少数允许**拥有正式产物**的并行阶段之一。

- 当 `api-contract.md.stage_status = ready` 且 Domain ID 已稳定时，可由子代理独立拥有并产出 `backend-design.md`
- 允许与 `ship-frontend-design` 并行执行，但两者只能共享 `api-contract.md`、`requirements.md` 和 `spec_context`，不可互改对方正式产物
- `parallel_subagent` 仅作用于当前节点；允许只启动后端设计，不要求与前端成对启动
- `assistive_subagent` 在本阶段无效；若 `ask_on_parallel_stage = false` 且没有显式 `node_overrides[ship-backend-design] = parallel_subagent`，则回退 `current_context`
- 子代理仍不得推进 `ship-design-review`，正式阶段切换由 orchestrator 统一收口
- 本阶段只消费 workspace `spec_root` 下的规范，不从 `meta.yml.projects` 预设前后端角色；项目是否包含 API / service / job / persistence 必须基于 Project Reality First 证据判断

### 步骤详解

**Step 1: 背景、范围与风险整理**

先读取 `tech-research.md` 的 Project Reality Scan / Existing Surface Inventory / Evidence and Uncertainty，写清项目背景、现状痛点、本期目标、非目标、关键假设、跨团队 / 外部系统依赖、上线风险和 Open Questions。小项目可以合并章节，但不能省略设计边界。

**Step 2: 架构模式选择**

常见选项：
- **分层架构**（Controller / Service / Repository）：适合大多数 CRUD 场景
- **六边形架构**（Hexagonal）：适合复杂业务、需要多种适配器
- **CQRS**：适合读写分离、高并发查询场景
- **微服务**：适合大型团队、独立部署需求

**Step 3: 业务域映射**

```
requirements.md         backend
D-AUTH-001 用户认证 →   src/modules/auth/
D-AUTH-002 权限管理 →   src/modules/auth/permissions/
D-ORD-001  订单创建  →   src/modules/order/
D-PAY-001  支付处理  →   src/modules/payment/
```

**Step 4: 加载 ship-spec 约束**

- 先读 `.docs/spec/INDEX.md`，优先从 `backend / shared` 分类选择候选 spec
- 基于 `tech-selection.md` 的技术栈标签、`requirements.md` 的 Domain ID 和涉及文件匹配规范
- 规范匹配边界固定为 workspace `spec_root`
- 将命中的 `spec_id` 记录到 `backend-design.md.referenced_spec_ids`
- 无匹配规范时显式写“无匹配规范”，并把 warning 写入 `spec_warnings`
- 若 INDEX 与 frontmatter 不一致，记录 warning，默认 Warn Then Continue

**Step 5: 系统边界与运行时概览**

- 明确业务入口、核心服务、基础设施、外部系统和部署边界
- 用 PlantUML 表达 Runtime Component、关键接口 Sequence、message / worker / cron 承接关系
- 简单项目可写“不画图 + 原因”，但仍需说明边界与关键路径

**Step 6: 数据模型设计**

- 先读取 `tech-research.md` 中已有 DB / ORM / migration 发现，再从 api-contract.md 的数据模型推导新增或扩展字段
- 标注主键、外键、唯一索引、复合索引
- 考虑软删除、审计字段（created_at / updated_at / created_by）
- 标注字段的业务含义与约束

**Step 7-8: 服务层与接口映射**

每个接口必须能追溯到：
```
POST /api/v1/todos
  → TodoController.create()
    → TodoService.createTodo(dto)
      → TodoRepository.save(entity)
```

**Step 9-12: 运行时、事件、部署与横切关注点**

认证、授权、日志、错误处理、缓存、限流、监控均需统一方案。复杂项目还需明确 Runtime Component、服务交互、MQ / worker / cron、Domain Event / Message、事务边界、一致性补偿、Security Design、Data Lifecycle、Read / Write Path、部署拓扑、rollout / rollback、依赖项、风险和 Q&A。

## Service Layer Design Rules

### 服务方法签名规范

```typescript
// 命名：动词 + 名词
class TodoService {
  // 查询：find / get / list / search
  async findById(id: string): Promise<Todo | null>
  async listByUser(userId: string, query: ListTodosQuery): Promise<PaginatedResult<Todo>>

  // 命令：create / update / delete / 业务动词
  async createTodo(dto: CreateTodoDto): Promise<Todo>
  async updateTodo(id: string, dto: UpdateTodoDto): Promise<Todo>
  async completeTodo(id: string): Promise<Todo>
  async deleteTodo(id: string): Promise<void>
}
```

### 服务边界原则

| 场景 | 处理方式 |
|------|----------|
| 同一聚合内的操作 | 同一 Service 方法内事务保证一致性 |
| 跨聚合但同一服务 | 编排型 Service 调用多个领域 Service |
| 跨服务（同进程） | 通过领域事件解耦 |
| 跨服务（跨进程） | 异步消息 + 最终一致性 |

### 异常处理约定

```typescript
// 业务异常 → 抛出携带错误码的异常
throw new BusinessError('TODO_NOT_FOUND', 40401, 'Todo 不存在')

// 校验异常 → 抛出字段级详情
throw new ValidationError({ title: '不能为空' })

// 系统异常 → 让全局错误处理器捕获
// 不要在 Service 中 catch 后吞掉异常
```

## Data Model Design Rules

### 表结构规范

```sql
-- 命名：snake_case，复数表名
CREATE TABLE todos (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id),
  title        VARCHAR(200) NOT NULL,
  description  TEXT,
  status       VARCHAR(20) NOT NULL DEFAULT 'pending',
  due_date     TIMESTAMPTZ,

  -- 审计字段（每张表必备）
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at   TIMESTAMPTZ,

  -- 索引
  CONSTRAINT todos_status_check CHECK (status IN ('pending', 'in_progress', 'done'))
);

CREATE INDEX idx_todos_user_id ON todos(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_todos_status ON todos(status) WHERE deleted_at IS NULL;
```

### 索引设计原则

- 外键字段必须有索引
- 频繁过滤的字段加索引（结合 api-contract.md 的过滤参数）
- 软删除场景使用 partial index（`WHERE deleted_at IS NULL`）
- 避免索引过多（写入性能下降）

### 字段命名一致性

- API 字段：camelCase（`userId`）
- 数据库字段：snake_case（`user_id`）
- ORM 层负责映射，禁止在 SQL 中混用

## Output: backend-design.md

编写前先读取 [`references/backend-design-template.md`](./references/backend-design-template.md)。

使用规则：
- 模板是写作引导，不是 rigid schema；章节顺序可调整，不适用章节可裁剪
- 模板中的“必答问题”必须被显式回答；若当前项目不适用，需写明原因
- `backend-design.md` 仍以本文件定义的 frontmatter、stage_status 和 verification 要求为准

### Frontmatter

```yaml
---
stage: ship-backend-design
stage_status: draft  # draft / ready
updated_at: ""
evidence_complete: false
spec_checked_at: ""
referenced_spec_ids: []
spec_warnings: []
---
```

### 推荐覆盖点

以下内容是推荐覆盖点，不要求固定章节顺序；可按项目复杂度合并或拆分，但需确保模板中的必答问题有对应答案。

#### 0. Document Metadata / 文档元信息
- 功能名称、平台 / 系统名称
- 前言、修订历史、词汇表
- 关联文档：requirements.md、tech-selection.md、api-contract.md、spec

#### 1. Background / Scope / Goals
- 项目背景、现状痛点、本期目标
- 覆盖范围
- 非目标 / 不覆盖范围
- 关键假设与约束

#### 2. Summary / Architecture Decisions
- 架构模式（分层 / 六边形 / CQRS）及选择依据
- 技术栈（语言 / 框架 / ORM / 数据库）来自 tech-selection.md
- 分层策略与依赖方向
- 方案对比与最终取舍
- 明确不做的内容
- 目录结构

```
src/
├── modules/
│   ├── auth/
│   │   ├── auth.controller.ts
│   │   ├── auth.service.ts
│   │   ├── auth.repository.ts
│   │   └── auth.entity.ts
│   ├── todo/
│   └── order/
├── common/
│   ├── middlewares/
│   ├── decorators/
│   └── filters/
└── config/
```

#### 2.1 System Boundary / Runtime Overview
- 业务入口
- 核心服务
- 基础设施
- 外部系统
- Runtime Component Diagram / 关键流程 Sequence Diagram

#### 3. Domain-to-Module Map

```markdown
| Domain ID | Domain 名称 | 代码模块 | 聚合 / 核心对象 | 核心 Service | Repository / Gateway |
|-----------|-------------|----------|------------------|--------------|----------------------|
| D-AUTH-001 | 用户认证 | modules/auth | UserCredential | AuthService | AuthRepository |
| D-AUTH-002 | 权限管理 | modules/auth/permissions | Permission | PermissionService | PermissionRepository |
| D-TODO-001 | 待办管理 | modules/todo | Todo | TodoService | TodoRepository |
```

#### 3.1 Referenced Specs / Constraints
- 引用的 `spec_id` 列表
- 对当前后端方案生效的关键约束
- 若无匹配规范，显式记录原因和 warnings

#### 3.2 Existing Backend Surface Plan

来自 `tech-research.md` 的现有后端 surface 必须逐项处理，数据模型设计不能只从 `api-contract.md` 反推：

```markdown
| Surface | Existing Item | Path / Source | Relation | Plan | Risk / Open Question |
|---|---|---|---|---|---|
| DB | users | prisma/schema.prisma | extend | 复用主键和 email，新增 profile relation | avatar 字段归属待确认 |
| Service | UserService | src/modules/user/user.service.ts | extend | 新增 updateProfile 方法 | 需保持权限检查 |
| MQ | user.updated | src/events/user.ts | unknown | 暂不发布，等待用户确认 | 下游订阅者未知 |
```

Relation 建议使用：`reuse`、`extend`、`replace`、`new`、`avoid`、`unknown`。

#### 4. Data Model / Storage Design
- ER 图（表 + 关系）
- 每张表的 DDL（含字段类型、约束、索引）
- 索引策略说明
- 软删除/审计字段约定
- 数据迁移与初始数据
- 状态字段与 `api-contract.md` state enum / State Contract 的映射

#### 4.1 Data Model / ER Diagrams

复杂项目建议补充 PlantUML component / sequence / ER style class / deployment diagram，并在图下说明范围、参与方、关键路径、异常路径、未覆盖范围、一致性检查。

#### 5. Service Design

每个 Domain 列出：

```markdown
### TodoService (D-TODO-001)

**职责**：待办管理的核心业务逻辑

**方法签名**：
- `createTodo(userId, dto): Promise<Todo>` —— 创建待办
- `findById(id): Promise<Todo | null>` —— 查询单条
- `listByUser(userId, query): Promise<PaginatedResult<Todo>>` —— 分页列表
- `completeTodo(id): Promise<Todo>` —— 标记完成
- `deleteTodo(id): Promise<void>` —— 删除

**依赖**：TodoRepository, UserService（验证用户存在）

**事务边界**：每个公开方法为一个事务
```

#### 6. Contract-to-Implementation Map

api-contract.md 中每个接口的实现路径：

```markdown
| Contract | Handler / Controller / Consumer / Job / Command | Service 方法 | Repository / Gateway | Storage / External dependency | 副作用 |
|----------|--------------------------------------------------|--------------|----------------------|-------------------------------|--------|
| POST /api/v1/todos | TodoController.create | TodoService.createTodo | TodoRepository.save | todos | INSERT todos |
| GET /api/v1/todos | TodoController.list | TodoService.listByUser | TodoRepository.findByUserId | todos | SELECT todos |
| DELETE /api/v1/todos/:id | TodoController.delete | TodoService.deleteTodo | TodoRepository.softDelete | todos | UPDATE todos SET deleted_at |
```

#### 6.1 Cross-Document Traceability Matrix

```markdown
| Domain ID | AC ID | Contract | Handler | Service | Repository / Gateway | Storage / External | Test Focus |
|---|---|---|---|---|---|---|---|
```

#### 6.2 Test Focus / Verification Scenario

Test Focus 应能直接输入后续 delivery plan 和 verification 阶段，按 service method、transaction、event consumer、external dependency 写清场景与预期结果。

```markdown
| Domain ID | AC ID | Design Surface | Scenario | Expected Result | Evidence |
|---|---|---|---|---|---|
```

#### 7. Transaction / Consistency / Idempotency

```markdown
| 操作 | 涉及聚合 | 事务边界 | 一致性要求 | 失败补偿 | 幂等策略 |
|---|---|---|---|---|---|
```

#### 8. MQ / Domain Event / Worker / Cron

承接 `api-contract.md` 中的 message、cron、cli、sdk contract，明确 producer / consumer / job / command handler。

```markdown
| Topic / Queue / Event / Job | Producer | Consumer / Worker / Job | Payload schema | 触发事务点 | Outbox | Retry | DLQ | 幂等 key |
|---|---|---|---|---|---|---|---|---|
```

无 MQ、worker、cron 或异步事件时，写明“不涉及 MQ / 异步事件 + 原因”。

#### 9. Service Interaction / External Integration

```markdown
| 调用方 | 被调用方 | 调用方式 | 超时 | 重试 | fallback / 降级 | error mapping |
|---|---|---|---|---|---|---|
```

#### 10. Cross-Cutting Concerns / Security Design

- **认证中间件**：解析 JWT、注入 user 上下文
- **授权中间件**：基于角色 / 权限的访问控制
- **请求日志**：记录请求/响应、脱敏 PII
- **错误处理**：统一异常 → API 错误响应
- **限流**：按 IP / 用户 / 接口的限流策略

复杂项目单独覆盖 AuthN、AuthZ、Tenant isolation、Sensitive data、Audit、Abuse prevention、Dependency security；不要只写“由中间件处理”。

#### 11. Read / Write Path Design

适用于 CQRS、搜索、Redis 缓存、报表宽表、高并发列表查询。

```markdown
| 场景 | 写模型 | 读模型 | 缓存 | 索引 | 一致性延迟 |
|---|---|---|---|---|---|
```

#### 12. Deployment / Operations / Reliability
- 迁移工具（Prisma Migrate / TypeORM / Flyway）
- 迁移命名规范（`YYYYMMDDHHmmss_description.sql`）
- 回滚策略（每个迁移配套 down 脚本）
- 生产环境迁移流程（备份 → 演练 → 灰度）
- 部署拓扑与运行时边界
- rollout 顺序和灰度策略
- rollback 触发条件和回滚步骤
- migration 执行流程与失败恢复
- 无部署变更时写明“沿用现有部署拓扑 + 原因”
- **缓存**：Redis 使用场景、key 命名规范、过期策略
- **限流**：算法（令牌桶 / 漏桶）、维度、配置
- **监控**：指标（QPS / 延迟 / 错误率）、告警阈值
- **日志**：结构化日志格式、级别、采样策略
- **可观测性**：trace ID 透传、链路追踪
- **安全**：SQL 注入防护、XSS、CSRF、依赖漏洞扫描

#### 12.1 Data Lifecycle / Retention

```markdown
| 数据对象 | 敏感级别 | 保留周期 | 删除策略 | 脱敏/加密 | 审计要求 |
|---|---|---|---|---|---|
```

#### 13. Observability / Capacity / Alerting

- 核心指标：QPS、latency、error rate、queue lag、job duration、DLQ count
- 告警阈值：按业务风险给初始阈值，或说明无法确定
- 容量假设：数据量、并发量、热点查询、缓存命中预期

#### 14. Risk / Dependencies / Q&A / Ready Checklist
- 风险评估
- 跨团队 / 外部系统依赖
- Open Questions
- Q&A
- 接口映射、数据模型、事务一致性、安全、部署迁移、observability 的 ready checklist

#### 14.5 Design Grill Notes（可选）

`ship-grill-me` 可作为 `ship-backend-design.pre-ready` 辅助质询 hook 使用。触发点是 `backend-design.md` 基本成稿、准备 `stage_status: ready` 前。

质询重点：

- Service boundary 是否和 Domain ID 对齐。
- 数据模型是否支撑 contract 字段。
- 事务、一致性、幂等、重试、补偿是否明确。
- 权限、审计、日志、metrics 是否落到具体实现点。
- migration / rollback / deployment risk 是否明确。

parallel ownership 约束：

- 本阶段是 `parallel_owned_outputs`，`assistive_subagent` 在本阶段无效。
- grill 由当前拥有 `backend-design.md` 的上下文执行；若本阶段由 `parallel_subagent` 产出，该子代理只在自己产物 ready 前执行内部 grill。
- 不允许另一个 grill 子代理同时修改 `backend-design.md`，也不得修改 `frontend-design.md`。

建议记录：

| ID | Risk / Question | Evidence | Decision | Follow-up |
|---|---|---|---|---|

- blocking design grill question 未 resolved 时保持 draft。
- non-blocking question 必须进入 Open Questions 或 Risk section，并写明影响范围。

### stage_status 流转规则

- `draft`：业务域映射、数据模型或接口映射不完整
- `ready`：所有 Domain 有对应模块，所有接口有实现路径，blocking design grill question 已 resolved，可进入设计评审

### evidence_complete 判定标准

- 每个 Domain ID 有对应的代码模块和 Service
- 已记录 `referenced_spec_ids` 或“无匹配规范”
- 已消费 `tech-research.md` 的 Project Reality Scan / Existing Surface Inventory，并处理已有 DB / ORM / migration / Service / MQ / Redis / Cron 事实
- 每个接口在接口实现映射中有完整链路
- 数据模型支撑 api-contract.md 所有数据结构
- 中间件方案覆盖认证、授权、错误处理
- 数据库迁移策略明确

## Anti-Rationalizations

1. **"业务逻辑写在 Controller 里更简单"** —— Controller 写业务逻辑等于代码无法复用、无法测试、无法迁移到其他入口（CLI / 队列消费者）。Service 层是必需的。
2. **"事务用 @Transactional 注解就行，不用思考边界"** —— 注解只是工具，事务边界是业务决策。跨聚合的强一致是反模式，会导致死锁和性能问题。
3. **"先不加索引，等慢了再加"** —— 加索引容易，发现慢查询难。基础索引（外键 + 高频过滤字段）必须一开始就有。
4. **"日志先随便打，上线再优化"** —— 上线后排查问题没有合适的日志等于盲调。结构化日志和关键节点日志必须设计在前。
5. **"权限以后再加，先把功能做出来"** —— 后期补权限会渗透到每个 Service，重构成本极高。中间件 + 装饰器在一开始就要落地。

## Red Flags

- **Domain ID 与代码模块对应不上** → 业务域映射失败，后期难维护
- **接口找不到对应的 Service 方法** → 实现路径不清晰
- **数据模型缺少审计字段** → 排查问题、合规审计困难
- **Service 方法直接接收 HTTP 请求对象** → 分层不清晰，无法跨入口复用
- **跨聚合强一致事务** → 性能与死锁隐患
- **没有数据库迁移工具** → 团队协作和生产部署混乱
- **错误处理散落在各 Service** → 缺少统一的异常 → API 错误响应映射

## Verification

完成 backend-design.md 后，执行以下检查：

```
□ 业务域是否与 requirements.md 的 Domain ID 一一对应？
□ 每个 Domain 是否有对应的代码模块和 Service？
□ 是否已读取 tech-research.md 的 Project Reality Scan 和 Existing Surface Inventory？
□ 数据模型是否结合已有 DB / ORM / migration 发现，而不是只从 api-contract.md 反推？
□ Service / Repository / MQ / Redis / Cron 等方案是否引用 backend/shared spec 或记录无匹配规范？
□ 项目背景、范围、目标、非目标和关键假设是否明确？
□ 依赖项、风险、Q&A / Open Questions 是否有结论？
□ 是否已完成 ship-spec 匹配并记录 `referenced_spec_ids` / `spec_warnings`？
□ api-contract.md 中每个接口是否有完整的实现映射？
□ 数据模型是否支撑接口规约的所有数据结构？
□ 数据库表是否包含审计字段（created_at / updated_at）？
□ 索引设计是否覆盖外键和高频过滤字段？
□ 中间件方案是否覆盖认证、授权、错误处理？
□ 数据库迁移策略是否明确？
□ 缓存/限流/监控方案是否各有至少一条？
□ 服务方法签名命名是否一致？
□ 事务边界是否在 Service 方法粒度明确？
□ frontmatter 字段是否正确填写？
□ 复杂后端场景是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的 Service / Repository / Event / external dependency 是否存在于正文表格？
□ api-contract.md 中的 message / cron / cli / sdk contract 是否被 backend design 承接？
□ 无 MQ / async / worker / cron 时是否写明不适用原因？
□ 每个写操作是否说明事务边界、一致性要求、失败补偿和幂等策略？
□ 外部依赖是否说明 timeout、retry、fallback、error mapping？
□ deployment / rollout / rollback 是否有明确结论，或写明沿用现有部署拓扑的原因？
□ Security Design 是否覆盖 AuthN、AuthZ、Tenant isolation、PII、Audit、Abuse prevention 和 Dependency security？
□ 后端实现路径是否能反向追溯到 Domain ID、AC ID、Contract 和 Test Focus？
□ 若启用 `ship-grill-me`，blocking design grill question 是否已 resolved，non-blocking question 是否已进入 Open Questions / Risk section？
```

全部通过后，将 `stage_status` 设为 `ready`，`evidence_complete` 设为 `true`。
