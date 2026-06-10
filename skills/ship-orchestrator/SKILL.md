---
name: ship-orchestrator
description: "新 ShipKit 统一入口。识别 feature 开发场景，路由到 split/understand/design/build，维护 meta.yml 单一事实源，并执行唯一用户确认门禁。"
---

# ship-orchestrator

## 职责

`ship-orchestrator` 是新 ShipKit 的编排层，只做五件事：

1. 识别用户入口：新建、恢复、拆分、状态查询。
2. 判定场景：`quick_start`、`full_flow`、`prd_direct`、`split_first`。
3. 识别用户是否有显式 Design 模板意图，并原样记录。
4. 按 `meta.yml.current_stage` 路由到阶段技能。
5. 执行阶段门禁，不让流程跳过关键验证。

它不替代阶段技能做具体产物。它也不把旧 ShipKit 的 14 阶段状态带进新设计。

## 触发时机

用户表达以下任一意图时触发：

- 新建 feature："做一个…"、"开发…功能"、"新需求"、"帮我实现…"。
- 恢复 feature："继续"、"接着做"、"上次那个"、"回到 XX 功能"。
- 拆分需求："这个需求太大"、"帮我拆分"、"拆成 TAPD/Jira 任务"。
- 查询状态："现在到哪了"、"还有什么没做"、"feature 状态"。

## 三个前置判断

开始前先做这三个判断，别过度设计：

1. 这是实际 feature 开发，还是普通问答/修 bug？不是 feature 流程就不要强行 ShipKit。
2. 有没有更简单路径？小功能优先 `quick_start`。
3. 会破坏什么？不要覆盖已有 feature；恢复时必须读取 `meta.yml`。

## 场景识别

| 场景 | 入口信号 | 起点 | grill-me 策略 |
|---|---|---|---|
| `quick_start` | 小功能、熟悉技术栈、低风险 | `ship-understand` | Understand 条件触发，Design 跳过 |
| `full_flow` | 中等复杂度、跨模块、风险不明 | `ship-understand` | Understand/Design 必须触发 |
| `prd_direct` | 有完整 PRD/原型/明确 AC | `ship-understand` PRD 解析模式 | Understand 跳过，Design 风险触发 |
| `split_first` | 显式要求拆分或大需求含 5+ 独立功能 | `ship-split` | 拆分后每个子需求走 `full_flow` |

不确定时降级到 `full_flow`。宁可多一次质询，不要把模糊需求直接推进实现。

## Feature 目录

默认创建或恢复：

```text
.docs/feature-YYYYMMDD-slug/
├── meta.yml
├── requirements.md
├── design.md
├── build-plan.yml
├── verification.md
└── resource/
```

`meta.yml` 是单一事实源：

```yaml
feature_name: "用户登录"
current_stage: understand # understand | design | build | done
status: in_progress       # in_progress | blocked | completed
scenario: full_flow       # quick_start | full_flow | prd_direct | split_first
created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T14:30:00Z"
spec_refs: []
requested_design_template: "" # 可选：用户显式要求的 Design 模板原话；orchestrator 不解析
design_template_ref: ""       # Design 阶段解析后写入，如 builtin:fullstack-feature@1
design_template_reason: ""    # Design 阶段写入简短选择依据
artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md
# blocked_reason: awaiting_grill_answers | awaiting_user_confirmation | test_failures
# parent_split_id: REQ-ROOT
# split_id: REQ-001
# split_dependency: []
```

## 路由规则

```text
用户输入
  ├─ 恢复模式？ → 读取 meta.yml → 路由到 current_stage
  ├─ 拆分请求？ → ship-split
  ├─ 有完整 PRD/原型？ → prd_direct → ship-understand
  └─ 默认 → full_flow 或 quick_start → ship-understand
```

优先级：恢复 > 拆分 > PRD 直通 > 新建。

## Design 模板意图传递

用户如果显式说“按某模板写设计”“按 .docs/技术方案模版.md”“这是 MQ/异步任务按异步模板走”，本技能只做一件事：把原话写入 `meta.yml.requested_design_template`。

不做这些事：

- 不解析模板 ID。
- 不判断模板文件是否存在。
- 不自动选择内置模板。
- 不生成或修改 `design.md`。

解析、选择、`design_template_ref` 和 `design_template_reason` 都属于 `ship-design`。这样 `meta.yml` 仍是单一事实源，但编排层不变成半个架构师。

## 阶段推进门禁

| 转换 | 门禁 | 动作 |
|---|---|---|
| Understand → Design | AI 自检 | `requirements.md` frontmatter `status: ready`；`validate_requirements.py` 无 errors；无未解决 blocking grill-me |
| Design → Build | **用户确认** | `design.md` `status: ready`；`validate_design.py` 无 errors；非 quick_start 已记录 `design_template_ref`；明确询问并收到 yes/开始/确认 |
| Build → Done | AI 验证 | 项目真实测试通过；`verification.md` 记录所有 AC 覆盖；`validate_build.py` 无 errors |

`Design → Build` 是唯一硬用户门禁。用户只确认需求范围、AC 或问题答案，不等于确认开始实现。

## 阻塞处理

`meta.yml.status: blocked` 时不要假装继续。按 `blocked_reason` 处理：

- `awaiting_grill_answers`：调用 `ship-grill-me` 继续只问阻塞问题。
- `awaiting_user_confirmation`：复述设计摘要，问是否进入 Build；提供 `[yes] [modify] [review]`。
- `test_failures`：展示失败测试和最小修复计划，停留在 Build。
- `split_dependency` 或 `blocked_by` 非空：调用 `ship-split` 检查上游状态。

解除阻塞后把 `status` 改回 `in_progress`，清理 `blocked_reason`，更新 `updated_at`。

## 输出格式

新建时：

```text
✓ 场景识别：full_flow
✓ 起点：ship-understand
当前阶段：Understand
目标：产出 requirements.md(status: ready)
下一步：加载 spec，解析需求，必要时 grill-me 质询。
```

恢复时：

```text
✓ 加载 feature：用户登录
✓ 当前阶段：Design
✓ 状态：blocked(awaiting_user_confirmation)
已完成：requirements.md
下一步：设计方案已 ready，是否开始 Build？
```

## 不做什么

- 不创建旧 ShipKit 的细阶段文档。
- 不在 Design 用户确认前改业务代码。
- 不把 `meta.yml` 外的隐式记忆当事实。
- 不解析 Design 参考模板；只传递用户显式模板意图。
- 不为了形式主义生成无用文档；产物必须推进交付。
