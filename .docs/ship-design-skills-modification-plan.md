---
title: "ShipKit 三个设计技能详细修改计划"
created_at: "2026-05-31"
scope: "skills/ship-contract, skills/ship-backend-design, skills/ship-frontend-design"
source: ".docs/ship-design-skills-optimization-suggestions.md"
focus: "PlantUML 图示协议、跨文档追踪、复杂项目设计表达、可评审性、可验证性"
status: "draft"
---

# ShipKit 三个设计技能详细修改计划

## 1. 修改目标

本计划用于指导后续直接修改以下 6 个文件：

- `skills/ship-contract/SKILL.md`
- `skills/ship-contract/references/api-contract-template.md`
- `skills/ship-backend-design/SKILL.md`
- `skills/ship-backend-design/references/backend-design-template.md`
- `skills/ship-frontend-design/SKILL.md`
- `skills/ship-frontend-design/references/frontend-design-template.md`

目标不是重写三个 skill，而是在现有结构上做协议层增强：

- 简单项目仍保持轻量，不强制画图或填复杂矩阵。
- 复杂项目有明确触发条件，agent 知道什么时候推荐 PlantUML 图示。
- Contract、Backend、Frontend 三份设计文档能通过统一追踪链互相校验。
- 复杂业务流程、异步消息、状态机、权限流、事务一致性、前端状态流都有稳定表达方式。
- Verification 从单文档 checklist 增强为“文档内部一致 + 跨文档一致”。

## 2. 已理解的现状证据

本计划基于已读取的优化建议和目标 skill/template 文件。关键现状如下。

### 2.1 `ship-contract`

已具备：

- `Scope Adaptation` 覆盖 `rest`、`grpc`、`message`、`cron`、`cli`、`sdk` 多种 contract form。
- `Machine-Readable Contract Policy` 已要求 OpenAPI、JSON Schema、Zod、proto、Avro 等机器可读产物或说明原因。
- `Output: api-contract.md` 已要求接口关联 AC ID 和 consumer / entrypoint。
- template 已有 REST、gRPC、message、cron、cli、sdk 的详细写法。
- Verification 已覆盖 Domain ID、AC ID、请求响应、错误码、共享模型、分页、认证、版本策略。

缺口：

- 缺少统一 `Diagram Guidance`。
- 缺少跨所有 contract form 的 Consumer / Provider Matrix。
- 业务流程、状态迁移、幂等重试、兼容性规则可以更显式。
- 错误码表缺少“用户可恢复、是否可重试、前端处理、后端日志级别”等列。
- Verification 未检查图示与正文、contract/backend/frontend 的一致性。

### 2.2 `ship-backend-design`

已具备：

- 已有 Domain ID 到代码模块、Service、Repository、DB 的实现链路要求。
- Process 中已要求 ER 图、数据模型、Service、接口实现映射、横切关注点、迁移策略、非功能方案。
- template 已强调 Contract-to-Implementation Map、事务、一致性、外部集成、风险验证。
- Verification 已覆盖 Domain 映射、接口实现映射、数据模型、审计字段、索引、中间件、迁移、缓存/限流/监控。

缺口：

- ER 图之外缺少统一 PlantUML 图示协议。
- Runtime component、服务交互、异步事件、outbox、DLQ、事务补偿、读写路径还未形成固定输出结构。
- Security 仍混在横切关注点中，复杂项目需要单独展开。
- Data lifecycle、retention、PII、租户隔离、审计不可变性表达不足。
- Verification 未强制检查 backend design 是否承接 message contract、state enum、error mapping。

### 2.3 `ship-frontend-design`

已具备：

- 已强调 UI/UX 设计稿是事实源，不能凭空想象页面。
- 已有 Page Tree、组件分层、Page-API Mapping、状态管理、路由权限、UI evidence index。
- `Page-API Mapping Protocol` 已要求页面操作粒度，并声明接口与页面双向一致。
- template 已覆盖 visual evidence、component architecture、state/data flow、routing/permission、loading/error/empty。
- Verification 已覆盖 UI evidence、页面树、组件数据来源、Page-API Mapping、接口引用、状态管理、权限、性能、SEO、无障碍、响应式。

缺口：

- 缺少统一 PlantUML 图示协议和复杂用户流触发条件。
- UI State Matrix、Frontend Data Ownership、Permission UX、Design Evidence Quality 还未模板化。
- Page-to-Contract 双向覆盖可以更具体到错误码、loading/empty/error 状态。
- Accessibility / Responsive 需要按关键页面或组件展开，而不是只列原则。
- Verification 未明确检查图中的页面、状态、接口是否与正文和 contract 一致。

## 3. 总体改造原则

### 3.1 保持轻量，不把简单项目复杂化

所有新增内容必须使用以下口径：

