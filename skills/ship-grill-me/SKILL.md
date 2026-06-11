---
name: ship-grill-me
description: "ShipKit 嵌入式质询助手。Understand/Design ready 前必须执行 blocking review，先查证据，再一次只问用户一个关键阻塞问题。"
---

# ship-grill-me

## 目标

在 `requirements.md` 或 `design.md` 标记 `status: ready` 前，把会阻塞实现或导致返工的问题挖出来。

它通常嵌入 `ship-understand` 和 `ship-design`，不是独立阶段；但如果用户单独调用，也必须按 TODO preflight 创建自己的审查 TODO。

## TODO preflight

- 嵌入调用时：不要创建新的独立 TODO，但必须更新父阶段 TODO 和审查记录。
- 单独调用时：必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Grill TODO：
  1. 加载 `feature_dir`、`meta.yml` 和当前阶段文档。
  2. 加载相关 spec、source_refs、参考模板和已有代码证据。
  3. 列出 blocking 问题。
  4. 先从仓库/spec/来源材料找答案。
  5. 一次只向用户提出一个最关键问题。
  6. 把答案写回父阶段文档或审查记录。
  7. 重新运行对应 validator。

## 必须触发的位置

- Understand 阶段 ready 前必须执行 blocking review。
- Design 阶段 ready 前必须执行 blocking review。

不存在按流程模式跳过的例外。PRD、UI/UX、link、split 子需求都只是来源或元数据形态，不改变 full flow 审查要求。

## blocking 判定

Understand blocking：

- 没有可测试 AC。
- AC 缺 Given/When/Then 且会影响实现。
- 需求互相冲突。
- 引用不存在或未定义的现有功能。
- 边界条件缺失会改变数据模型/API。
- primary `source_refs` 不可读或状态为 `inaccessible/needs_user`。
- project group 下 `projects` 缺失或与 `.docs/ship/project.yml` 不一致。

Design blocking：

- API 缺 Request/Response/Error。
- 数据模型与 spec 或现有表冲突。
- 错误处理缺失。
- 性能目标无法由设计解释。
- 前后端责任边界不清。
- 设计未覆盖某个 AC。
- 模板选择明显不匹配需求类型。
- 缺少 `meta.yml.design_template_ref` 或正文 `## 方案模板引用`。
- 模板必填项缺失且无“不涉及 + 原因”或模板偏离说明。
- 偏离项目 spec、现有代码事实或 AC，且没有解释影响与替代设计。
- `status: ready` 仍包含未替换模板变量、`TBD`、`待补充`、`后续再说`、无解释的“视情况而定”。

warning 不阻塞 ready，但必须记录到文档风险或审查记录里。

## 质询流程

1. 扫描当前 draft、`meta.yml`、`requirements.md`、`design.md`、`source_refs`、spec 引用和参考模板。
2. 列出所有问题，只保留 blocking 问题。
3. 对每个问题，先从仓库、`.docs/spec/`、已有 feature 文档、来源材料和模板文件找答案。
4. 找到答案：自动修正文档，并记录依据。
5. 找不到答案：一次只问用户一个最关键问题。
6. 用户回答后立刻更新 draft 或审查记录。
7. 重新运行对应 validator。
8. 无 blocking 后返回 `ready`；仍有阻塞则更新 `meta.yml.status: blocked` 和 `blocked_reason: awaiting_grill_answers`。

## 问题格式

每个问题必须包含四个部分：当前阻塞、已检查证据、推荐答案、影响。

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

- 一次只问一个问题。不要把多个阻塞问题糊成一坨。
- 必须给推荐答案和证据；没有证据就说没有。
- 能从仓库/spec/source_refs 得到答案就不要问用户。
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
  - 性能目标未量化，已记录为 Design 风险
```

## 不做什么

- 不替代用户确认 Design → Build。
- 不做泛泛 code review。
- 不把 non-blocking warning 升级成形式主义门禁。
- 不把 `review_checklist` 变成 validator 的硬语义门禁；语义问题只在会导致返工时 blocking。
- 不绕过父阶段 TODO 或审查记录。
