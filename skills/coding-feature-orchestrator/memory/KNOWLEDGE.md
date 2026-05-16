---
doc_type: knowledge_memory
doc_status: active
updated_at: ""
---

# 项目知识 (KNOWLEDGE)

从已完成 feature 的 handoff.md 中提取的跨 feature 项目知识。

## API 模式

无记录。

## 数据模型

无记录。

## 常见陷阱

无记录。

## 架构决策

无记录。

---

## 自动学习规则

1. Feature 完成（handoff.md stage_status: complete）时触发知识提取。
2. 从 handoff.md 的"变更范围"和"残余风险与后续建议"中提取：
   - 新增或修改的 API 模式（endpoint 命名、认证方式、错误格式）。
   - 数据模型变更（新表、字段约定、索引策略）。
   - 踩过的坑（配置陷阱、依赖兼容性、环境差异）。
   - 重要架构决策（技术选型理由、设计取舍）。
3. 每条知识标注来源 feature 和日期。
4. 知识条目超过 20 条时，合并或归档低频条目。
