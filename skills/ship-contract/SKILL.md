---
name: ship-contract
description: "ShipKit stage. Designs API contracts as the shared agreement between frontend and backend. Use after ship-tech-discovery completes."
---

# 接口规约设计 (API Contract Design)

## Overview

接口规约设计是 Contract-First 开发模式的核心阶段，负责基于 requirements.md 的业务域和 tech-selection.md 的技术栈，设计端到端的接口规约。

核心目标：
- 产出前后端并行开发的"契约"，消除前后端联调时的认知差异
- 定义完整的请求/响应结构、错误码体系和数据模型
- 确保每个接口可追溯到具体的验收标准（AC ID）和前端页面
- 建立统一的 API 风格规范，保证接口一致性

产出物：`api-contract.md`

## When to Use

- `ship-tech-discovery` 已完成，且 `tech-selection.md.stage_status = ready`
- 项目采用前后端分离架构，需要明确接口契约
- 多团队并行开发，需要接口作为协作基准
- 需要生成 Mock 数据供前端独立开发

## When NOT to Use

- `ship-tech-discovery` 尚未完成 —— 技术栈未定无法确定 API 风格
- 纯前端项目（无后端交互）—— 无需接口规约
- 使用 BFF 且前后端同一人开发 —— 可简化为内部接口文档
- 纯后端批处理/定时任务 —— 使用后端设计阶段直接定义

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
1. 确定 API 风格与基础约定
   verify: 风格选择有 tech-selection.md 依据
2. 定义通用约定（分页/排序/过滤/错误码体系）
   verify: 约定覆盖所有常见场景
3. 按业务域逐一设计接口
   verify: 每个接口关联 AC ID + 前端页面
4. 提取共享数据模型
   verify: 模型覆盖所有接口的请求/响应结构
5. 完善错误码表
   verify: 错误码覆盖所有异常路径
6. 自检与交叉验证
   verify: Verification Checklist 全部通过
```

### 步骤详解

**Step 1: 确定 API 风格**

基于 tech-selection.md 中的技术栈选择：
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
- 为每个操作设计接口（方法 + 路径 + 参数 + 响应）
- 标注关联的 AC ID 和调用页面

**Step 4-6: 数据模型与错误码**

- 从接口中提取重复出现的数据结构，抽象为共享模型
- 为每种异常场景分配错误码，确保前端可据此做差异化处理

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
updated_at: ""
evidence_complete: false
---
```

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
- **关联页面**：CreateResourcePage
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

#### 4. 数据模型
- 共享的 TypeScript interface / JSON Schema
- 模型之间的引用关系
- 枚举值定义

#### 5. 错误码表
- 按 HTTP Status 分组
- 每个错误码含：code + message + HTTP status + 触发条件 + 前端处理建议

#### 6. 接口变更日志
- 格式：`[日期] [版本] [接口] [变更类型] [描述]`
- 变更类型：新增 / 修改 / 废弃 / 删除

### stage_status 流转规则

- `draft`：接口设计进行中，存在未覆盖的业务域或未定义的错误码
- `ready`：所有业务域接口已覆盖，错误码完整，数据模型一致，可进入前后端设计

### evidence_complete 判定标准

- 每个 Domain ID 至少有一个对应接口
- 每个接口至少关联一个 AC ID
- 每个接口至少关联一个前端页面
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
□ 请求参数是否包含类型和校验规则？
□ 响应结构是否区分成功和失败？
□ 错误码表是否覆盖所有异常场景？
□ 数据模型是否前后端共享且一致？
□ 分页/排序/过滤约定是否完整？
□ 认证方式是否明确？
□ 版本策略是否定义？
□ 接口命名是否符合选定的 API 风格规范？
□ frontmatter 字段是否正确填写？
```

全部通过后，将 `stage_status` 设为 `ready`，`evidence_complete` 设为 `true`。
