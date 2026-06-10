---
id: config-change
version: 1
priority: 30
triggers: ["config", "feature flag", "permission", "role", "gray", "配置", "开关", "灰度", "权限", "角色"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["后端设计/配置项", "后端设计/默认值与兼容", "后端设计/灰度范围", "风险和回滚/回滚方案"]
review_checklist: ["default_value", "compatibility", "gray_scope", "audit", "rollback", "permission_matrix"]
---

# config-change

## 适用场景

配置项、灰度开关、权限矩阵、角色策略、功能开关、运行时参数调整。

## 输出要求

重点写默认值、兼容性、灰度范围、审计和回滚。小改也不能让默认行为变成谜。

## 必填项

- 配置项名称、类型、位置。
- 默认值。
- 兼容性和旧行为。
- 灰度范围和放量策略。
- 权限矩阵或角色影响。
- 审计记录。
- 回滚方式。

## 常见反模式

- 默认值不明确，导致线上行为随机。
- 灰度没有范围和退出条件。
- 权限矩阵只写“管理员可用”，不写其他角色。
- 配置回滚依赖改代码。

## 输出片段示例

```markdown
## 后端设计

### 配置项
- `order.export.enabled`: boolean，默认 `false`，读取现有配置中心。

### 默认值与兼容
- 默认关闭，保持旧行为；未配置时按 `false` 处理。

### 灰度范围
- 先对内部管理员开启，再按租户白名单放量。

## 风险和回滚
### 回滚方案
- 关闭开关即可恢复旧行为，无需回滚代码。
```