- “复杂项目建议”而不是“一律必须”。
- 简单项目可合并章节或写“不适用 + 原因”。
- 图示用于说明设计决策，不作为装饰。
- 若复杂项目未画图，需要说明原因。

### 3.2 统一图示协议，不制造新事实源

三个 skill 都新增 `Diagram Guidance`，但避免三份各写一套冲突规则。

统一规则：

- 推荐使用 PlantUML source 写入 Markdown，不要求渲染图片入库。
- 图示必须有标题，避免 `System Flow` 这类泛名。
- 图下方必须写说明：范围、参与方、关键路径、异常路径、未覆盖范围、一致性检查。
- 图中的 page、contract、service、repository、event、state 名称必须与正文表格保持一致。
- 复杂项目至少覆盖一个关键异常路径，不能只画 happy path。

### 3.3 统一跨文档追踪链

三个 skill 都应承认并维护同一条追踪链：

```text
Requirement Domain ID
→ AC ID
→ Contract operation / event / task
→ Backend handler / service / repository / storage
→ Frontend page / user action / state
→ Verification item / test scenario
```

推荐矩阵字段：

```markdown
| Domain ID | AC ID | Contract | Frontend Page/Action | Backend Implementation | Test Focus |
|---|---|---|---|---|---|
```

落地口径：

- `ship-contract` 先记录 Domain / AC / Contract / Consumer / Entrypoint。
- `ship-backend-design` 补齐 Contract / Handler / Service / Repository / Storage。
- `ship-frontend-design` 补齐 Page / User Action / State / Error UX。
- 三个 template 都放入 `Traceability Matrix` 建议章节，允许按项目复杂度合并到现有 mapping 表。

## 4. P0 修改计划：统一协议与最低可评审性

P0 是必须先做的最小闭环，完成后复杂项目至少能稳定表达图示和跨文档追踪。

### 4.1 修改 `skills/ship-contract/SKILL.md`

#### 4.1.1 在 `Scope Adaptation` 后新增 `Diagram Guidance`

建议位置：`Scope Adaptation` 与 `Delegation Boundary` 之间。

新增内容要点：

- 简单项目不强制画图。
- 复杂项目推荐使用 PlantUML。
- 推荐图类型：sequence diagram、activity diagram、state diagram、component diagram。
- 触发条件：多业务域、异步消息、状态机、第三方依赖、幂等重试、评审者难以仅靠表格理解。
- 每张图必须补充说明：范围、参与方、关键路径、异常路径、未覆盖范围、一致性检查。

验收标准：

- `ship-contract/SKILL.md` 中存在 `## Diagram Guidance`。
- 文案明确“复杂项目建议”，没有把简单项目强制复杂化。
- 提到图中 contract / event / state 必须与正文表格一致。

#### 4.1.2 在 `Process` 中插入图示与追踪步骤

建议调整：

- Step 3 后增加“为复杂业务补充 Business Flow / State Contract”。
- Step 6 的“自检与交叉验证”扩展为“自检、追踪矩阵与跨文档验证”。

验收标准：

- Process 中能看出图示不是额外装饰，而是复杂流程设计的一部分。
- Process 中出现 Traceability Matrix 或等价表达。

#### 4.1.3 在 `Output: api-contract.md` 推荐覆盖点中新增 P0 小节

新增推荐覆盖点：

- `Consumer / Provider Matrix`
- `Business Flow Contract`
- `State Contract`
- `Traceability Matrix`
- `Diagrams / Visual Aids`

注意：不要删除已有 REST/gRPC/message/cron/cli/sdk 内容。

验收标准：

- 新增小节与现有 `#### 1. 接口规约概览` 等格式一致。
- Consumer / Provider Matrix 覆盖 REST、gRPC、message、cron、cli、sdk，而不仅是 HTTP。

#### 4.1.4 增强 `Verification`

在现有 checklist 后追加：

```text
□ 复杂场景是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的 contract / event / task / state 是否存在于本文正文表格？
□ 是否存在 Consumer / Provider Matrix，或说明本期不适用原因？
□ 每个关键 contract 是否能追溯到 Domain ID、AC ID、consumer / entrypoint？
□ 状态 enum 是否有合法状态迁移说明？
□ 写接口、message、cron、CLI 副作用命令是否说明幂等和重试策略？
```

验收标准：

- Verification 同时覆盖图示、consumer/provider、状态迁移、幂等重试。
- 不与已有 checklist 重复到难以维护。

### 4.2 修改 `skills/ship-contract/references/api-contract-template.md`

#### 4.2.1 在 `必答问题` 中增加复杂项目问题

新增问题：

- 是否存在跨接口业务流程、状态迁移或异步链路需要图示辅助评审？
- 每个 contract 的 provider、consumer、entrypoint、调用时机是否明确？
- 状态 enum 是否定义了合法迁移和非法迁移错误？
- 写操作、message、cron、CLI 副作用命令的幂等与重试边界是什么？

