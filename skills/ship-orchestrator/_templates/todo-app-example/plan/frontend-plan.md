---
stage: ship-delivery-plan
artifact_role: frontend-plan
stage_status: ready
updated_at: "2026-05-22T15:00:00+08:00"
evidence_complete: true
task_count: 14
---

# TODO Web App — 前端实施计划

## 1. 实施概览

- 总任务数: 14
- 预估总工时: 约 16 小时
- 关键里程碑:
  - M1: 接口对齐完成（Mock + Types + API Client）
  - M2: 核心组件完成（atoms + molecules）
  - M3: 列表页面可运行
  - M4: 全量 CRUD + 集成测试通过

## 2. 任务清单

### 阶段一: 基础设施 + 接口对齐（FE-I / FE-C）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| FE-I-001 | 项目初始化 | `npm create vite@latest`，配置 TS / Tailwind / 路由 | - | - | `npm run dev` 启动空白页正常 | 1h | TODO |
| FE-I-002 | 安装核心依赖 | TanStack Query / Zustand / axios / react-hook-form / zod / Headless UI / lucide-react | FE-I-001 | FE-I-001 | package.json 含全部依赖，`npm i` 通过 | 0.5h | TODO |
| FE-C-001 | 共享类型定义 | 从 api-contract.md §4 复制 TS 类型到 `src/types/todo.ts` | AC-001~010 | FE-I-002 | tsc 编译通过 | 0.5h | TODO |
| FE-C-002 | API Client 封装 | axios 实例 + `api/todos.ts` 5 个方法（list/getById/create/update/delete） | AC-001~007 | FE-C-001 | 每个方法返回类型正确 | 1h | TODO |
| FE-C-003 | MSW Mock 服务 | 配置 MSW，按 api-contract.md 实现 5 个 mock handler | AC-001~007 | FE-C-002 | mock 数据可通过 API client 返回 | 1.5h | TODO |

### 阶段二: 共享组件（FE-S）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| FE-S-001 | atoms 组件 | Button / Input / Textarea / Checkbox / Badge / Select | - | FE-I-002 | 组件测试全部通过 | 2h | TODO |
| FE-S-002 | molecules 组件 | FormField / EmptyState / ConfirmDialog / LoadingSpinner | - | FE-S-001 | 组件测试全部通过 | 1.5h | TODO |
| FE-S-003 | filterStore | Zustand store，含 completed/sortBy/order 字段 | AC-006, AC-007 | FE-I-002 | 单元测试通过 | 0.5h | TODO |
| FE-S-004 | useTodos hooks | TanStack Query 封装：useTodoList / useCreateTodo / useUpdateTodo / useDeleteTodo | AC-001~007 | FE-C-002 | hook 测试通过（用 MSW） | 1.5h | TODO |

### 阶段三: 页面（FE-P）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| FE-P-001 | 路由配置 | React Router 配置 / → /todos 重定向 + NotFound | - | FE-I-002 | 路由跳转正确 | 0.5h | TODO |
| FE-P-002 | TodoFilters 组件 | 状态筛选 + 排序控件，连 filterStore | AC-006, AC-007 | FE-S-001, FE-S-003 | 切换筛选触发列表更新 | 1h | TODO |
| FE-P-003 | TodoItem 组件 | 单条 TODO 卡片，含 checkbox/标题/优先级/操作 | AC-002, AC-003 | FE-S-001 | 组件测试通过，点击 checkbox 触发 mutation | 1h | TODO |
| FE-P-004 | TodoForm 组件 | 创建/编辑表单，含 react-hook-form + zod 校验 | AC-001, AC-004, AC-008 | FE-S-001, FE-S-002 | 校验逻辑测试通过 | 1.5h | TODO |
| FE-P-005 | TodoListPage 装配 | 集成 filters + list + form 弹窗 + delete 确认 | AC-001~009 | FE-P-002, FE-P-003, FE-P-004, FE-S-004 | 页面可运行所有 CRUD 流程 | 2h | TODO |

### 阶段四: 集成（FE-INT）

| ID | 标题 | 描述 | 关联 | 依赖 | 完成判定 | 工时 | 状态 |
|----|------|------|------|------|---------|------|------|
| FE-INT-001 | E2E 测试 | Playwright 覆盖每条 AC 至少 1 个场景 | AC-001~010 | FE-P-005 | 全部 AC 场景 PASS | 2h | TODO |

## 3. 依赖关系图

```
FE-I-001 → FE-I-002 ─┬─ FE-C-001 → FE-C-002 → FE-C-003
                     ├─ FE-S-001 ─┬─ FE-S-002
                     │            ├─ FE-P-002 ┐
                     │            ├─ FE-P-003 ├──┐
                     │            └─ FE-P-004 ┘  │
                     ├─ FE-S-003 ───────────────┤
                     ├─ FE-P-001 ───────────────┤
                     └─ FE-S-004 (依赖 FE-C-002)─┴─→ FE-P-005 → FE-INT-001
```

## 4. 执行顺序建议

1. FE-I-001 → FE-I-002 → FE-C-001 → FE-C-002 → FE-C-003（接口对齐先行）
2. 与后端约定 mock 一致后，前端可独立推进
3. FE-S-001 → FE-S-002 / FE-S-003 / FE-S-004（共享组件并行）
4. FE-P-001 → FE-P-002 / FE-P-003 / FE-P-004（页面组件并行）
5. FE-P-005（装配）→ FE-INT-001（E2E）
