---
name: ship-frontend-design
description: "Optional Ship support skill for complex frontend design. Use when a UI/frontend task needs deeper page, component, state, routing, accessibility, or API-client design before planning."
---

# Ship Frontend Design

支持 skill，不是默认 runtime stage。小改动直接走 `ship-contract → ship-delivery-plan`；复杂前端才调用本 skill。

## Use When

- 多页面、多状态、多权限或复杂表单。
- 涉及 API client、server state、缓存、路由、可访问性。
- UI 设计材料需要转成组件和状态方案。

## Output

`frontend-design.md` 或 `resource/frontend-design.md`：

- Page / Component map
- UI state matrix
- API usage map
- Accessibility notes
- Existing surface reuse / extend / avoid
- Implementation risks

## Completion Criteria

- 设计能直接拆 slices。
- 页面状态和错误路径不缺失。
- 没有凭空创造设计稿中不存在的页面事实。