验收标准：

- 必答问题不只面向 REST，也适用于 message/cron/cli/sdk。

#### 4.2.2 在推荐写法中新增 `Consumer / Provider Matrix`

建议位置：`Summary / Key Decisions` 后、`Global Conventions` 前。

表格：

```markdown
| Contract | Provider | Consumer | Entrypoint | AC ID | 调用时机 | 是否阻塞主流程 |
|---|---|---|---|---|---|---|
```

验收标准：

- 表格字段与优化建议一致。
- 说明可覆盖 REST、gRPC、message、cron、cli、sdk。

#### 4.2.3 新增 `Diagrams / Visual Aids`

建议位置：`Consumer / Provider Matrix` 后。

内容包括：

- 推荐 sequence diagram 表达业务调用顺序。
- 推荐 state diagram 表达状态迁移。
- 图下说明格式。
- 不要求渲染图片入库。

验收标准：

- 包含 PlantUML 示例或最小格式。
- 图示说明覆盖范围、参与方、关键路径、异常路径、未覆盖范围、一致性检查。

#### 4.2.4 新增 `Traceability Matrix`

建议位置：`Change Impact / Open Questions` 前。

表格：

```markdown
| Domain ID | AC ID | Contract | Consumer / Entrypoint | Shared Model / Error Code | Test Focus |
|---|---|---|---|---|---|
```

验收标准：

- contract template 中的矩阵不要求填 backend/frontend 细节，但要为下游预留字段或说明由下游补齐。

### 4.3 修改 `skills/ship-backend-design/SKILL.md`

#### 4.3.1 新增 `Diagram Guidance`

建议位置：`Domain-Driven Design Approach` 后、`Process` 前。

内容要点：

- 复杂后端推荐 PlantUML component、sequence、ER style class、deployment diagram。
- 触发条件：多服务、第三方依赖、message/worker、复杂事务、一致性补偿、权限/租户隔离、部署拓扑。
- 图必须与 Domain Map、Contract-to-Implementation Map、Service、Repository、Event 表一致。

验收标准：

- 明确 ER 图不是唯一图示类型。
- 明确 message contract 必须在 backend design 中有承接图或表。

#### 4.3.2 调整 `Process`

建议修改点：

- Step 4 从“ER 图 + 表结构”扩展为“数据模型与状态/关系图”。
- Step 6 后增加“服务交互、事件流、事务一致性设计”。
- Step 7 的横切关注点中明确安全设计要独立覆盖 AuthN/AuthZ/Tenant/PII/Audit/Abuse。

验收标准：

- Process 能覆盖 Runtime Component、Transaction/Consistency、Domain Event。

#### 4.3.3 在推荐覆盖点中新增 P0 小节

新增：

- `Runtime Component Diagram`
- `Transaction / Consistency Matrix`
- `Service Interaction Protocol`
- `Domain Event / Message Design`
- `Cross-Document Traceability Matrix`

验收标准：

- 保留现有 Domain Map、Data Model、Service、Contract-to-Implementation Map。
- 新增内容与现有 `#### 4. 数据模型设计`、`#### 6. 接口实现映射` 不冲突。

#### 4.3.4 增强 `Verification`

新增：

```text
□ 复杂后端场景是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的 Service / Repository / Event / external dependency 是否存在于正文表格？
□ api-contract.md 中的 message / cron / cli / sdk contract 是否被 backend design 承接？
□ 每个写操作是否说明事务边界、一致性要求、失败补偿和幂等策略？
□ 外部依赖是否说明 timeout、retry、fallback、error mapping？
□ 后端实现路径是否能反向追溯到 Domain ID、AC ID、Contract 和 Test Focus？
```

验收标准：

- Verification 覆盖图示一致性、异步承接、事务一致性、外部依赖、跨文档追踪。

### 4.4 修改 `skills/ship-backend-design/references/backend-design-template.md`

#### 4.4.1 增强 `必答问题`

新增：

- 当前后端运行时组件和外部依赖边界是什么？
- 哪些调用同步阻塞主流程，哪些通过事件或 worker 异步处理？
- `api-contract.md` 中的 message/cron/cli/sdk contract 如何落到 producer/consumer/job/command handler？
- 事务失败后如何补偿，幂等键来自哪里？

验收标准：

- 必答问题能覆盖非 HTTP 后端入口。

#### 4.4.2 新增 `Diagrams / Visual Aids`

建议位置：`Summary / Architecture Decisions` 后。

推荐图：

- Runtime Component Diagram
- Service Interaction Sequence Diagram
- ER style class diagram
- Deployment Diagram

验收标准：

- 每张图要求有说明，不只贴 PlantUML。

#### 4.4.3 新增矩阵模板

新增表格：

```markdown
| 操作 | 涉及聚合 | 事务边界 | 一致性要求 | 失败补偿 | 幂等策略 |
|---|---|---|---|---|---|
```

