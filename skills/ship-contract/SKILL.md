---
name: ship-contract
description: "ShipKit stage. Designs API contracts as the shared agreement between frontend and backend. Use after ship-tech-discovery completes."
---

# 接口规约设计 (API Contract Design)

## Overview

接口规约设计是 Contract-First 开发模式的核心阶段，负责基于 requirements.md 的业务域、tech-research.md 的项目事实发现和 tech-selection.md 的技术栈，设计端到端的接口规约。

核心目标：
- 产出前后端并行开发的"契约"，消除前后端联调时的认知差异
- project_group 需求下，表达 involved projects 之间的生产者、消费者和被影响方边界，而不是预设单项目内部前后端契约
- 定义完整的请求/响应结构、错误码体系和数据模型
- 确保每个接口可追溯到具体的验收标准（AC ID）和 consumer / entrypoint
- 基于 `Requirement-to-Reality Mapping` 判断已有 API / message / cron / cli / sdk surface 是兼容新增、扩展、废弃还是 breaking change
- 建立统一的 API 风格规范，保证接口一致性

产出物：`api-contract.md`

## When to Use

- `ship-tech-discovery` 已完成，且 `tech-selection.md.stage_status = ready`
- 项目采用前后端分离架构，需要明确接口契约
- 多团队并行开发，需要接口作为协作基准
- 需要生成 Mock 数据供前端独立开发

## When NOT to Use

- `ship-tech-discovery` 尚未完成 —— 技术栈未定无法确定 API 风格
- 纯前端且无任何外部 API / worker / batch 交互 —— 可产出显式 empty/internal contract，并说明原因
- 使用 BFF 且前后端同一人开发 —— 可简化为内部接口文档
- 纯后端批处理/定时任务 —— 仍产出 contract，但形态为消息契约 / 定时任务契约，不要求 HTTP 接口（见 Scope Adaptation）

## Contract-First Philosophy

Contract-First 的核心理念：**接口规约先于实现**。

```
传统模式：后端先写 → 前端适配 → 联调修改 → 反复迭代
Contract-First：共同定义契约 → 前后端并行开发 → 联调即验证
```

优势：
1. **并行开发**：前端基于契约 Mock，后端基于契约实现，互不阻塞
2. **减少联调成本**：契约即测试用例，联调变成验证而非调试
3. **变更可控**：接口变更必须走变更日志，影响范围可追溯
4. **自动化友好**：契约可生成 SDK、Mock Server、测试用例

## Process

```
1. 读取 requirements.md、tech-research.md、tech-selection.md
   verify: 已理解 Requirement-to-Reality Mapping、Existing Surface Inventory 和选型约束
2. 确定 API 风格与基础约定
   verify: 风格选择有 tech-selection.md 依据，且不破坏 tech-research.md 中已有 surface 约束
3. 定义通用约定（分页/排序/过滤/错误码体系）
   verify: 约定覆盖所有常见场景
4. 按业务域逐一设计接口
   verify: 每个接口关联 AC ID + 前端页面
5. 对 involved projects 做生产者、消费者、被影响方边界判断
   verify: 每个角色都有 tech-research.md 证据，不从 feature `meta.yml.projects` 预设
6. 对已有 API / route / message / cron / cli / sdk 做兼容性判断
   verify: 每个现有 surface 都标注所属 project 与 additive / compatible extension / breaking / deprecation / avoid / new
7. 提取共享数据模型
   verify: 模型覆盖所有接口的请求/响应结构
8. 完善错误码表
   verify: 错误码覆盖所有异常路径
9. 自检与交叉验证
   verify: Traceability Matrix 与 Verification Checklist 全部通过
```

## Scope Adaptation

本阶段在所有 `project_scope` 下都保留，但契约形态根据消费者和调用方式调整。`api-contract.md` 是单文件多章节产物，按选定形态裁剪。

当 `meta.yml.scenario: technical_plan_provided` 时，还必须按 `technical_plan_source.selected_scope` 裁剪 contract：只纳入 selected scope 直接需要的接口、事件、任务或 SDK surface。未选中技术方案内容不得进入本期 contract，除非作为依赖风险或 open question 记录；即便发现未选中内容相关接口，也不能把它升级为本期实现范围。

### 契约形态矩阵

