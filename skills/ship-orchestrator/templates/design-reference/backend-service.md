---
id: backend-service
version: 1
priority: 50
triggers: ["api", "service", "controller", "repository", "permission", "auth", "后端", "接口", "权限", "服务"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["API 契约/Request", "API 契约/Response", "API 契约/Error", "后端设计/鉴权与权限", "后端设计/事务边界", "后端设计/幂等设计"]
review_checklist: ["api_contract", "error_mapping", "auth_boundary", "transaction_boundary", "idempotency", "rollback"]
---

# backend-service

## 适用场景

API、服务层、权限、业务规则、数据模型变更；没有明显 UI 或 UI 只是调用既有页面。

## 输出要求

专项内容写进稳定基础章节，不能替代 `design.md` 顶层骨架。

## 必填项

- API path/method/request/response/error。
- 鉴权和权限边界。
- Controller/Service/Repository 分层。
- 事务边界。
- 错误码和异常映射。
- 数据模型、索引、唯一约束。
- 幂等要求；不需要也要说明为什么。
- 回滚方案。

## 常见反模式

- 只写“新增接口”不写错误响应。
- 忽略权限边界，让 Build 阶段猜。
- 数据唯一性只靠前端校验。
- 把 token、密码、生产地址写进设计。

## 输出片段示例

```markdown
## 后端设计

### 鉴权与权限
- 需要 `admin` 角色；普通用户返回 403 `FORBIDDEN`。

### 事务边界
- Service 方法内开启事务；写入订单和审计日志同事务提交。

### 幂等设计
- 使用 `request_id` 唯一索引防重复提交；无幂等要求时写明原因。
```
