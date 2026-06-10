---
id: data-migration
version: 1
priority: 70
triggers: ["migration", "schema", "backfill", "ddl", "sql", "迁移", "表结构", "回填", "清洗", "索引"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["数据模型/schema 变更", "数据模型/回填范围", "数据模型/校验方案", "风险和回滚/回滚方案", "性能考量/锁表与性能风险"]
review_checklist: ["schema_change", "backfill_scope", "online_migration", "lock_risk", "validation_sql", "rollback", "compat_window"]
---

# data-migration

## 适用场景

表结构变更、索引调整、数据迁移、回填、清洗、历史数据修复。

## 输出要求

重点写入 `数据模型`、`性能考量`、`风险和回滚`。不涉及 API/UI 时仍保留章节并说明原因。

## 必填项

- schema 变更。
- 数据回填范围。
- 是否在线迁移。
- 锁表/性能风险。
- 校验 SQL / 校验脚本。
- 回滚策略。
- 灰度和分批。
- 与旧代码兼容窗口。

## 常见反模式

- 只写 DDL，不写回滚。
- 大表加索引不评估锁表风险。
- 迁移后没有校验 SQL。
- 新旧代码兼容窗口被忽略。

## 输出片段示例

```markdown
## 数据模型

### schema 变更
- `orders` 新增 nullable 字段 `source`，默认由应用层写入。

### 回填范围
- 回填最近 180 天订单；每批 5000 行。

### 校验方案
- 校验 SQL：对比回填行数和 `source is null` 剩余数量。

## 性能考量
### 锁表与性能风险
- 使用在线 DDL；低峰执行；单批限速。
```
