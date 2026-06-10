---
id: fullstack-feature
version: 1
priority: 60
triggers: ["fullstack", "api", "ui", "database", "端到端", "全栈", "页面", "接口", "数据"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["API 契约/Request", "API 契约/Response", "前端设计/状态管理", "后端设计/鉴权与权限", "风险和回滚/回滚方案"]
review_checklist: ["e2e_ac_mapping", "api_ui_boundary", "state_sync", "data_model", "rollback"]
---

# fullstack-feature

## 适用场景

同时涉及 UI、API、后端业务和数据模型的端到端功能。

## 输出要求

重点把前后端边界、接口契约、状态同步和 AC 端到端覆盖说清楚。

## 必填项

- AC 到 UI/API/后端/数据的覆盖映射。
- 前后端接口契约。
- 状态同步和缓存失效策略。
- 鉴权、权限、错误码。
- 数据模型和兼容性。
- 端到端测试建议。
- 回滚方案。

## 常见反模式

- 前端设计和 API 契约字段不一致。
- API 成功态写了，失败态不写。
- 数据迁移影响旧页面但没有兼容窗口。
- 只写单元测试，不写端到端 AC 覆盖。

## 输出片段示例

```markdown
## AC 覆盖映射
| AC | 设计位置 | 测试建议 |
|---|---|---|
| AC-1 | 前端设计/交互流；API 契约 POST /login；后端设计 AuthService | e2e 登录成功 |

## 前端设计
### 状态管理
- 登录状态由现有 auth store 持有；API 401 时清理本地 session。
```