```markdown
| 调用方 | 被调用方 | 调用方式 | 超时 | 重试 | 熔断/降级 | 错误映射 |
|---|---|---|---|---|---|---|
```

```markdown
| Event | Producer | Consumer | 触发事务点 | Outbox | Retry | DLQ |
|---|---|---|---|---|---|---|
```

```markdown
| Domain ID | AC ID | Contract | Handler | Service | Repository / Gateway | Storage / External | Test Focus |
|---|---|---|---|---|---|---|---|
```

验收标准：

- 矩阵放在合适章节，不打断现有推荐写法。
- 明确小项目可合并或写不适用原因。

### 4.5 修改 `skills/ship-frontend-design/SKILL.md`

#### 4.5.1 新增 `Diagram Guidance`

建议位置：`UI/UX-Driven Design Philosophy` 后、`Delegation Boundary` 前。

内容要点：

- 复杂前端推荐 PlantUML activity、sequence、component diagram。
- 触发条件：多步骤表单、审批/支付/导入导出、复杂权限、多页面共享状态、实时刷新、离线/弱网、复杂错误恢复。
- 图中的页面、用户操作、状态、接口必须与 Page Tree、Page-API Mapping、State Matrix 一致。

验收标准：

- 明确没有设计稿时仍不能凭图示替代 UI evidence。
- 图示只辅助流程，不替代页面事实源。

#### 4.5.2 调整 `Process`

建议修改点：

- Step 1 增加设计证据等级记录。
- Step 2 增加复杂用户流 / 异常流 / 权限流。
- Step 5 增加 Page-to-Contract bidirectional coverage。
- Step 6 增加状态所有权与 UI State Matrix。

验收标准：

- Process 能覆盖 Design Evidence Quality、User Flow、UI State Matrix、Data Ownership。

#### 4.5.3 增强 `Page-API Mapping Protocol`

新增反向覆盖规则：

```markdown
| 页面操作 | 使用接口 | contract 是否存在 | 错误码是否覆盖 | loading/empty/error 是否设计 |
|---|---|---|---|---|
```

验收标准：

- 既检查页面调用未定义接口，也检查 contract 接口无人使用。
- 错误码和 UI 状态被纳入覆盖检查。

#### 4.5.4 在推荐覆盖点中新增 P0 小节

新增：

- `User Flow Diagram`
- `UI State Matrix`
- `Frontend Data Ownership`
- `Page-to-Contract Bidirectional Coverage`
- `Cross-Document Traceability Matrix`

验收标准：

- 不弱化原有 UI/UX evidence、Page Tree、Component List。

#### 4.5.5 增强 `Verification`

新增：

```text
□ 复杂用户流是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的页面 / 用户操作 / 状态 / 接口是否存在于 Page Tree、Page-API Mapping、State Matrix？
□ 每个关键页面是否覆盖 loading、empty、error、permission denied 等状态，或说明不适用原因？
□ 每个页面操作调用的接口是否存在于 api-contract.md？
□ api-contract.md 中面向前端的接口是否至少有一个页面操作消费，或说明是非前端 consumer？
□ 401 / 403 / 404 / 409 等关键错误码是否有对应 UX 处理？
□ 前端设计是否能追溯到 Domain ID、AC ID、Contract、Page Action 和 Test Focus？
```

验收标准：

- Verification 覆盖图示一致性、UI 状态、错误码 UX、跨文档追踪。

### 4.6 修改 `skills/ship-frontend-design/references/frontend-design-template.md`

#### 4.6.1 增强 `必答问题`

新增：

- 每个页面视觉证据等级是什么，哪些交互或状态缺失？
- 复杂用户流是否需要图示辅助评审？
- 每个关键页面的 loading/empty/error/permission/offline 状态如何表现？
- URL state、local state、server state、global app state、derived state 分别由谁拥有？
- contract 错误码如何映射到 UI 反馈？

验收标准：

- 必答问题覆盖复杂交互、状态所有权、错误 UX。

#### 4.6.2 新增 `Design Evidence Quality`

建议位置：`UI Evidence Index` 内或之后。

表格：

```markdown
| 页面 | 证据等级 | 来源 | 缺失信息 | 采用假设 |
|---|---|---|---|---|
```

等级定义：

- `high`：Figma final design / design system / 完整交互说明。
- `medium`：截图 / 原型 / 局部设计稿。
- `low`：wireframe / 用户口述 / 暂存假设。

验收标准：

- 强调低证据等级不能假装已定稿。

#### 4.6.3 新增 `Diagrams / Visual Aids`

建议位置：`Page Tree / Flow Map` 后。

推荐图：

- User Flow activity diagram。
- Page/API sequence diagram。
- Frontend state/component flow diagram。

验收标准：

- 图示不替代 UI evidence。
- 图示说明包括异常路径和权限路径。

