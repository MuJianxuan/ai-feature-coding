# Backend Design Template Reference

这是一份写作引导模板，不是固定格式。

使用原则：
- 先从业务域边界、数据约束和接口实现链路出发，再谈框架和目录结构
- 模板强调“后端为什么这样分层、如何承接 contract”，不是泛泛列中间件名词
- 若项目不是典型 CRUD，也要把命令流、事件流或集成边界写清楚
- 若某部分不适用，写明“不适用 + 原因”，不要静默省略

## 必答问题

1. 本次方案覆盖哪些业务域、服务边界和运行时组件？不覆盖什么？
2. 为什么选择当前架构模式：
   - layered、hexagonal、CQRS、modular monolith、microservice
3. `requirements.md` 的 Domain ID 如何映射到代码模块、聚合、Service？
4. `api-contract.md` 中每个接口如何落到实现链路：
   - controller / handler → service → repository → storage / external dependency
5. 数据模型如何支撑接口契约：
   - 表结构、约束、索引、审计字段、软删除、唯一性、状态机
6. 哪些操作需要事务，一致性边界在哪里，哪些地方接受 eventual consistency？
7. 认证、授权、日志、错误处理、缓存、限流、监控如何统一落地？
8. 与外部系统如何集成：
   - 重试、超时、幂等、补偿、降级
9. 哪些地方是高风险区域：
   - 热点查询、复杂事务、迁移风险、跨域编排、权限模型

## 推荐写法

可按以下顺序组织，也可按项目调整：

### 1. Summary / Architecture Decisions

先用短段落写清：
- 覆盖范围
- 架构模式与核心理由
- 主要模块边界
- 明确不做的内容

### 2. Domain-to-Module Map

建议先把业务边界讲清，再写类名。

关键示例：

```markdown
| Domain ID | 业务域 | 模块 | 聚合 / 核心对象 | Core Service |
|-----------|--------|------|------------------|--------------|
| D-ORD-001 | 订单管理 | modules/order | Order | OrderService |
```

### 3. Data Model / Storage Design

每个核心模型建议回答：
- 为什么需要这张表或这个集合
- 主键、外键、唯一约束
- 状态字段与状态转移
- 索引依据来自哪些查询或过滤条件
- 审计字段和删除策略

关键示例：

```markdown
### orders
- **用途**：保存订单主记录
- **关键约束**：`order_no` 唯一；`status` 仅允许 `pending|paid|shipped|cancelled`
- **索引**：
  - `idx_orders_user_id_created_at`：支撑“我的订单”按时间倒序查询
  - `idx_orders_status`：支撑后台状态筛选
```

### 4. Service Design

不要只列方法名，要说明：
- 方法职责
- 依赖
- 输入输出
- 事务边界
- 抛出的业务异常

关键示例：

```markdown
### OrderService.cancelOrder
- **职责**：校验状态、记录取消原因、回写订单状态
- **依赖**：OrderRepository, AuditLogService
- **事务边界**：单事务
- **异常**：
  - `ORDER_NOT_FOUND`
  - `ORDER_STATUS_CONFLICT`
```

### 5. Contract-to-Implementation Map

这是核心交付物之一。确保每个接口都有落点。

关键示例：

```markdown
| 接口 | Handler | Service | Repository / Gateway | 副作用 |
|------|---------|---------|----------------------|--------|
| POST /api/v1/orders/:id/cancel | OrderController.cancel | OrderService.cancelOrder | OrderRepository.updateStatus | 写审计日志 |
```

### 6. Cross-Cutting Concerns

只写与当前方案真的相关的机制：
- authn / authz
- validation
- error mapping
- structured logging
- tracing / metrics
- rate limiting
- cache
- background jobs / domain events

### 7. Migration / Operations / Reliability

建议覆盖：
- migration 工具与命名约定
- rollout / rollback
- 外部依赖失败时的重试与超时
- 观测指标和告警
- 敏感数据、审计、合规策略

### 8. Risk / Verification

建议最后收束：
- 接口映射是否全覆盖
- 数据模型是否支撑 contract
- 当前已知风险和约束
- stage_status 是否可切到 `ready`

## 裁剪规则

- 纯内部 worker 或 batch 任务可弱化 controller 层，但必须保留输入边界和失败处理
- 无数据库场景可把数据模型改写成 external storage / third-party API contract
- 小项目可以把 “Summary + Domain Map” 合并，但不要省略实现链路
- 没有缓存或限流需求时，显式写“本期不引入 + 原因”

## 常见空话警报

- “采用分层架构，职责清晰” 但没有写出每层实际边界
- “数据库按需建表” 但没有从 contract 反推字段与索引
- “统一异常处理” 但没有错误到 API 响应的映射规则
- “后续再考虑事务和权限” 这通常意味着后面会重构主链路
