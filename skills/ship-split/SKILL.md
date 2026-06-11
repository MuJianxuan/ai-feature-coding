---
name: ship-split
description: "ShipKit 可选前置分析技能。把大需求拆成可独立交付的小 feature 建议，只生成 splits.yml，不直接创建 feature 目录。"
---

# ship-split

## 目标

把大需求拆成多个小需求建议。每个子需求必须能独立测试、独立交付，并有清楚依赖。

`ship-split` 是独立前置分析技能，不是 ShipKit feature flow 内部模式。它只产出拆分建议；用户确认后的 feature 目录创建统一交回 `ship-orchestrator` 执行。

## TODO preflight

开始拆分前，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Split TODO：

1. 加载大需求来源和已有 feature 上下文。
2. 加载 spec：已有功能、业务域、项目边界。
3. 识别独立功能模块或用户故事。
4. 标注依赖、优先级、预计工期。
5. 生成 `splits.yml`。
6. 让用户确认拆分方案。
7. 输出给 `ship-orchestrator` 的批量创建 handoff。

## 何时使用

- 用户明确说"拆分"、"这个需求太大"、"拆成任务"。
- 需求包含 5 个以上独立功能点。
- 单个需求预计超过 3 天。
- 需要生成 TAPD/Jira 任务清单。

不要用于已经很小的需求，也不要把用户明确只要的一小块强行拆开。

## 输入

- 大需求描述、PRD、会议纪要、用户故事。
- TAPD/Jira 链接或导出数据（如果有）。
- `ship-spec` 加载的现有功能、业务域、技术栈。
- 可选 workspace scope；若不确定，只在拆分建议中记录待 orchestrator 确认。

## 流程

1. 加载 spec：已有功能、业务域、项目边界。
2. 识别独立功能模块或用户故事。
3. 按业务价值和技术依赖排序。
4. 控制粒度：单个子需求 `estimated_days <= 3`。
5. 生成 `splits.yml`。
6. 让用户确认拆分方案：`[yes] 交给 orchestrator 批量创建`、`[modify] 修改`、`[tapd] 同步任务`。
7. 用户确认后，输出 handoff；不得自己创建 `.docs/feature-*` 或初始 `meta.yml`。

## 拆分原则

- 每个子需求可独立验证，有独立 AC。
- 依赖必须显式：不要靠口头顺序。
- 优先交付基础能力，再交付增强能力。
- 同级任务尽量可并行。
- 不为追求整齐而拆出没有业务价值的假任务。

## splits.yml 格式

```yaml
parent_requirement: "用户管理系统"
split_strategy: "by_user_story"
estimated_total_days: 12
splits:
  - id: REQ-001
    name: 用户注册
    suggested_slug: user-register
    suggested_feature_name: 用户注册
    priority: high
    estimated_days: 2
    dependencies: []
    created_feature_dir: ""
    status: pending
    blocked_by: []
    tapd_id: ""
  - id: REQ-002
    name: 用户登录
    suggested_slug: user-login
    suggested_feature_name: 用户登录
    priority: high
    estimated_days: 1
    dependencies: [REQ-001]
    created_feature_dir: ""
    status: blocked
    blocked_by: [REQ-001]
```

`created_feature_dir` 默认必须为空；只有 `ship-orchestrator` 批量创建子 feature 后才能回填实际目录。

## 批量创建 handoff

用户确认拆分方案后，输出给 orchestrator 的创建请求：

```text
拆分方案已确认，但 ship-split 不创建 feature 目录。
请调用 ship-orchestrator 批量创建以下子 feature，并为每个目录写入 workflow: full_flow：
1. REQ-001 用户注册，suggested_slug=user-register，dependencies=[]
2. REQ-002 用户登录，suggested_slug=user-login，dependencies=[REQ-001]
```

orchestrator 为每个子 feature 创建目录和 `meta.yml`，统一写入 `parent_split_id/split_id/split_dependency`。

## 依赖检查

每次继续 split feature 前执行：

1. 读取 `splits.yml`。
2. 对每个未完成 split，检查 `dependencies` 指向的 split 是否 `status: completed`。
3. 未完成则写入 `blocked_by`，并同步对应 feature `meta.yml.status: blocked`。
4. 已解除依赖则清空 `blocked_by`，同步 `status: in_progress`。

依赖状态更新可以辅助 orchestrator 恢复，但不得越权创建或删除 feature 目录。

## TAPD/Jira 集成边界

本技能只定义集成框架，不能伪造远程任务创建成功。

- 如果没有凭证/API 配置：只生成可导入字段，不调用接口。
- 如果调用 API：必须把返回的 `tapd_id`/`jira_key` 写回 `splits.yml`。
- API 失败：保留本地 `splits.yml`，报告失败原因，不阻塞本地 ShipKit 流程。

## 输出

```text
拆分方案生成完成。
建议顺序：
1. REQ-001 用户注册（无依赖）
2. REQ-002 用户登录（依赖 REQ-001）

是否交给 ship-orchestrator 批量创建 feature？
[yes] 交给 orchestrator
[modify] 修改拆分
[tapd] 准备/同步 TAPD 任务
```

## 不做什么

- 不直接创建 `.docs/feature-*`。
- 不写初始 `meta.yml`。
- 不把实际目录写进 `created_feature_dir`，除非 orchestrator 已创建并回填。
- 不替代 Understand/Design/Build 阶段。
