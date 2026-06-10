---
id: frontend-ui
version: 1
priority: 40
triggers: ["ui", "page", "component", "form", "modal", "frontend", "页面", "组件", "交互", "表单", "前端"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["前端设计/页面与组件树", "前端设计/交互流", "前端设计/状态管理", "前端设计/校验与错误展示", "前端设计/加载空态错误态"]
review_checklist: ["component_tree", "interaction_flow", "state_owner", "validation_errors", "loading_empty_error", "accessibility"]
---

# frontend-ui

## 适用场景

页面、组件、表单、弹窗、状态管理、交互体验；无后端变更或只调用既有 API。

## 输出要求

后端和数据章节仍保留；无变更时写“不涉及 + 原因”。

## 必填项

- 页面/组件树。
- 用户交互流。
- 状态管理归属。
- 表单校验和错误展示。
- loading/empty/error 状态。
- 权限态/不可用态。
- 可访问性和响应式要求。
- 与 API 的契约边界。

## 常见反模式

- 只画 UI，不写错误态。
- 把 API 字段名猜出来却不标明来源。
- loading/empty/error 全靠实现临场发挥。
- 用颜色作为唯一状态表达，破坏可访问性。

## 输出片段示例

```markdown
## 前端设计

### 页面与组件树
- `/orders`: `OrderPage -> FilterBar -> OrderTable -> Pagination`。

### 交互流
1. 用户修改筛选条件。
2. URL query 更新。
3. 拉取列表；失败显示可重试错误态。

### 校验与错误展示
- 日期范围最长 1 年；字段级错误显示在控件下方。
```