#### 4.6.4 新增状态与权限矩阵

新增表格：

```markdown
| 页面 | 状态 | 触发条件 | UI 表现 | 可执行操作 |
|---|---|---|---|---|
```

```markdown
| 状态 | Owner | 存储位置 | 更新来源 | 是否持久化 | 不变量 |
|---|---|---|---|---|---|
```

```markdown
| 权限场景 | 页面/组件表现 | 接口错误 | 前端处理 |
|---|---|---|---|
```

验收标准：

- 状态矩阵至少提示 initial/loading/empty/error/partial success/optimistic/permission denied/offline。
- Permission UX 覆盖未登录、无权限、数据不可见。

#### 4.6.5 新增 Accessibility / Responsive Detail

表格：

```markdown
| 页面/组件 | Keyboard | Screen Reader | Focus | Contrast | Mobile Behavior |
|---|---|---|---|---|---|
```

验收标准：

- 不只写“语义化 HTML、ARIA”。
- 提醒 Modal、Dropdown、Table、Form、Toast、Date picker、Drag and drop 等关键组件。

## 5. P1 修改计划：增强复杂项目表达能力

P1 在 P0 的统一协议上，补齐三个 skill 各自的复杂项目专项能力。

### 5.1 `ship-contract` P1

#### 5.1.1 强化 Compatibility / Versioning

修改位置：`Machine-Readable Contract Policy` 或 `Output` 推荐覆盖点中的接口变更日志附近。

新增规则：

- 新增 response 字段必须默认 optional，或说明 consumer 兼容性。
- 新增 request 必填字段通常是 breaking change。
- enum 新增值可能破坏前端 switch exhaustiveness，必须提示默认处理。
- error code 新增需要前端默认 fallback。
- message topic 不兼容变更必须发布 `v2` topic，不原地破坏 schema。
- SDK public API deprecation 周期必须明确。

验收标准：

- 文档能指导 breaking / non-breaking / additive 的分类。

#### 5.1.2 强化 Error Handling Contract

在 template 的 `Error Model` 中把示例表升级为：

```markdown
| 错误码 | HTTP/gRPC Code | 触发条件 | 用户可恢复 | 是否可重试 | 前端处理 | 后端日志级别 |
|---|---|---|---|---|---|---|
```

验收标准：

- 前端 UX 和后端 logging 都能从错误码表得到依据。

#### 5.1.3 标准化 Idempotency / Retry Contract

新增表格：

```markdown
| Contract | 幂等要求 | 幂等键来源 | 重复请求行为 | 超时后是否可重试 | 冲突响应 |
|---|---|---|---|---|---|
```

适用范围：写接口、message consumer、cron/batch、CLI 副作用命令。

验收标准：

- 不只服务 HTTP POST，也覆盖异步和运维入口。

### 5.2 `ship-backend-design` P1

#### 5.2.1 增强 Data Lifecycle / Retention

在 SKILL 推荐覆盖点和 template `Migration / Operations / Reliability` 中加入：

```markdown
| 数据对象 | 敏感级别 | 保留周期 | 删除策略 | 脱敏/加密 | 审计要求 |
|---|---|---|---|---|---|
```

覆盖：归档、PII 脱敏、删除恢复、保留周期、审计不可变、多租户隔离、敏感字段加密。

验收标准：

- 敏感数据处理不再只作为泛泛安全项。

#### 5.2.2 强化 Security Design

从 Cross-Cutting Concerns 中单独列出 `Security Design` 推荐覆盖点。

至少覆盖：

- AuthN
- AuthZ
- Tenant isolation
- Sensitive data
- Audit
- Abuse prevention
- Dependency security

验收标准：

- Verification 中有 Security Design 检查。

#### 5.2.3 增加 Read / Write Path Design

新增表格：

```markdown
| 场景 | 写模型 | 读模型 | 缓存 | 索引 | 一致性延迟 |
|---|---|---|---|---|---|
```

适用：CQRS、搜索、Redis 缓存、报表宽表、高并发列表查询。

验收标准：

- 复杂查询和写路径不会混在一个“Service 方法”描述里。

### 5.3 `ship-frontend-design` P1

#### 5.3.1 强化 Permission UX

在 SKILL 和 template 中加入权限 UX 表：

```markdown
| 权限场景 | 页面/组件表现 | 接口错误 | 前端处理 |
|---|---|---|---|
```

要求覆盖：未登录、无权限、数据不可见、操作被禁用、资源不存在但不能泄露存在性。

验收标准：

- 不只写 route guard。

#### 5.3.2 强化 Design Evidence Quality

在 SKILL 的 UI evidence 相关位置说明证据等级。

验收标准：

- `evidence_complete` 的判断能区分 high/medium/low，而不是只看“有链接”。

#### 5.3.3 强化 Accessibility / Responsive Detail

