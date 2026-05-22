---
stage: ship-backend-plan
stage_status: ready
updated_at: "2026-05-22T15:00:00+08:00"
evidence_complete: true
task_count: 12
---

# TODO Web App — 后端实施计划

## 1. 实施概览

- 总任务数: 12
- 预估总工时: 约 12 小时
- 关键里程碑:
  - M1: 项目骨架 + 数据库就绪
  - M2: TODO 业务域 Repository + Service 完成
  - M3: 全部 5 个接口可调用
  - M4: 测试覆盖率 ≥ 80%，契约测试通过

## 2. 任务清单

### 阶段一: 基础设施（BE-I）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| BE-I-001 | 项目脚手架 | npm init + TS + Express + tsx + 目录结构 | - | - | `npm run dev` 启动空 server 监听 3001 | 0.5h | TODO |
| BE-I-002 | 安装核心依赖 | express / cors / zod / pino / prisma / @prisma/client + 测试依赖 | - | BE-I-001 | package.json 含全部依赖 | 0.3h | TODO |
| BE-I-003 | Prisma 初始化 + Schema | `npx prisma init` 用 sqlite，定义 Todo 模型 + 索引 | - | BE-I-002 | `npx prisma migrate dev` 生成首个迁移 | 1h | TODO |
| BE-I-004 | 中间件骨架 | cors / express.json / requestLogger / errorHandler | - | BE-I-002 | 简单 health check 接口可用 | 1h | TODO |
| BE-I-005 | 路由骨架 + 错误类型 | Router 注册到 /api/v1，定义 NotFoundError / ValidationError | - | BE-I-004 | 错误中间件能统一返回错误格式 | 0.5h | TODO |

### 阶段二: TODO 业务域（BE-TODO）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| BE-TODO-001 | TodoRepository | 5 个方法：findMany / count / findById / create / update / delete | TODO Domain | BE-I-003 | 单元测试覆盖（用真实 sqlite 内存库） | 1.5h | TODO |
| BE-TODO-002 | TodoService | 5 个方法：list / getById / create / update / delete + 业务校验 | TODO Domain | BE-TODO-001 | 单元测试覆盖率 ≥ 80%（mock Repository） | 1.5h | TODO |
| BE-TODO-003 | zod schemas | createTodoSchema / updateTodoSchema / listTodoQuerySchema | AC-008 | BE-I-002 | schema 单元测试覆盖边界条件 | 0.5h | TODO |
| BE-TODO-004 | Validator 中间件 | 通用 zod 校验中间件 | - | BE-TODO-003 | 错误时返回 400 + VALIDATION_ERROR | 0.5h | TODO |
| BE-TODO-005 | TodoController + Routes | 5 个 endpoint，挂接 service + validator | AC-001~009 | BE-TODO-002, BE-TODO-004, BE-I-005 | 5 个接口手工 curl 全部正确 | 1.5h | TODO |

### 阶段三: 测试与契约（BE-TEST）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| BE-TEST-001 | 集成测试 | Supertest 覆盖 5 个 endpoint 的 happy + error path | AC-001~009 | BE-TODO-005 | 全部测试 PASS，覆盖率达标 | 2h | TODO |
| BE-TEST-002 | 契约测试 | 用 zod schema 反向校验响应，验证错误码完整 | AC-001~009 | BE-TEST-001 | 5 个接口 100% 契约一致 | 1h | TODO |

## 3. 依赖关系图

```
BE-I-001 → BE-I-002 ─┬─ BE-I-003 → BE-TODO-001 → BE-TODO-002 ┐
                     ├─ BE-I-004 → BE-I-005 ─────────────────┤
                     └─ BE-TODO-003 → BE-TODO-004 ───────────┤
                                                              ↓
                                                          BE-TODO-005 → BE-TEST-001 → BE-TEST-002
```

## 4. 执行顺序建议

1. BE-I 系列基础设施全部完成（M1）
2. BE-TODO 业务域：repository → service → schemas/validator → controller（M2/M3）
3. BE-TEST 测试与契约（M4）
4. 与前端 contract task 同步：BE-I-005 完成 + 路由骨架就位后，前端 mock 即可对齐真实接口路径

## 5. 与前端的接口对齐 checkpoint

- **C1（BE-I-005 完成时）**: 通知前端基础 URL 和错误格式已确定，可调整 API client baseURL
- **C2（BE-TODO-005 完成时）**: 通知前端可关闭 MSW，连真实接口
- **C3（BE-TEST-002 完成时）**: 契约一致性确认，进入 `ship-verify` 阶段联调
