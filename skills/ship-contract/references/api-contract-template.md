# API Contract Template Reference

这是一份写作引导模板，不是固定格式。

使用原则：
- 先基于 `requirements.md`、`tech-selection.md` 和相关设计输入做判断，再决定文档结构
- 优先回答关键设计问题，而不是机械填章节
- 若项目采用 GraphQL / tRPC / gRPC，可把“接口”改写为 operation / procedure / method，但保留同等粒度的信息
- 若某部分不适用，写明“不适用 + 原因”，不要静默省略

## 必答问题

1. 这份契约要服务哪些调用方，为什么当前 API 风格最合适？
2. 全局约定是什么：
   - base URL / versioning / auth / idempotency / time format / pagination / sorting / filtering
3. 每个业务域分别暴露哪些操作，这些操作分别对应哪些 AC ID 和页面？
4. 每个操作的输入边界是什么：
   - path / query / header / body 字段、类型、必填、校验、默认值、空值语义
5. 每个操作的输出边界是什么：
   - 成功结构、空结果、分页结构、异步结果、字段含义、可为空字段
6. 失败路径如何表达：
   - HTTP status、business error code、message、details、前端处理建议、是否可重试
7. 哪些数据结构是共享模型，哪些是接口专属模型？
8. 契约中有哪些假设、兼容性约束和潜在变更点？

## 推荐写法

可按以下顺序组织，也可按项目调整：

### 1. Summary / Key Decisions

先用短段落写清：
- 契约覆盖范围
- API 风格与原因
- 本文的关键设计决策
- 明确不包含的范围

### 2. Global Conventions

建议至少覆盖：
- URL / versioning 规则
- auth 方式与权限上下文
- 通用请求头与响应 envelope
- idempotency、幂等冲突、并发控制
- 分页 / 排序 / 过滤 / 搜索 / 日期范围规范
- 时间、货币、枚举、空值和时区约定

关键示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 3. Domain Contract Blocks

按业务域分组，不按 HTTP method 平铺。每个接口块建议至少包含：
- 描述
- 关联 AC
- 关联页面 / 调用方
- 请求字段表
- 成功响应示例
- 错误响应表
- 权限 / 幂等 / 缓存 / 限流等特殊约束

关键示例：

```markdown
#### POST /api/v1/orders/:id/cancel
- **描述**：取消订单
- **关联 AC**：AC-ORD-004
- **关联页面**：OrderDetailPage
- **前置条件**：订单状态必须为 `pending`
- **请求参数**：
  | 位置 | 字段 | 类型 | 必填 | 校验 | 说明 |
  |------|------|------|------|------|------|
  | path | id | string | 是 | UUID | 订单 ID |
  | body | reason | string | 否 | max 200 | 取消原因 |
- **成功响应**：返回最新订单快照
- **错误响应**：
  | 错误码 | HTTP Status | 条件 | 前端处理 |
  |--------|-------------|------|----------|
  | 40901 | 409 | 订单已发货 | 刷新页面并提示不可取消 |
```

### 4. Shared Models

建议明确：
- 共享 DTO / schema / enum
- 字段来源与复用范围
- 哪些字段允许 `null`
- API 命名与持久化命名的映射规则

### 5. Error Model

建议按“用户可处理 / 业务冲突 / 权限问题 / 系统故障”分层整理，而不是只列数字。

关键示例：

```markdown
| 类别 | 错误码 | HTTP Status | 触发条件 | 用户提示 | 是否可重试 |
|------|--------|-------------|----------|----------|------------|
| 业务冲突 | 40901 | 409 | 订单已发货 | 当前状态不可取消 | 否 |
```

### 6. Change Impact / Open Questions

建议记录：
- 兼容性策略
- 预期高变更区域
- 暂存假设
- 后续若接口调整，前端和后端各受什么影响

### 7. Verification Snapshot

简要汇总：
- Domain 覆盖情况
- AC / 页面关联完整度
- 未闭合风险
- stage_status 是否可切到 `ready`

## 裁剪规则

- 小项目可以合并 “Summary + Global Conventions”
- GraphQL / tRPC 项目可以把“接口清单”写成 query / mutation / procedure 清单
- 没有分页场景时，可显式写“本期无分页接口”
- 没有公开 API 时，仍要写明调用方边界，例如 Web app / internal admin / worker

## 常见空话警报

- “接口遵循 RESTful 规范” 但没有解释资源边界
- “错误统一处理” 但没有错误码和差异化处理建议
- “数据模型见实现” 这会破坏 Contract-First
- “字段含义自解释” 这通常意味着含义并不清晰
