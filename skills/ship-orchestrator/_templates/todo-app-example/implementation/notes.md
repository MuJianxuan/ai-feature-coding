# TODO Web App — 实施要点

## 编码规范

- 使用 TypeScript 严格模式（`strict: true`）
- 命名: 文件 kebab-case，组件/类 PascalCase，变量/函数 camelCase
- 导入顺序: 第三方 → 共享类型 → 本模块
- 错误必须用自定义错误类（不抛字符串）
- 所有 API 调用必须用 try/catch 或 TanStack Query 处理错误

## Contract-First 原则

1. api-contract.md 是前后端共同遵守的合同
2. 任何接口变更必须先改 contract，再分别同步前后端
3. 前端 mock 应严格按 contract 实现，避免"mock 通过但真实接口失败"
4. 数据模型字段类型前后端一致（用共享 types 文件）

## 前端要点

- `tailwind.config.js` 配置主题色（priority: high=red-500, medium=yellow-500, low=gray-400）
- TanStack Query 的 staleTime 设置 5 分钟，cacheTime 10 分钟
- 创建/更新成功后调用 `queryClient.invalidateQueries(['todos'])`
- 删除前必须弹 ConfirmDialog
- 移动端断点用 `sm:` (640px) 和 `md:` (768px)
- 所有交互元素必须有 `aria-label`

## 后端要点

- Express 路由必须用 `next(error)` 而非 `res.status(500)` 直接返回错误
- Prisma 查询用 `select` 显式指定字段（即使本期返回全部字段，写明也利于后续优化）
- 日志用 pino 结构化输出，禁止 `console.log`
- 测试隔离：每个 test case 用独立内存数据库（`file::memory:?cache=shared`）
- 时间字段全部存 UTC，响应时序列化为 ISO8601

## 部署要点（开发环境）

```bash
# 同时启动前后端
# Terminal 1
cd todo-backend && npm run dev   # 监听 3001

# Terminal 2
cd todo-frontend && npm run dev  # 监听 5173

# 前端通过 vite proxy 转发 /api 到 3001
```

`vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:3001',
    },
  },
});
```

## 常见陷阱

| 陷阱 | 应对 |
|------|------|
| Prisma SQLite 不支持 enum | 用 string + zod 校验 |
| Prisma 时间字段返回 Date 对象 | 序列化时转 ISO 字符串 |
| TanStack Query mutation 后忘记 invalidate | 在 onSuccess 里调用 invalidateQueries |
| react-hook-form + zod 校验时机 | mode: 'onBlur' 更友好 |
| MSW 拦截 axios 但 fetch 漏拦 | 统一用 axios，不混用 fetch |
| CORS 配置不全 | 必须允许 localhost:5173 origin + Content-Type header |