在 template `Routing / Permission / UX Edge Cases` 或 `Non-Functional Decisions` 增加表格。

验收标准：

- 关键组件的 keyboard、screen reader、focus、contrast、mobile behavior 有落点。

## 6. P2 修改计划：增强可运行、可测试与长期维护

P2 不阻塞 P0/P1，但建议纳入计划文件，后续分批实施。

### 6.1 三个 skill 统一补 `Test Focus / Verification Scenario`

新增口径：每个设计文档的 Traceability Matrix 最后一列必须能导出测试关注点。

推荐字段：

```markdown
| Domain ID | AC ID | Design Surface | Scenario | Expected Result | Evidence |
|---|---|---|---|---|---|
```

落地方式：

- `ship-contract`：按 contract operation / event / error code 生成 Test Focus。
- `ship-backend-design`：按 service method / transaction / event consumer 生成 Test Focus。
- `ship-frontend-design`：按 page action / UI state / permission UX 生成 Test Focus。

验收标准：

- 后续 `ship-delivery-plan` 和 `ship-verify` 能直接消费这些测试关注点。

### 6.2 `ship-contract` 明确机器可读产物输出路径

已有 Machine-Readable Contract Policy，但可进一步要求路径格式。

建议补充示例：

```text
OpenAPI: docs/contracts/openapi.yaml
JSON Schema: docs/contracts/schemas/*.schema.json
Zod: src/contracts/*.schema.ts
proto: proto/<domain>/v1/*.proto
Avro: schemas/<domain>/*.avsc
```

验收标准：

- Markdown contract 不再孤立，机器可读 artifact 有 owner 和路径。

### 6.3 `ship-backend-design` 补 observability 与容量假设

新增建议：

- 核心指标：QPS、latency、error rate、queue lag、job duration、DLQ count。
- 告警阈值：按业务风险写初始阈值或说明无法确定。
- 容量假设：数据量、并发量、热点查询、缓存命中预期。

验收标准：

- 运行时风险不只停留在“加监控”。

### 6.4 `ship-frontend-design` 补埋点、性能预算、可访问性测试点

新增建议：

- Analytics events：关键页面进入、关键操作提交、失败原因、转化漏斗。
- Performance budget：首屏、交互延迟、列表渲染规模、bundle 分包。
- Accessibility tests：键盘路径、focus trap、screen reader label、contrast。

验收标准：

- 前端非功能方案可被测试或观测。

## 7. 推荐实施顺序

### Phase 0：修改前基线确认

目标：避免误改和遗漏。

步骤：

1. 读取 6 个目标文件。
2. 确认当前章节锚点：`Process`、`Output`、`Verification`、template `必答问题`、template `推荐写法`。
3. 记录修改前 `rg -n "Diagram Guidance|Traceability Matrix|Consumer / Provider|UI State Matrix|Transaction / Consistency" skills/ship-*` 输出，作为基线。

验证：

- 能列出每个目标文件将插入的具体位置。

### Phase 1：落地 P0 统一协议

目标：先打通图示和追踪链。

步骤：

1. 修改三个 `SKILL.md`，新增 `Diagram Guidance`。
2. 修改三个 template，新增 `Diagrams / Visual Aids`。
3. 三个 skill/template 增加 `Traceability Matrix` 口径。
4. 三个 skill 的 Verification 增加图示一致性与跨文档一致性检查。

验证：

```bash
rg -n "Diagram Guidance|Diagrams / Visual Aids|Traceability Matrix|PlantUML|复杂.*图" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
```

预期：6 个目标文件都能命中相关内容。

### Phase 2：落地 P1 专项增强

目标：补齐三个设计阶段对复杂项目的专项表达能力。

步骤：

1. `ship-contract` 增加 Consumer / Provider、Business Flow、State Contract、Compatibility、Error Handling、Idempotency / Retry。
2. `ship-backend-design` 增加 Runtime Component、Transaction / Consistency、Service Interaction、Domain Event / Outbox、Security、Data Lifecycle、Read / Write Path。
3. `ship-frontend-design` 增加 User Flow、UI State Matrix、Data Ownership、Permission UX、Design Evidence Quality、Accessibility / Responsive Detail。

验证：

```bash
rg -n "Consumer / Provider|State Contract|Idempotency|Compatibility|Transaction / Consistency|Domain Event|Outbox|Data Lifecycle|Read / Write|UI State Matrix|Data Ownership|Permission UX|Design Evidence Quality|Accessibility" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
```

预期：每类专项能力在对应 skill/template 中至少出现一次，且 Verification 有对应检查。

### Phase 3：落地 P2 可测试与维护增强

目标：让设计文档更容易被 delivery plan 和 verification 阶段消费。

步骤：

