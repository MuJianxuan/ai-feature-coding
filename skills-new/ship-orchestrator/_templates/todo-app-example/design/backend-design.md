---
stage: ship-backend-design
stage_status: ready
updated_at: "2026-05-22T13:30:00+08:00"
evidence_complete: true
---

# TODO Web App — 后端技术方案

## 1. 后端架构概览

- **框架**: Express 4
- **语言**: TypeScript 5
- **ORM**: Prisma 5
- **数据库**: SQLite（dev/test）
- **校验**: zod
- **日志**: pino
- **架构模式**: 分层架构（Controller / Service / Repository）

## 2. 目录结构

```
src/
├── server.ts                # 入口，启动 Express
├── app.ts                   # 应用配置（中间件、路由挂载）
├── config/
│   └── env.ts               # 环境变量校验（zod）
├── middleware/
│   ├── errorHandler.ts      # 错误处理
│   ├── requestLogger.ts     # 日志
│   └── validator.ts         # zod 校验中间件
├── modules/
│   └── todo/
│       ├── todo.routes.ts   # 路由定义
│       ├── todo.controller.ts
│       ├── todo.service.ts
│       ├── todo.repository.ts
│       └── todo.schemas.ts  # zod schemas
├── shared/
│   ├── types/               # 与前端共享类型（同步 api-contract.md）
│   ├── errors/              # 自定义错误类
│   └── utils/
└── prisma/
    ├── schema.prisma
    └── migrations/
```

## 3. 业务域划分

| Domain ID | Module | 描述 | 数据库表 |
|-----------|--------|------|---------|
| TODO | modules/todo | TODO 增删改查、状态管理 | todos |

## 4. 数据模型（Prisma Schema）

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model Todo {
  id          String   @id @default(uuid())
  title       String                              // 1-200 字符（zod 校验）
  description String?
  completed   Boolean  @default(false)
  priority    String   @default("medium")         // high | medium | low (zod 枚举校验)
  dueDate     DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([completed])
  @@index([priority])
  @@index([dueDate])
  @@map("todos")
}
```

> 注: SQLite 不支持原生 enum，priority 用 string + zod 校验保证。

## 5. 服务层设计

### TodoService 方法签名

```typescript
class TodoService {
  list(query: ListTodoQuery): Promise<PaginatedResult<Todo>>;
  getById(id: string): Promise<Todo>;          // 不存在抛 NotFoundError
  create(input: CreateTodoInput): Promise<Todo>;
  update(id: string, input: UpdateTodoInput): Promise<Todo>;
  delete(id: string): Promise<void>;
}
```

### TodoRepository 方法签名

```typescript
class TodoRepository {
  findMany(args: Prisma.TodoFindManyArgs): Promise<Todo[]>;
  count(where?: Prisma.TodoWhereInput): Promise<number>;
  findById(id: string): Promise<Todo | null>;
  create(data: Prisma.TodoCreateInput): Promise<Todo>;
  update(id: string, data: Prisma.TodoUpdateInput): Promise<Todo>;
  delete(id: string): Promise<void>;
}
```

## 6. 接口实现映射

| 接口 (api-contract.md) | Controller | Service | Repository |
|------------------------|-----------|---------|------------|
| GET /todos | TodoController.list | TodoService.list | findMany + count |
| POST /todos | TodoController.create | TodoService.create | create |
| GET /todos/:id | TodoController.getById | TodoService.getById | findById |
| PATCH /todos/:id | TodoController.update | TodoService.update | findById + update |
| DELETE /todos/:id | TodoController.delete | TodoService.delete | findById + delete |

## 7. 中间件设计

| 中间件 | 顺序 | 职责 |
|--------|------|------|
| cors | 1 | 允许前端跨域请求 |
| express.json | 2 | JSON body 解析 |
| requestLogger | 3 | 请求日志（method, url, duration） |
| validator (zod) | 4 | 路由级输入校验 |
| errorHandler | last | 统一错误响应 |

### 错误处理映射

| 错误类 | HTTP Status | code |
|--------|-------------|------|
| ValidationError (zod) | 400 | VALIDATION_ERROR |
| NotFoundError | 404 | NOT_FOUND |
| 其他 | 500 | INTERNAL_ERROR（生产环境隐藏 stack） |

## 8. 数据库迁移策略

```bash
# 开发环境
npx prisma migrate dev --name <change_name>

# 生产环境
npx prisma migrate deploy
```

- 每次 schema 变更产生独立迁移文件
- 提交到 git，CI/CD 自动应用
- 回滚: 创建反向迁移，不直接 drop

## 9. 后端非功能方案

### 性能

- Prisma 单条查询 < 50ms（SQLite 本地文件）
- 列表查询用 `select` 限制字段（本期所有字段都要返回，跳过此优化）
- 索引覆盖 `completed` / `priority` / `dueDate` 三个常用过滤/排序字段

### 安全

- zod 校验所有输入（防注入）
- Prisma 参数化查询（防 SQL 注入）
- CORS 限制 origin 为前端域名
- 不返回敏感字段（本项目无）

### 日志

- pino 结构化日志，level: info（生产）/ debug（开发）
- 请求日志: method, url, statusCode, duration
- 错误日志: 完整 stack trace

### 测试策略

- 单元测试: Service 层（mock Repository）
- 集成测试: Controller + Service + Repository（用真实 SQLite 内存数据库）
- 契约测试: 验证响应结构与 api-contract.md 一致（用 zod schema 反向校验）
