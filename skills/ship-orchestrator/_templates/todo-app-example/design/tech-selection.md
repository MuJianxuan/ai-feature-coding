---
stage: ship-tech-discovery
artifact_role: selection
stage_status: ready
updated_at: "2026-05-22T11:00:00+08:00"
evidence_complete: true
---

# TODO Web App — 技术选型

## 1. 选型摘要

采用 React + Vite + TypeScript 前端 + Node + Express + Prisma + SQLite 后端的全 TypeScript 技术栈，优先考虑开发效率、类型安全和零配置启动。

## 2. 技术栈决策表

| 层级 | 选型 | 版本 | 理由 | 备选方案 |
|------|------|------|------|---------|
| 前端框架 | React | 18.x | 生态最大、社区资料丰富、AI 辅助友好 | Vue 3（同样优秀但 React 生态更大） |
| 构建工具 | Vite | 5.x | 零配置、HMR 极快、TS 原生支持 | webpack（配置复杂） |
| 类型系统 | TypeScript | 5.x | 前后端共享类型、编译时错误检查 | JavaScript（缺乏类型安全） |
| CSS 方案 | TailwindCSS | 3.x | 原子化、响应式内置、无需写 CSS 文件 | CSS Modules（需要更多文件） |
| 后端框架 | Express | 4.x | 最成熟的 Node 框架、中间件生态丰富 | Fastify（更快但生态略小） |
| ORM | Prisma | 5.x | 类型化 ORM、自动迁移、Schema 即文档 | TypeORM（API 不够直观） |
| 数据库 | SQLite | 3.x | 零部署、文件级、开发友好 | PostgreSQL（本项目不需要） |
| 测试-前端 | Vitest + Testing Library | latest | 与 Vite 同生态、API 兼容 Jest | Jest（需额外配置） |
| 测试-E2E | Playwright | latest | 跨浏览器、稳定、API 现代 | Cypress（免费版限制多） |
| 测试-后端 | Vitest + Supertest | latest | 统一测试框架、HTTP 断言方便 | Jest + Supertest |

## 3. ADR 列表

### ADR-001: 选择 SQLite 而非 PostgreSQL

- **状态**: accepted
- **上下文**: 单用户 TODO 应用，数据量 < 10000，无并发写入压力
- **决策**: 使用 SQLite
- **理由**: 零部署成本、Prisma 完整支持、文件级备份简单
- **后果**: 
  - 正面: 开发环境零配置，CI 无需数据库服务
  - 负面: 不支持并发写入（本项目不需要）
  - 风险: 如果未来需要多用户，需迁移到 PostgreSQL（Prisma 切换成本低）

### ADR-002: 前后端分离而非全栈框架

- **状态**: accepted
- **上下文**: 需要演示 Contract-First 开发模式
- **决策**: 前端 Vite SPA + 后端 Express API，通过 HTTP 通信
- **理由**: 清晰的前后端边界、独立部署、接口契约驱动
- **后果**:
  - 正面: 前后端可并行开发、接口文档化
  - 负面: 需要处理 CORS、多一层网络开销
  - 风险: 无（标准架构）

### ADR-003: 选择 TailwindCSS 而非 CSS-in-JS

- **状态**: accepted
- **上下文**: 需要快速实现响应式 UI，AI 辅助编码场景
- **决策**: 使用 TailwindCSS
- **理由**: 原子化类名 AI 生成友好、响应式内置、无运行时开销
- **后果**:
  - 正面: 开发速度快、bundle 小、无样式冲突
  - 负面: HTML 类名较长（可接受）

## 4. 架构模式

**模式**: 前后端分离 + 分层架构

```
前端 (SPA)                    后端 (REST API)
┌─────────────┐              ┌─────────────────┐
│ Pages       │              │ Routes/Controllers│
│ Components  │  ← HTTP →   │ Services         │
│ Hooks/Store │              │ Repositories     │
│ API Client  │              │ Prisma (ORM)     │
└─────────────┘              └─────────────────┘
                                    │
                              ┌─────┴─────┐
                              │  SQLite    │
                              └───────────┘
```

## 5. 项目初始化方案

```bash
# 前端
npm create vite@latest todo-frontend -- --template react-ts
cd todo-frontend && npm install tailwindcss @tailwindcss/vite

# 后端
mkdir todo-backend && cd todo-backend
npm init -y
npm install express prisma @prisma/client cors zod
npm install -D typescript @types/express @types/cors vitest supertest @types/supertest tsx
npx prisma init --datasource-provider sqlite
```