1. 三个 skill/template 补 `Test Focus / Verification Scenario`。
2. `ship-contract` 明确机器可读产物路径示例。
3. `ship-backend-design` 补 observability、capacity、alerting。
4. `ship-frontend-design` 补 analytics、performance budget、accessibility tests。

验证：

```bash
rg -n "Test Focus|Verification Scenario|OpenAPI|JSON Schema|Zod|proto|Avro|Observability|capacity|alert|Analytics|Performance budget|Accessibility tests" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
```

预期：P2 内容可被检索到，且没有把简单项目变成硬性复杂模板。

### Phase 4：整体一致性复查

目标：确认修改没有互相冲突。

步骤：

1. 检查三个 skill 的 `Diagram Guidance` 触发条件是否一致。
2. 检查三个 template 的图示说明字段是否一致。
3. 检查 Traceability Matrix 字段是否能串起 Domain ID、AC ID、Contract、Backend、Frontend、Test Focus。
4. 检查 “complex project recommended” 与 “simple project may omit with reason” 是否同时存在。
5. 检查没有新增“必须画图”这类过度约束。

验证：

```bash
rg -n "必须.*画图|强制.*PlantUML|不要求简单项目|复杂项目建议|不适用 \+ 原因" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
```

预期：没有简单项目强制画图的表达；有明确裁剪口径。

## 8. 逐文件修改清单

### 8.1 `skills/ship-contract/SKILL.md`

- [ ] 新增 `Diagram Guidance`。
- [ ] Process 增加复杂业务图示和追踪矩阵步骤。
- [ ] 推荐覆盖点新增 Consumer / Provider Matrix。
- [ ] 推荐覆盖点新增 Business Flow Contract。
- [ ] 推荐覆盖点新增 State Contract。
- [ ] 推荐覆盖点新增 Idempotency / Retry Contract。
- [ ] 推荐覆盖点增强 Compatibility / Versioning。
- [ ] Verification 增加图示一致性、状态迁移、幂等重试、consumer/provider 检查。

### 8.2 `skills/ship-contract/references/api-contract-template.md`

- [ ] 必答问题增加复杂流程、provider/consumer、状态迁移、幂等重试。
- [ ] 新增 Consumer / Provider Matrix 表格。
- [ ] 新增 Diagrams / Visual Aids 章节。
- [ ] 新增 Traceability Matrix。
- [ ] Error Model 表格增加用户可恢复、是否可重试、前端处理、后端日志级别。
- [ ] 新增 Compatibility / Versioning 规则。
- [ ] 新增 machine-readable artifact path 示例。

### 8.3 `skills/ship-backend-design/SKILL.md`

- [ ] 新增 `Diagram Guidance`。
- [ ] Process 增加 Runtime Component、服务交互、事件流、事务一致性。
- [ ] 推荐覆盖点新增 Runtime Component Diagram。
- [ ] 推荐覆盖点新增 Transaction / Consistency Matrix。
- [ ] 推荐覆盖点新增 Service Interaction Protocol。
- [ ] 推荐覆盖点新增 Domain Event / Message Design。
- [ ] 推荐覆盖点新增 Data Lifecycle / Retention。
- [ ] 推荐覆盖点单独强化 Security Design。
- [ ] 推荐覆盖点新增 Read / Write Path Design。
- [ ] Verification 增加图示一致性、异步承接、外部依赖、事务补偿、跨文档追踪。

### 8.4 `skills/ship-backend-design/references/backend-design-template.md`

- [ ] 必答问题增加运行时组件、同步/异步边界、message/cron/cli/sdk 承接、补偿和幂等。
- [ ] 新增 Diagrams / Visual Aids 章节。
- [ ] 新增 Transaction / Consistency Matrix。
- [ ] 新增 Service Interaction Protocol 表格。
- [ ] 新增 Domain Event / Outbox 表格。
- [ ] 新增 Traceability Matrix。
- [ ] 新增 Data Lifecycle / Retention 表格。
- [ ] 新增 Security Design 细项。
- [ ] 新增 Read / Write Path 表格。
- [ ] 新增 observability、capacity、alerting 建议。

### 8.5 `skills/ship-frontend-design/SKILL.md`

- [ ] 新增 `Diagram Guidance`。
- [ ] Process 增加设计证据等级、复杂用户流、Page-to-Contract 双向覆盖、状态所有权。
- [ ] Page-API Mapping Protocol 增加反向覆盖和错误码/UI 状态检查。
- [ ] 推荐覆盖点新增 User Flow Diagram。
- [ ] 推荐覆盖点新增 UI State Matrix。
- [ ] 推荐覆盖点新增 Frontend Data Ownership。
- [ ] 推荐覆盖点新增 Permission UX。
- [ ] 推荐覆盖点新增 Design Evidence Quality。
- [ ] 推荐覆盖点新增 Accessibility / Responsive Detail。
- [ ] Verification 增加图示一致性、UI 状态、错误码 UX、跨文档追踪。