| 形态 | 适用场景 | 必答问题 |
|------|---------|---------|
| `rest` REST/HTTP | 对外 API、对前端 SPA / 移动端 | 资源命名、HTTP 方法、状态码、错误码、分页/过滤约定 |
| `grpc` gRPC | 内部微服务高频通信 | proto 定义位置、流式模式（unary/server/client/bidi）、超时、重试、deadline |
| `message` 消息契约 | MQ / 事件驱动 / 异步处理 | topic / queue 名、payload schema、分区键、幂等键、重试策略、死信处理 |
| `cron` 定时任务契约 | cron / batch / scheduled job | 触发表达式、输入源、输出去向、失败补偿、并发控制、超时 |
| `cli` CLI 接口 | 工具类、运维脚本 | 子命令树、参数定义、退出码、stdin/stdout 格式、环境变量 |
| `sdk` 内部 SDK | 库类、SDK 类项目 | 公开 API 表面、版本策略、breaking change 政策、deprecation 周期 |

### 形态选择规则

1. 每个 feature 通常只选 **1-2 种形态**；多选必须有明确理由
2. 形态选择优先级：
   - 若 `ship-discover.product-brief.md` §6.2 已预判契约形态，沿用该选择
   - 否则基于 `tech-selection.md` 的技术栈推断（如选了 Kafka → 至少包含 `message`；选了 cron 框架 → 至少包含 `cron`）
   - 仍无法判定时，与用户确认
3. 选定形态后裁剪不适用章节，但必须在文档开头显式标注"本期不适用 X 形态及原因"
4. `frontmatter.contract_forms` 必须列出所有选定形态

### Machine-Readable Contract Policy

- `rest` 默认引用 OpenAPI、JSON Schema 或 Zod artifact；若只写 Markdown，必须说明暂不输出机器可读附件的原因。
- `grpc` 必须引用 `.proto` 文件路径或明确 proto 生成位置。
- `message` 必须引用 payload schema（如 Avro / JSON Schema / Protobuf）或明确 schema owner。
- `cli` / `sdk` 必须记录 command/schema 或 public API surface，包含版本策略。
- `api-contract.md` 必须有 contract changelog / change classification，至少能区分 `breaking` / `non-breaking` / `additive`。
- 维护者可运行 `python3 skills/ship-orchestrator/scripts/validate_contract.py <feature-dir>` 执行启发式检查。

### Scope 与形态的常见组合

| project_scope | 常见形态组合 |
|---------------|-------------|
| `fullstack` | `rest`（默认）；前端 + 后端通过 REST 对齐 |
| `backend_only` | 取决于消费者：对前端/移动端用 `rest` / `grpc`；纯异步用 `message`；纯定时任务用 `cron`；工具类用 `cli` 或 `sdk` |
| `frontend_only` | 通常引用已有外部契约（第三方 API / BFF）；本阶段产出"消费方契约视角"文档，记录依赖了哪些外部接口 |

### 单文件组织规则

`api-contract.md` 按以下顺序组织：

1. Summary（含本期选定的形态及理由）
2. Global Conventions（auth、版本、时间格式等所有形态共用约定）
3. 各形态专属章节（按 `contract_forms` 顺序）：
   - REST/HTTP 接口清单（如选了 `rest`）
   - gRPC service 与 proto 引用（如选了 `grpc`）
   - 消息契约清单（如选了 `message`）
   - 定时任务契约清单（如选了 `cron`）
   - CLI 命令清单（如选了 `cli`）
   - SDK 公开 API 表面（如选了 `sdk`）
4. Shared Models（跨形态共享的数据模型）
5. Error Model（统一错误体系）
6. Change Impact / Open Questions
7. Verification Snapshot

未选中的形态章节直接省略，但 §1 Summary 中显式列出"本期不适用：X、Y，原因：……"。

## Diagram Guidance

复杂项目建议使用 PlantUML source 写入 Markdown 辅助评审，不要求渲染图片入库；简单项目不强制画图，可合并章节或写明“不适用 + 原因”。图示必须服务于契约设计决策，不能作为装饰。

推荐图类型：
- sequence diagram：表达跨接口、跨服务或同步/异步调用顺序
- activity diagram：表达业务流程、异常分支和人工/系统步骤
- state diagram：表达订单、审批、任务等有状态对象的合法迁移
- component diagram：表达 provider、consumer、外部系统和消息通道边界

推荐触发条件：
- 多业务域、多 contract form 或多 consumer 协作
- 存在异步消息、定时任务、第三方依赖或 worker 链路
- 存在状态机、幂等重试、补偿或兼容性风险
- 评审者难以仅靠表格理解调用顺序或异常路径

每张图下方必须补充：范围、参与方、关键路径、至少一个关键异常路径、未覆盖范围、一致性检查。图中的 contract、event、task、command、state 名称必须与正文表格、Shared Models 和 Error Model 保持一致。

