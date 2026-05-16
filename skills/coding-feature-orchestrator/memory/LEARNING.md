---
doc_type: learning_memory
doc_status: active
updated_at: ""
---

# 经验教训 (LEARNING)

从 metrics 聚合分析和 error recovery reflection 中提取的模式和经验。

## 流程模式

无记录。

## 常见阻塞原因

无记录。

## Recovery 经验

无记录。

## 效率优化

无记录。

---

## 自动学习规则

1. 每完成 3 个 feature 后，运行 `aggregate_metrics.py` 并从报告中提取模式：
   - 平均阶段耗时趋势（哪个阶段最耗时？是否在改善？）。
   - 高频阻塞原因（重复出现的 blocker 类型）。
   - Fast-track vs standard 使用比例（是否有更多需求适合 fast-track？）。
2. 从 error recovery 的 reflection 中提取：
   - 重复出现的错误类型和根因。
   - 有效的预防措施。
   - 需要更新 design 或 tasks 的模式。
3. 每条经验标注数据来源（哪些 feature 的 metrics）和提取日期。
4. 经验条目应可操作：不只是"X 经常发生"，而是"当 Y 条件时，优先做 Z"。
