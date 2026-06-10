---
name: ship-grill-me
description: "新 ShipKit 嵌入式质询助手。Understand/Design ready 前发现 blocking 问题，先查仓库和 spec，再一次只问用户一个关键问题。"
---

# ship-grill-me

## 目标

在文档标记 `status: ready` 前，把会阻塞实现或导致返工的问题挖出来。它不是独立阶段；只嵌入 `ship-understand` 和 `ship-design`。

## 触发矩阵

| 场景 | Understand | Design |
|---|---|---|
| `quick_start` | 条件触发：有 blocking 问题 | 跳过 |
| `full_flow` | 必须触发 | 必须触发 |
| `prd_direct` | 跳过 | 条件触发：有技术风险 |
| `split_first` | 子 feature 按 full_flow | 子 feature 按 full_flow |

## blocking 判定

Understand blocking：

- 没有可测试 AC。
- AC 缺 Given/When/Then 且会影响实现。
- 需求互相冲突。
- 引用不存在或未定义的现有功能。
- 边界条件缺失会改变数据模型/API。

Design blocking：

- API 缺 Request/Response/Error。
- 数据模型与 spec 或现有表冲突。
- 错误处理缺失。
- 性能目标无法由设计解释。
- 前后端责任边界不清。
- 设计未覆盖某个 AC。
- 模板选择明显不匹配需求类型。
- `full_flow`、`prd_direct`、`split_first` 子 feature 缺少模板引用事实或正文 `## 方案模板引用`。
- 模板必填项缺失且无“不涉及 + 原因”或模板偏离说明。
- 偏离项目 spec、现有代码事实或 AC，且没有解释影响与替代设计。
- `status: ready` 仍包含未替换模板变量、`TBD`、`待补充`、`后续再说`、无解释的“视情况而定”。
warning 不阻塞 ready，但必须记录在文档风险里。

Design 模板 warning：

- `quick_start` 未使用模板，但已说明低风险原因。
- 模板要求项与本需求无关，且已写“不涉及 + 原因”。
- 有模板但未充分说明候选模板评分；不影响实现时只记录风险。

## 质询流程

1. 扫描 draft doc、`meta.yml`、requirements、spec 引用和参考模板。
2. 列出所有问题，只保留 blocking 问题。
3. 对每个问题，先从仓库、`.docs/spec/`、已有 feature 文档和模板文件找答案。
4. 找到答案：自动修正文档，并记录依据。
5. 找不到答案：一次只问用户一个问题。
6. 用户回答后立刻更新 draft。
7. 重新运行 `validate_design.py` 或对应 validator。
8. 无 blocking 后返回 `ready`；仍有阻塞则更新 `meta.yml.status: blocked`。

## 问题格式

```text
问题 1/3：导出范围
当前阻塞：需求未明确用户可导出的时间范围，影响 API 参数和查询索引。
已检查证据：.docs/spec/shared/existing-features.md 中订单查询支持时间范围筛选。
推荐答案：支持自定义时间范围，最长 1 年。
影响：若不确认，Design 无法确定查询约束和性能目标。

你的决定？
[采纳推荐] / [自定义答案]
```

Design 模板问题示例：

```text
问题 1/2：异步任务幂等策略
当前阻塞：需求包含 MQ 消费，但 design.md 未定义幂等 key。重复消费会导致订单状态被重复推进。
已检查证据：async-task@1 要求定义 idempotency_key；现有 spec 未提供统一规则。
推荐答案：使用 order_id + event_type + event_version 作为幂等 key，写入 processed_events 表。
影响：不确认该策略，Build 阶段无法安全实现消费者。

你的决定？
[采纳推荐] / [自定义答案]
```

## 提问规则

- 一次只问一个问题。不要把 5 个问题糊成一坨。
- 必须给推荐答案和证据；没有证据就说没有。
- 能从仓库/spec 得到答案就不要问用户。
- 不问偏好型废话，只问会影响实现的决策。
- 用户回答模糊时，追问最小必要信息。

## 输出给阶段技能

```yaml
result: ready # ready | blocked
resolved:
  - id: Q-001
    source: spec
    summary: 使用现有订单查询时间范围规则
pending: []
warnings:
  - 性能目标未量化，quick_start 下记录为风险
```

## 不做什么

- 不替代用户确认 Design → Build。
- 不做泛泛 code review。
- 不把 non-blocking warning 升级成形式主义门禁。
- 不把 `review_checklist` 变成 validator 的硬语义门禁；语义问题只在会导致返工时 blocking。