若存在 `blocking_gaps`，必须保持 `stage_status: draft` 或 meta blocked，不得进入下游。

## Delegation Boundary

本阶段属于 `forbidden` 节点，**禁止启动任何子代理**，包括辅助委派与只读支线。

- `api-contract.md` 是后续前后端并行的共享基线，必须保持单一事实源
- 即使是资料搜集、草稿比对、只读检查，也必须在当前主上下文内完成，不得拆给子代理
- 只有主上下文可以定稿请求/响应结构、错误码体系和共享数据模型

### 步骤详解

**Step 1: 确定 API 风格**

先读取 `tech-research.md`：
- `Requirement-to-Reality Mapping`：识别每个 Domain / AC 对应的现有 surface 关系类型
- `Existing Surface Inventory`：识别已有 API、RPC、message topic、cron、CLI、SDK、前端 consumer 和后端 provider
- `Evidence and Uncertainty`：把证据不足的 surface 标为 Open Question 或 assumption，不得当作已确认事实

再基于 tech-selection.md 中的技术栈选择：
- RESTful：适合资源导向的 CRUD 场景
- GraphQL：适合前端需要灵活查询的场景
- tRPC：适合全栈 TypeScript 项目
- gRPC：适合微服务间通信

**Step 2: 定义通用约定**

必须覆盖：
- 基础 URL 结构与版本策略
- 认证方式（Bearer Token / Cookie / API Key）
- 请求/响应通用格式
- 分页、排序、过滤的参数规范
- 错误响应统一结构

**Step 3: 按业务域设计接口**

遍历 requirements.md 中的每个 Domain ID：
- 识别该域需要的所有操作（CRUD + 业务操作）
- 对照 `tech-research.md` 判断该操作是复用、扩展、替换、新增、避免还是 unknown
- 若已有 API surface 存在，先判断兼容新增、breaking change、deprecation 或 versioning 策略，不默认新建 endpoint
- 为每个操作设计接口（方法 + 路径 + 参数 + 响应）
- 标注关联的 AC ID 和调用页面
- message / cron / cli / sdk 形态需结合 Existing Surface Inventory，而不是只从 tech-selection 推断
- 复杂业务补充 Business Flow Contract / State Contract，必要时使用 PlantUML 展示调用顺序、异常路径和状态迁移

**Step 4-6: 数据模型与错误码**

- 从接口中提取重复出现的数据结构，抽象为共享模型
- 为每种异常场景分配错误码，确保前端可据此做差异化处理
- 建立 Traceability Matrix，串起 Domain ID、AC ID、Contract、consumer / entrypoint、Shared Model / Error Code 和 Test Focus，并与后续 frontend/backend design 交叉验证

## API Convention Standards

### RESTful 命名规范

```
资源命名：复数名词，kebab-case
  GET    /api/v1/todo-items          → 列表
  POST   /api/v1/todo-items          → 创建
  GET    /api/v1/todo-items/:id      → 详情
  PUT    /api/v1/todo-items/:id      → 全量更新
  PATCH  /api/v1/todo-items/:id      → 部分更新
  DELETE /api/v1/todo-items/:id      → 删除

嵌套资源：最多两层
  GET    /api/v1/users/:userId/orders

业务操作：动词后缀
  POST   /api/v1/orders/:id/cancel
  POST   /api/v1/orders/:id/confirm
```

### 通用响应格式

```typescript
// 成功响应
interface SuccessResponse<T> {
  code: 0;
  data: T;
  message: string;
}

// 分页响应
interface PaginatedResponse<T> {
  code: 0;
  data: {
    items: T[];
    pagination: {
      page: number;
      pageSize: number;
      total: number;
      totalPages: number;
    };
  };
  message: string;
}

// 错误响应
interface ErrorResponse {
  code: number;       // 业务错误码（非 0）
  message: string;    // 用户可读的错误信息
  details?: object;   // 字段级错误详情（表单校验）
}
```

### 分页/排序/过滤参数

```
分页：?page=1&pageSize=20
排序：?sort=createdAt&order=desc
过滤：?status=active&keyword=search
日期范围：?startDate=2026-01-01&endDate=2026-12-31
```

## Output: api-contract.md

编写前先读取 [`references/api-contract-template.md`](./references/api-contract-template.md)。

使用规则：
- 模板是写作引导，不是 rigid schema；章节顺序可调整，不适用章节可裁剪
- 模板中的“必答问题”必须被显式回答；若当前项目不适用，需写明原因
- `api-contract.md` 仍以本文件定义的 frontmatter、stage_status 和 verification 要求为准