### 8.6 `skills/ship-frontend-design/references/frontend-design-template.md`

- [ ] 必答问题增加证据等级、复杂用户流、UI 状态、状态所有权、错误码 UX。
- [ ] UI Evidence Index 增加 Design Evidence Quality 表格。
- [ ] 新增 Diagrams / Visual Aids 章节。
- [ ] 新增 UI State Matrix。
- [ ] 新增 Frontend Data Ownership 表格。
- [ ] 新增 Permission UX 表格。
- [ ] 新增 Page-to-Contract Bidirectional Coverage 表格。
- [ ] 新增 Accessibility / Responsive Detail 表格。
- [ ] 新增 analytics、performance budget、accessibility tests 建议。

## 9. 验收标准

### 9.1 P0 验收

- [ ] 三个 `SKILL.md` 都有 `Diagram Guidance`。
- [ ] 三个 template 都有 `Diagrams / Visual Aids`。
- [ ] 三个设计阶段都使用同一条 Traceability 链路。
- [ ] Verification 覆盖图示与正文一致性。
- [ ] Verification 覆盖 contract/backend/frontend 跨文档一致性。
- [ ] 简单项目不被强制画图，复杂项目未画图需要说明原因。

### 9.2 P1 验收

- [ ] `ship-contract` 覆盖 Consumer / Provider、State Contract、Compatibility、Error Handling、Idempotency / Retry。
- [ ] `ship-backend-design` 覆盖 Runtime Component、Transaction / Consistency、Service Interaction、Domain Event / Outbox、Security、Data Lifecycle、Read / Write Path。
- [ ] `ship-frontend-design` 覆盖 User Flow、UI State Matrix、Data Ownership、Permission UX、Design Evidence Quality、Accessibility / Responsive Detail。
- [ ] 三个 skill 的专项能力都在 template 中有可复制的表格或写法。

### 9.3 P2 验收

- [ ] 三个 skill 都能产出 Test Focus / Verification Scenario。
- [ ] `ship-contract` 说明机器可读产物路径或 owner。
- [ ] `ship-backend-design` 覆盖 observability、capacity、alerting。
- [ ] `ship-frontend-design` 覆盖 analytics、performance budget、accessibility tests。

### 9.4 全局验收

- [ ] 没有删除现有 contract forms、Page-API Mapping、Contract-to-Implementation Map 等核心能力。
- [ ] 新增章节不与现有章节重复冲突。
- [ ] 所有新增规则都有裁剪口径或“不适用 + 原因”。
- [ ] 图示要求不变成装饰性输出。
- [ ] 三份设计文档能通过 Domain ID / AC ID / Contract / Page / Service / Test Focus 串起来。

## 10. 修改完成后的复查命令

建议执行：

```bash
rg -n "Diagram Guidance|Diagrams / Visual Aids|Traceability Matrix|PlantUML" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
rg -n "Consumer / Provider|State Contract|Idempotency|Compatibility|Error Model" skills/ship-contract
rg -n "Runtime Component|Transaction / Consistency|Service Interaction|Domain Event|Outbox|Data Lifecycle|Security Design|Read / Write" skills/ship-backend-design
rg -n "User Flow|UI State Matrix|Data Ownership|Permission UX|Design Evidence Quality|Accessibility / Responsive" skills/ship-frontend-design
rg -n "必须.*画图|强制.*PlantUML" skills/ship-contract skills/ship-backend-design skills/ship-frontend-design
```

期望：

- 前四条能命中预期新增内容。
- 最后一条不应出现简单项目强制画图的表达；若命中，需要人工确认语义是否过度。

## 11. 风险与注意事项

- 不要把模板改成 rigid schema；当前三个 template 都明确是写作引导，新增内容应延续这个定位。
- 不要为了覆盖建议而复制大段重复文字；三个 skill 可共享规则，但每个 skill 只强调本阶段关注点。
- 不要弱化 `ship-frontend-design` 的 UI evidence 要求；PlantUML 不能替代设计稿、截图、wireframe。
- 不要让 `ship-contract` 只面向 REST；新增矩阵必须覆盖 gRPC、message、cron、cli、sdk。
- 不要把 backend 的 Security 只写成“中间件”；复杂项目必须覆盖数据隔离、审计、滥用防护。
- 不要新增与现有 `validate_contract.py` 或 orchestrator 协议冲突的硬性字段，除非后续同步更新 validator。

## 12. 最终复查清单

- [ ] 已完整阅读优化建议和 6 个目标文件。
- [ ] 已按 P0/P1/P2 拆分修改。
- [ ] 已逐文件列出具体修改点。
- [ ] 已给出每项修改的验收标准。
- [ ] 已给出实施顺序和复查命令。
- [ ] 已保留简单项目裁剪口径。
- [ ] 已避免重写现有 skill。
- [ ] 计划文档写入 `.docs/`。

