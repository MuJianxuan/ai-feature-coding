---
name: ship-split
description: "新 ShipKit 可选前置技能。把大需求拆成可独立交付的小 feature，生成 splits.yml，标注依赖，并可准备 TAPD/Jira 任务数据。"
---

# ship-split

## 目标

把大需求拆成多个小需求。每个子需求必须能独立测试、独立交付，并有清楚依赖。

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

## 流程

1. 加载 spec：已有功能、业务域、项目边界。
2. 识别独立功能模块或用户故事。
3. 按业务价值和技术依赖排序。
4. 控制粒度：单个子需求 `estimated_days <= 3`。
5. 生成 `splits.yml`。
6. 让用户确认拆分方案：`[yes] 批量创建`、`[modify] 修改`、`[tapd] 同步任务`。
7. 用户确认后，为每个 split 创建 `.docs/feature-*` 的 `meta.yml`。

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
    priority: high
    estimated_days: 2
    dependencies: []
    feature_dir: .docs/feature-20260609-user-register
    status: pending
    blocked_by: []
    tapd_id: ""
  - id: REQ-002
    name: 用户登录
    priority: high
    estimated_days: 1
    dependencies: [REQ-001]
    feature_dir: .docs/feature-20260609-user-login
    status: blocked
    blocked_by: [REQ-001]
```

## 批量创建 feature

用户确认后，每个 split 创建：

```yaml
feature_name: "用户登录"
current_stage: understand
status: blocked # 若依赖未完成；否则 in_progress
scenario: split_first
created_at: "..."
updated_at: "..."
spec_refs: []
artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md
parent_split_id: "用户管理系统"
split_id: REQ-002
split_dependency: [REQ-001]
blocked_reason: "等待依赖: REQ-001"
```

## 依赖检查

每次继续 split feature 前执行：

1. 读取 `splits.yml`。
2. 对每个未完成 split，检查 `dependencies` 指向的 split 是否 `status: completed`。
3. 未完成则写入 `blocked_by`，并同步对应 feature `meta.yml.status: blocked`。
4. 已解除依赖则清空 `blocked_by`，同步 `status: in_progress`。

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

是否批量创建 feature？
[yes] 批量创建
[modify] 修改拆分
[tapd] 准备/同步 TAPD 任务
```
