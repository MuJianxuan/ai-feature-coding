---
stage: ship-tech-discovery
artifact_role: research
stage_status: ready
updated_at: "2026-05-22T10:30:00+08:00"
evidence_complete: true
---

# TODO Web App — 技术调研

## 1. 调研范围

| 关注点 | 优先级 | 关键问题 |
|--------|--------|----------|
| 前端框架 | P0 | 是否适合快速交付单页应用？ |
| 后端框架 | P0 | 是否能低成本支撑 REST API？ |
| ORM | P0 | 是否具备类型安全和迁移能力？ |
| 数据库 | P1 | 是否需要独立数据库服务？ |
| 测试栈 | P1 | 是否便于前后端统一验证？ |

## 2. 技术调研结果

### React + Vite
- 当前稳定方案：React 18 + Vite 5
- 关键特性：成熟生态、快速 HMR、TypeScript 友好
- 适用场景：中小型 SPA、组件化前端、快速原型到生产
- 已知限制：需要自行组合路由/数据层/状态管理
> 来源：官方文档与 release notes | 获取时间：2026-05-22

### Express
- 当前稳定方案：Express 4
- 关键特性：中间件生态成熟、上手成本低、REST API 模式清晰
- 适用场景：轻量 API 服务、教学/示例项目、中小型后端
- 已知限制：默认无强约束，需要自己组合校验与错误处理
> 来源：官方文档与 npm registry | 获取时间：2026-05-22

### Prisma
- 当前稳定方案：Prisma 5
- 关键特性：类型化 ORM、schema 驱动、迁移工具完备
- 适用场景：TypeScript 全栈项目、需要可读 schema 与迁移历史
- 已知限制：SQLite 下原生 enum 支持有限
> 来源：官方文档与 GitHub releases | 获取时间：2026-05-22

## 3. 候选对比摘要

| 领域 | 候选 A | 候选 B | 结论 |
|------|--------|--------|------|
| 前端框架 | React | Vue | React 生态与 AI 辅助资料更丰富 |
| 后端框架 | Express | Fastify | Express 更成熟、上手更平滑 |
| ORM | Prisma | TypeORM | Prisma 类型体验更强 |
| 数据库 | SQLite | PostgreSQL | TODO 场景优先开发效率，选 SQLite |

## 4. 匹配度结论

- 单页 TODO 应用不需要复杂 SSR 或多节点部署
- 单用户、小数据量、低并发适合 SQLite
- 前后端分离更符合 Contract-First 演示目标
- 全 TypeScript 栈利于共享类型与自动化校验

## 5. 信息来源清单

- 官方文档 / release notes / registry 页面
- 获取时间统一为 `2026-05-22`
