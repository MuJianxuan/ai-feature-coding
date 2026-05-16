---
doc_type: work_memory
doc_status: active
updated_at: ""
---

# 工作记忆 (WORK)

当前活跃 feature 的工作状态。每次 orchestrator 启动时自动更新。

## 当前活跃 Feature

无活跃 feature。

## 上次停止点

无记录。

## 待处理问题

无。

---

## 自动维护规则

1. Orchestrator 每次启动时，扫描 `.docs/feature-*/` 目录，找到最近更新的 feature。
2. 更新"当前活跃 Feature"：feature 名称、当前阶段、pipeline_mode、最近事件。
3. 更新"上次停止点"：上次执行的阶段、任务 ID、停止原因。
4. 更新"待处理问题"：BLOCKED 任务、未回答的澄清问题、pending design approval。
5. Feature 完成（handoff complete）后，清空本文件并标记"无活跃 feature"。
