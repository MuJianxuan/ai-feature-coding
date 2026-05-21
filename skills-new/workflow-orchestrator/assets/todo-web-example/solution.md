---
feature_stage: technical-solution
stage_status: ready
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "采用 greenfield 路径，用官方脚手架初始化前后端项目。"
---

# Solution

## 1. 方案摘要

- 前端使用 React + Vite 构建单页 TODO UI；后端使用 Node.js + Express 提供 REST API；数据使用 SQLite 或内存仓储都可，但样例推荐 SQLite 便于验证存储路径

## 2. 技术选型

| 领域 | 候选 | 结论 | 依据 |
| --- | --- | --- | --- |
| frontend scaffold | Vite / CRA | Vite | 官方脚手架轻量、现代、适合样例 |
| backend scaffold | Express / Fastify | Express | 学习成本低，CRUD 样例足够 |
| storage | SQLite / in-memory | SQLite | 更接近真实交付，便于验证增删改查 |

## 3. 前端方案

- 页面结构：单页 `TodoPage`
- 状态管理：组件状态 + 请求层
- 表单 / 交互：创建输入框、编辑模式、checkbox、delete action、filter tabs
- 原型约束实现：空态、错误态、loading state

## 4. 后端方案

- 业务模块：todo service、todo repository、todo routes
- API 风格：REST
- 数据模型：`todos(id, title, completed, created_at, updated_at)`
- 权限与校验：样例不含认证，但保留标题非空校验和 404 错误返回

## 5. 页面到接口映射

| 页面 / 组件 | 用户动作 | 调用接口 | 请求 / 响应摘要 | 异常处理 |
| --- | --- | --- | --- | --- |
| TodoPage | 首次加载 | `GET /api/todos?filter=` | 返回 todo 列表 | 展示错误提示与重试 |
| CreateForm | 新建 todo | `POST /api/todos` | 提交 title，返回新 todo | 标题为空显示校验 |
| TodoItem | 编辑标题 | `PATCH /api/todos/:id` | 更新 title | 404 / 400 提示 |
| TodoItem | 切换完成 | `PATCH /api/todos/:id` | 更新 completed | 404 提示 |
| TodoItem | 删除 | `DELETE /api/todos/:id` | 删除成功返回 204 | 404 提示 |

## 6. 数据模型与存储

| Entity | 字段 | 约束 | 索引 / 唯一性 | 备注 |
| --- | --- | --- | --- | --- |
| Todo | id, title, completed, created_at, updated_at | `title != ""` | `id` primary key | `completed` 默认 false |

## 7. 调用链 / 数据流

- UI action -> frontend API client -> backend route -> service -> repository -> SQLite -> response -> UI refresh

## 8. 风险、降级与回滚

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| SQLite 初始化失败 | 应用无法启动 | 启动时执行 schema check | 回退到内存仓储 |
| 筛选逻辑前后端不一致 | 列表展示错误 | API test + UI test 双校验 | 先禁用服务端筛选，仅用前端筛选 |

## 9. 验证策略

- 前端测试：创建、编辑、切换、删除、筛选
- 后端测试：CRUD 与筛选 API
- 手工 smoke：完整用户路径

