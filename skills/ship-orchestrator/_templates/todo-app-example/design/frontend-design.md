---
stage: ship-frontend-design
stage_status: ready
updated_at: "2026-05-22T13:00:00+08:00"
evidence_complete: true
---

# TODO Web App — 前端技术方案

## 1. 前端架构概览

- **框架**: React 18
- **构建工具**: Vite 5
- **路由**: React Router 6
- **状态管理**: Zustand（轻量、无 Provider 嵌套）
- **数据请求**: TanStack Query (React Query) v5
- **HTTP 客户端**: axios
- **UI 库**: TailwindCSS 3 + Headless UI（弹窗/下拉等无障碍组件）
- **表单**: react-hook-form + zod
- **图标**: lucide-react

## 2. 目录结构

```
src/
├── main.tsx
├── App.tsx
├── routes/
│   └── router.tsx
├── pages/
│   ├── TodoListPage.tsx
│   └── NotFoundPage.tsx
├── components/
│   ├── atoms/        # Button, Input, Checkbox, Badge
│   ├── molecules/    # FormField, EmptyState, ConfirmDialog
│   └── organisms/    # TodoItem, TodoForm, TodoFilters
├── api/
│   ├── client.ts     # axios 实例
│   └── todos.ts      # TODO 相关请求
├── stores/
│   └── filterStore.ts
├── hooks/
│   └── useTodos.ts   # TanStack Query hooks
├── types/
│   └── todo.ts       # 共享类型（与后端同步）
└── lib/
    └── validators.ts # zod schema
```

## 3. 页面树

```
/                  → 重定向到 /todos
/todos             → TodoListPage  （列表 + 弹窗创建/编辑）
*                  → NotFoundPage
```

> 本期单页面应用，所有交互（创建/编辑/删除确认）都用弹窗实现，不做独立详情页。

## 4. 组件清单

### Atoms

| 组件 | 职责 |
|------|------|
| Button | 按钮，支持 primary/secondary/danger 三种变体 |
| Input | 单行输入框，含错误状态 |
| Textarea | 多行输入框 |
| Checkbox | 复选框（点击切换 TODO 状态） |
| Badge | 优先级标签（高/中/低对应红/黄/灰） |
| Select | 下拉选择 |

### Molecules

| 组件 | 职责 |
|------|------|
| FormField | label + Input/Textarea + 错误提示 |
| EmptyState | 列表为空时的占位 |
| ConfirmDialog | 删除确认弹窗 |
| LoadingSpinner | 加载状态 |

### Organisms

| 组件 | 职责 | 数据来源 |
|------|------|---------|
| TodoItem | 单条 TODO 展示（标题/复选框/优先级/操作按钮） | props |
| TodoForm | 创建/编辑表单 | react-hook-form |
| TodoFilters | 筛选与排序控件 | filterStore |
| TodoList | TODO 列表容器 | useTodos hook |

## 5. 页面-接口映射表

| 页面 | 用户操作 | 调用接口 | 请求参数 | 响应处理 |
|------|---------|---------|---------|---------|
| TodoListPage | 进入页面 / 切换筛选 / 切换排序 | GET /todos | page, pageSize, filter[completed], sortBy, order | 渲染列表，缓存 5 分钟 |
| TodoListPage | 点击「新建」并提交表单 | POST /todos | title, description, priority, dueDate | 关闭弹窗，invalidate 列表缓存 |
| TodoListPage | 点击复选框切换完成状态 | PATCH /todos/:id | { completed: !completed } | 乐观更新，失败回滚 |
| TodoListPage | 点击「编辑」并提交表单 | GET /todos/:id → PATCH /todos/:id | id / 表单字段 | 关闭弹窗，invalidate 列表缓存 |
| TodoListPage | 点击「删除」并确认 | DELETE /todos/:id | id | 关闭弹窗，invalidate 列表缓存 |
| TodoListPage | 翻页 | GET /todos | page, pageSize | 渲染列表 |

## 6. 状态管理方案

### 服务端状态（TanStack Query）

| Query Key | 用途 |
|-----------|------|
| `['todos', filters, sort, page]` | TODO 列表 |
| `['todos', id]` | 单条详情（编辑前查询） |

**Mutation:**
- `createTodo` — 成功后 invalidate `['todos']`
- `updateTodo` — 乐观更新 + 失败回滚
- `deleteTodo` — 成功后 invalidate `['todos']`

### 客户端状态（Zustand）

```typescript
interface FilterStore {
  completed: 'all' | 'pending' | 'done';
  sortBy: 'createdAt' | 'priority' | 'dueDate';
  order: 'asc' | 'desc';
  setFilter: (k: keyof FilterStore, v: unknown) => void;
}
```

### 数据流向

```
User Action → Component
    ↓
    ├─ 客户端状态变化 → Zustand store → 组件重渲染
    └─ 服务端数据请求 → TanStack Query → API Client → 后端
                              ↓
                         缓存更新 → 组件重渲染
```

## 7. 路由与权限

本期无认证，所有路由公开访问。

## 8. UI/UX 设计资料索引

| 资料 | 位置 |
|------|------|
| 线框图 | `resource/wireframe.png` |
| 组件库 | TailwindCSS + Headless UI |
| 设计令牌 | `tailwind.config.js`（颜色、间距、字体） |

## 9. 前端非功能方案

### 性能优化

- TanStack Query 缓存 5 分钟，减少重复请求
- 列表项使用 React.memo 避免无关重渲染
- Vite 自动代码分割

### 无障碍

- 所有交互元素有 `aria-label`
- Headless UI 组件原生支持键盘导航
- 颜色对比度满足 WCAG AA

### 错误处理

- API 错误用 ErrorBoundary 兜底
- Mutation 失败用 toast 提示用户
- 网络错误自动重试 1 次（TanStack Query 配置）

### 响应式

- 移动端: 单列布局，弹窗全屏
- 桌面端: 居中容器，弹窗居中
- Tailwind breakpoints: sm (640px) / md (768px) / lg (1024px)
