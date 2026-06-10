---
id: async-task
version: 1
priority: 90
triggers: ["mq", "queue", "cron", "schedule", "batch", "retry", "dead-letter", "异步", "定时", "批处理", "重试", "死信"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["后端设计/触发与调度", "后端设计/消息体", "后端设计/幂等设计", "后端设计/重试与失败处理", "后端设计/可观测性", "风险和回滚/回放与回滚"]
review_checklist: ["idempotency_key", "retry_policy", "dead_letter", "failure_compensation", "monitoring_alert", "replay"]
---

# async-task

## 适用场景

MQ、定时任务、批处理、重试、死信、长耗时任务、异步消费者。

## 输出要求

专项内容写进 `后端设计`、`性能考量`、`风险和回滚`，不能替代顶层骨架。

## 必填项

- 触发条件：事件、定时、手动、补偿。
- 消息体结构。
- 幂等 key。
- 重试策略：次数、间隔、是否指数退避。
- 死信/失败队列。
- 消费并发和顺序性。
- 补偿机制。
- 监控指标和告警。
- 回滚和重放策略。

## 常见反模式

- 没有幂等 key。
- 重试无限循环或吞异常。
- 死信队列无人处理。
- 只写“异步处理”，不写触发、重放、告警。

## 输出片段示例

```markdown
## 后端设计

### 触发与调度
- 订单状态变更为 paid 后发布 `order.paid.v1`。

### 幂等设计
- 幂等 key：`order_id + event_type + event_version`，写入 `processed_events` 唯一索引。

### 重试与失败处理
- 最多重试 3 次，间隔 1/5/30 分钟；仍失败进入死信队列。

### 可观测性
- 指标：消费延迟、失败率、死信数量；死信 > 0 告警。
```
