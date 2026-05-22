---
stage: ship-contract
stage_status: ready
updated_at: "2026-05-22T12:00:00+08:00"
evidence_complete: true
---

# TODO Web App — 接口规约

## 1. 接口规约概览

- **API 风格**: RESTful
- **基础 URL**: `http://localhost:3001/api/v1`
- **认证方式**: 无（本期不做认证）
- **版本策略**: URL path 版本号（`/v1`）
- **数据格式**: JSON
- **字符编码**: UTF-8

## 2. 通用约定

### 请求头

```
Content-Type: application/json
Accept: application/json
```

### 响应格式（成功）

```json
{
  "data": <T>,
  "meta": { "page": 1, "pageSize": 20, "total": 100 }  // 列表接口
}
```

### 响应格式（失败）

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "标题长度必须在 1-200 字符之间",
    "details": { "field": "title" }
  }
}
```

### 分页约定

- Query 参数: `page` (默认 1, 最小 1) + `pageSize` (默认 20, 最大 100)
- 响应 meta 包含: `page`, `pageSize`, `total`

### 排序约定

- Query 参数: `sortBy` + `order`
- 示例: `?sortBy=priority&order=desc`

### 过滤约定

- Query 参数: `filter[<field>]=<value>`
- 示例: `?filter[completed]=false`

## 3. 接口清单

### TODO 业务域

#### 3.1 GET /todos — 查询 TODO 列表

- **AC**: AC-002, AC-006, AC-007
- **关联页面**: TodoListPage

**Query 参数:**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 20 | 每页数量 |
| filter[completed] | boolean | 否 | - | 完成状态筛选 |
| sortBy | string | 否 | createdAt | 排序字段：createdAt / priority / dueDate |
| order | string | 否 | desc | 排序方向：asc / desc |

**响应:**

```json
{
  "data": [
    {
      "id": "uuid",
      "title": "买菜",
      "description": "番茄、鸡蛋",
      "completed": false,
      "priority": "medium",
      "dueDate": "2026-05-25T00:00:00.000Z",
      "createdAt": "2026-05-22T10:00:00.000Z",
      "updatedAt": "2026-05-22T10:00:00.000Z"
    }
  ],
  "meta": { "page": 1, "pageSize": 20, "total": 1 }
}
```

#### 3.2 POST /todos — 创建 TODO

- **AC**: AC-001, AC-008
- **关联页面**: TodoListPage（弹窗表单）

**请求体:**

```json
{
  "title": "string, 1-200 chars, required",
  "description": "string, optional",
  "priority": "high | medium | low, default: medium",
  "dueDate": "ISO8601 datetime, optional"
}
```

**响应**: 201 Created + Todo 对象

#### 3.3 GET /todos/:id — 查询单条 TODO

- **AC**: AC-004（编辑前的详情查询）
- **关联页面**: TodoDetailPage / TodoListPage（编辑弹窗）

**响应**: 200 OK + Todo 对象 / 404 Not Found

#### 3.4 PATCH /todos/:id — 更新 TODO

- **AC**: AC-003, AC-004
- **关联页面**: TodoListPage（点击复选框 / 编辑弹窗）

**请求体**（所有字段可选）:

```json
{
  "title": "string, 1-200 chars",
  "description": "string",
  "completed": "boolean",
  "priority": "high | medium | low",
  "dueDate": "ISO8601 datetime | null"
}
```

**响应**: 200 OK + 更新后的 Todo 对象

#### 3.5 DELETE /todos/:id — 删除 TODO

- **AC**: AC-005
- **关联页面**: TodoListPage（确认弹窗）

**响应**: 204 No Content / 404 Not Found

## 4. 数据模型（共享 TypeScript 类型）

```typescript
// shared/types/todo.ts (前后端共享)

export type Priority = 'high' | 'medium' | 'low';

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  priority: Priority;
  dueDate: string | null;  // ISO8601
  createdAt: string;
  updatedAt: string;
}

export interface CreateTodoInput {
  title: string;
  description?: string;
  priority?: Priority;
  dueDate?: string;
}

export interface UpdateTodoInput {
  title?: string;
  description?: string;
  completed?: boolean;
  priority?: Priority;
  dueDate?: string | null;
}

export interface ListTodoQuery {
  page?: number;
  pageSize?: number;
  filter?: { completed?: boolean };
  sortBy?: 'createdAt' | 'priority' | 'dueDate';
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: { page: number; pageSize: number; total: number };
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
```

## 5. 错误码表

| code | HTTP Status | message 示例 | 处理建议 |
|------|-------------|------------|---------|
| VALIDATION_ERROR | 400 | 字段校验失败 | 提示用户修正输入 |
| NOT_FOUND | 404 | TODO 不存在 | 列表刷新 |
| INVALID_QUERY | 400 | 查询参数非法 | 检查 query string |
| INTERNAL_ERROR | 500 | 服务器错误 | 提示稍后重试 |

## 6. 接口变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-05-22 | 初始版本 |