### Frontmatter

```yaml
---
stage: ship-contract
stage_status: draft  # draft / ready
contract_forms: []   # rest | grpc | message | cron | cli | sdk 中的一个或几个
updated_at: ""
evidence_complete: false
---
```

`contract_forms` 字段规则：

- 至少包含一个值；空数组等同于 `stage_status` 不可置 `ready`
- 多值时必须在文档 §1 Summary 中说明每种形态服务的调用方
- 未列入的形态在 §1 Summary 中显式标注"本期不适用：X，原因：……"
- 形态选择规则见 [Scope Adaptation](#scope-adaptation) 章节

### 推荐覆盖点

以下内容是推荐覆盖点，不要求固定章节顺序；可按项目复杂度合并或拆分，但需确保模板中的必答问题有对应答案。

#### 1. 接口规约概览
- API 风格（RESTful / GraphQL / tRPC）及选择依据
- 基础 URL（如 `/api/v1`）
- 认证方式与 Token 传递规范
- 版本策略（URL 路径 / Header / Query）

#### 2. 通用约定
- 请求/响应通用格式（含 TypeScript interface）
- 分页参数规范与默认值
- 排序/过滤参数规范
- 错误响应统一结构
- 日期时间格式（ISO 8601）
- 空值处理规则（null vs undefined vs 不传）

#### 3. 接口清单（按业务域分组）

每个接口包含：

```markdown
### [D-XXX-NNN] 业务域名称

#### POST /api/v1/resource
- **描述**：创建资源
- **关联 AC**：AC-XXX-001, AC-XXX-002
- **关联 consumer / entrypoint**：CreateResourcePage / route action / background worker
- **请求参数**：
  | 位置 | 字段 | 类型 | 必填 | 校验规则 | 说明 |
  |------|------|------|------|----------|------|
  | body | name | string | 是 | 1-50字符 | 资源名称 |
- **成功响应** (200)：
  ```json
  { "code": 0, "data": { "id": "xxx", "name": "xxx" }, "message": "ok" }
  ```
- **错误响应**：
  | 错误码 | HTTP Status | 触发条件 | 处理建议 |
  |--------|-------------|----------|----------|
  | 40001  | 400         | name 为空 | 提示用户填写 |
```

#### 4. Consumer / Provider Matrix

覆盖所有选定 contract form（REST、gRPC、message、cron、cli、sdk），说明谁提供、谁消费、从哪里触发、何时调用，以及是否阻塞主流程。

```markdown
| Contract | Provider | Consumer | Entrypoint | AC ID | 调用时机 | 是否阻塞主流程 |
|---|---|---|---|---|---|---|
```

#### 4.1 Existing Surface Compatibility

来自 `tech-research.md` 的现有 surface 必须逐项处理：

```markdown
| Existing Surface | Source Evidence | Required Change | Compatibility | Decision | Risk / Follow-up |
|---|---|---|---|---|---|
| GET /api/users/:id | src/routes/user.ts | 返回 nickname/avatar | compatible extension | extend existing endpoint | avatar 字段归属待确认 |
```

Compatibility 建议使用：`additive`、`compatible extension`、`breaking`、`deprecation`、`avoid`、`new`、`unknown`。

#### 5. Business Flow Contract / Diagrams

复杂流程建议补充 PlantUML sequence / activity diagram，并在图下说明范围、参与方、关键路径、异常路径、未覆盖范围、一致性检查。若复杂项目不画图，写明原因。

#### 6. State Contract

有状态对象必须说明 enum 值、合法迁移、非法迁移错误码和兼容性影响。复杂状态流建议补充 PlantUML state diagram。

#### 7. Idempotency / Retry Contract

写接口、message consumer、cron / batch、CLI 副作用命令需说明幂等键来源、重复请求行为、超时后是否可重试和冲突响应。

```markdown
| Contract | 幂等要求 | 幂等键来源 | 重复请求行为 | 超时后是否可重试 | 冲突响应 |
|---|---|---|---|---|---|
```

#### 8. Cross-Document Traceability Matrix

```markdown
| Domain ID | AC ID | Reality Relation | Contract | Consumer / Entrypoint | Shared Model / Error Code | Test Focus |
|---|---|---|---|---|---|---|
```

#### 8.1 Test Focus / Verification Scenario

Test Focus 应能直接输入后续 delivery plan 和 verification 阶段，按 contract operation / event / task / error code 写清场景与预期结果。

```markdown
| Domain ID | AC ID | Design Surface | Scenario | Expected Result | Evidence |
|---|---|---|---|---|---|
```

#### 9. 数据模型
- 共享的 TypeScript interface / JSON Schema
- 模型之间的引用关系
- 枚举值定义

#### 10. 错误码表
- 按 HTTP Status 分组
- 每个错误码含：code + message + HTTP status + 触发条件 + 用户可恢复 + 是否可重试 + 前端处理建议 + 后端日志级别

#### 11. Compatibility / Versioning 与接口变更日志
- 格式：`[日期] [版本] [接口] [变更类型] [描述]`
- 变更类型：新增 / 修改 / 废弃 / 删除
- 新增 response 字段默认 optional，或说明 consumer 兼容性
- 新增 request 必填字段通常是 breaking change
- enum 新增值需说明前端默认处理，避免 switch exhaustiveness 破坏
- message topic 不兼容变更必须发布 `v2` topic，不原地破坏 schema
- SDK public API deprecation 周期必须明确

### stage_status 流转规则

- `draft`：接口设计进行中，存在未覆盖的业务域或未定义的错误码
- `ready`：所有业务域接口已覆盖，错误码完整，数据模型一致，可进入前后端设计

### evidence_complete 判定标准

- 每个 Domain ID 至少有一个对应接口
- 每个接口至少关联一个 AC ID
- 每个接口至少关联一个前端页面
- 已处理 `tech-research.md` 中相关 Existing Surface Inventory，且兼容性结论明确
- 错误码表覆盖所有非 200 场景
- 数据模型覆盖所有接口的请求/响应结构

## Anti-Rationalizations

1. **"接口设计太早了，做的时候再定"** —— Contract-First 的核心就是先定契约再实现。没有契约的并行开发等于各写各的，联调时才发现不兼容。
2. **"错误码太多了，先只定义 200 和 500"** —— 前端需要根据不同错误码做差异化处理（提示用户重试 vs 跳转登录 vs 显示具体字段错误）。只有 200/500 等于前端无法优雅处理异常。
3. **"数据模型前后端各定义一份就行"** —— 各定义一份 = 两份不同步。共享模型是契约的核心，类型不一致是联调 bug 的第一大来源。
4. **"这个接口很简单不用写文档"** —— "简单"的接口往往隐藏着分页、权限、并发、缓存等未考虑的问题。写下来才能发现遗漏。
5. **"GraphQL 不需要接口文档，Schema 就是文档"** —— Schema 定义了"能查什么"，但没定义"应该怎么查"。Query 粒度、N+1 防护、权限粒度都需要额外约定。

## Red Flags

- **接口无法追溯到 AC ID** → 可能是多余接口或需求遗漏
- **同一数据在不同接口中结构不一致** → 数据模型未统一
- **错误码表为空或只有通用错误** → 异常路径未设计
- **接口路径不符合 REST 规范**（如 GET /deleteUser）→ 设计不规范
- **请求参数无校验规则** → 后端无法做输入验证
- **响应结构缺少分页信息**（列表接口）→ 前端无法实现分页
- **无版本策略** → 未来接口变更将导致破坏性更新

## Verification

完成 api-contract.md 后，执行以下检查：

```
□ 每个 Domain ID 是否至少有一个对应接口？
□ 每个接口是否关联了 AC ID？
□ 每个接口是否标注了调用页面？
□ 是否已消费 tech-research.md 的 Requirement-to-Reality Mapping？
□ 已有 API / route / message / cron / cli / sdk surface 是否有 compatibility / deprecation / breaking change 判断？
□ 请求参数是否包含类型和校验规则？
□ 响应结构是否区分成功和失败？
□ 错误码表是否覆盖所有异常场景？
□ 数据模型是否前后端共享且一致？
□ 分页/排序/过滤约定是否完整？
□ 认证方式是否明确？
□ 版本策略是否定义？
□ 接口命名是否符合选定的 API 风格规范？
□ frontmatter 字段是否正确填写？
□ 复杂场景是否已补充 PlantUML 图示，或说明不画图原因？
□ 图中的 contract / event / task / command / state 是否存在于本文正文表格？
□ 是否存在 Consumer / Provider Matrix，或说明本期不适用原因？
□ 每个关键 contract 是否能追溯到 Domain ID、AC ID、consumer / entrypoint 和 Test Focus？
□ 状态 enum 是否有合法状态迁移说明和非法迁移错误？
□ 写接口、message、cron、CLI 副作用命令是否说明幂等和重试策略？
□ 是否说明 breaking / non-breaking / additive 变更分类与兼容性影响？
```

全部通过后，将 `stage_status` 设为 `ready`，`evidence_complete` 设为 `true`。
