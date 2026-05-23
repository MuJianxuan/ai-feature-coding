---
name: ship-backend-design
description: "ShipKit stage. Designs backend architecture with domain modeling and data layer. Use after ship-contract completes."
---

# 后端技术方案 (Backend Design)

## Overview

后端技术方案阶段基于 requirements.md 的业务域和 api-contract.md 的接口规约，设计后端的整体架构、领域模型、数据层和服务层。

核心目标：
- 建立"业务域-服务边界-数据模型"三层设计，保证架构清晰可演进
- 每个接口都能追溯到具体的 Controller/Service/Repository 实现路径
- 数据模型完整支撑接口规约，并考虑事务、一致性与扩展性
- 横切关注点（认证、日志、限流、缓存）有统一方案

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

## Process

```
1. 选择架构模式与分层策略
   verify: 选择有 tech-selection.md 依据
2. 业务域 → 模块映射
   verify: 与 requirements.md 的 Domain ID 一一对应
3. 加载 ship-spec 约束
   verify: 已记录匹配的 `spec_id` 或“无匹配规范”
4. 设计数据模型（ER 图 + 表结构）
   verify: 支撑 api-contract.md 所有数据结构
5. 设计服务层（Service + 方法签名）
   verify: 每个 Domain 至少一个 Service
6. 接口实现映射（Controller → Service → Repository）
   verify: api-contract.md 每个接口都有映射
7. 设计中间件与横切关注点
   verify: 认证/授权/日志/错误处理覆盖
8. 制定数据库迁移策略
   verify: 含初始化脚本与升级脚本规范
9. 制定后端非功能方案
   verify: 缓存/限流/监控各至少一条
```

## Delegation Boundary

本阶段是少数允许**拥有正式产物**的并行阶段之一。

- 当 `api-contract.md.stage_status = ready` 且 Domain ID 已稳定时，可由子代理独立拥有并产出 `backend-design.md`
- 允许与 `ship-frontend-design` 并行执行，但两者只能共享 `api-contract.md`、`requirements.md` 和 `spec_context`，不可互改对方正式产物
- 子代理仍不得推进 `ship-design-review`，正式阶段切换由 orchestrator 统一收口

### 步骤详解

**Step 1: 架构模式选择**

常见选项：
- **分层架构**（Controller / Service / Repository）：适合大多数 CRUD 场景
- **六边形架构**（Hexagonal）：适合复杂业务、需要多种适配器
- **CQRS**：适合读写分离、高并发查询场景
- **微服务**：适合大型团队、独立部署需求

**Step 2: 业务域映射**

```
requirements.md         backend
D-AUTH-001 用户认证 →   src/modules/auth/
D-AUTH-002 权限管理 →   src/modules/auth/permissions/
D-ORD-001  订单创建  →   src/modules/order/
D-PAY-001  支付处理  →   src/modules/payment/
```

**Step 3: 加载 ship-spec 约束**

- 基于 `tech-selection.md` 的技术栈标签和 `requirements.md` 的 Domain ID 匹配规范
- 将命中的 `spec_id` 记录到 `backend-design.md.referenced_spec_ids`
- 无匹配规范时显式写“无匹配规范”，并把 warning 写入 `spec_warnings`

**Step 4: 数据模型设计**

- 从 api-contract.md 的数据模型反推数据库表结构
- 标注主键、外键、唯一索引、复合索引
- 考虑软删除、审计字段（created_at / updated_at / created_by）
- 标注字段的业务含义与约束

**Step 5-6: 服务层与接口映射**

每个接口必须能追溯到：
```
POST /api/v1/todos
  → TodoController.create()
    → TodoService.createTodo(dto)
      → TodoRepository.save(entity)
```

**Step 7-9: 横切关注点**

认证、授权、日志、错误处理、缓存、限流、监控均需统一方案。

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

#### 1. 后端架构概览
- 架构模式（分层 / 六边形 / CQRS）及选择依据
- 技术栈（语言 / 框架 / ORM / 数据库）来自 tech-selection.md
- 分层策略与依赖方向
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

#### 2. 业务域划分

```markdown
| Domain ID | Domain 名称 | 代码模块 | 核心 Service |
|-----------|-------------|----------|--------------|
| D-AUTH-001 | 用户认证 | modules/auth | AuthService |
| D-AUTH-002 | 权限管理 | modules/auth/permissions | PermissionService |
| D-TODO-001 | 待办管理 | modules/todo | TodoService |
```

#### 3. Referenced Specs / Constraints
- 引用的 `spec_id` 列表
- 对当前后端方案生效的关键约束
- 若无匹配规范，显式记录原因和 warnings

#### 4. 数据模型设计
- ER 图（表 + 关系）
- 每张表的 DDL（含字段类型、约束、索引）
- 索引策略说明
- 软删除/审计字段约定
- 数据迁移与初始数据

#### 5. 服务层设计

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

#### 6. 接口实现映射

api-contract.md 中每个接口的实现路径：

```markdown
| 接口 | Controller | Service 方法 | Repository | DB 操作 |
|------|------------|--------------|------------|---------|
| POST /api/v1/todos | TodoController.create | TodoService.createTodo | TodoRepository.save | INSERT todos |
| GET /api/v1/todos | TodoController.list | TodoService.listByUser | TodoRepository.findByUserId | SELECT todos |
| DELETE /api/v1/todos/:id | TodoController.delete | TodoService.deleteTodo | TodoRepository.softDelete | UPDATE todos SET deleted_at |
```

#### 7. 中间件 / 拦截器设计
- **认证中间件**：解析 JWT、注入 user 上下文
- **授权中间件**：基于角色 / 权限的访问控制
- **请求日志**：记录请求/响应、脱敏 PII
- **错误处理**：统一异常 → API 错误响应
- **限流**：按 IP / 用户 / 接口的限流策略

#### 8. 数据库迁移策略
- 迁移工具（Prisma Migrate / TypeORM / Flyway）
- 迁移命名规范（`YYYYMMDDHHmmss_description.sql`）
- 回滚策略（每个迁移配套 down 脚本）
- 生产环境迁移流程（备份 → 演练 → 灰度）

#### 9. 后端非功能方案
- **缓存**：Redis 使用场景、key 命名规范、过期策略
- **限流**：算法（令牌桶 / 漏桶）、维度、配置
- **监控**：指标（QPS / 延迟 / 错误率）、告警阈值
- **日志**：结构化日志格式、级别、采样策略
- **可观测性**：trace ID 透传、链路追踪
- **安全**：SQL 注入防护、XSS、CSRF、依赖漏洞扫描

### stage_status 流转规则

- `draft`：业务域映射、数据模型或接口映射不完整
- `ready`：所有 Domain 有对应模块，所有接口有实现路径，可进入设计评审

### evidence_complete 判定标准

- 每个 Domain ID 有对应的代码模块和 Service
- 已记录 `referenced_spec_ids` 或“无匹配规范”
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
```

全部通过后，将 `stage_status` 设为 `ready`，`evidence_complete` 设为 `true`。
