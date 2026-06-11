---
name: ship-orchestrator
description: "ShipKit feature flow 统一入口。负责访谈、创建/恢复需求目录、维护 meta.yml、路由阶段，并持久化 Design → Build 用户确认。"
---

# ship-orchestrator

## 职责

`ship-orchestrator` 是 ShipKit feature flow 的编排层，只做这些事：

1. 判断用户请求是否需要进入 ShipKit feature flow；普通问答或小修 bug 不强行进入。
2. 创建或恢复 `.docs/feature-*` 需求目录。
3. 创建目录前读取 `.docs/ship/project.yml`，并让用户确认 workspace scope。
4. 收集需求来源并写入 `meta.yml.source_refs`。
5. 维护 `meta.yml` 这个跨窗口单一事实源。
6. 按 `meta.yml.current_stage` 输出下一阶段 handoff。
7. 在用户明确确认后，持久化 Design → Build approval。

它不替代阶段技能写 `requirements.md`、`design.md`、`build-plan.yml` 或业务代码。

## TODO preflight

开始任何编排工作前，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复本阶段 TODO：

1. 判定是否进入 ShipKit feature flow。
2. 读取 `.docs/ship/project.yml`（若存在）。
3. 创建或恢复 feature 目录。
4. 确认 workspace scope 与 projects。
5. 登记至少一个 primary `source_refs`。
6. 写入或更新 `meta.yml`。
7. 输出下一阶段 handoff 或处理 Build approval。

## 触发时机

用户表达以下任一意图时触发：

- 新建 feature："做一个…"、"开发…功能"、"新需求"、"帮我实现…"。
- 恢复 feature："继续"、"接着做"、"上次那个"、"回到 XX 功能"。
- 拆分需求："这个需求太大"、"帮我拆分"、"拆成 TAPD/Jira 任务"。
- 查询状态："现在到哪了"、"还有什么没做"、"feature 状态"。
- Design ready 后用户确认开始实现。

## 前置判断

1. 这是实际 feature 开发，还是普通问答/小修 bug？不是 feature flow 就不要创建 ShipKit 目录。
2. 是否在恢复已有 feature？恢复时必须读取用户给出的 `feature_dir/meta.yml`，不要靠对话记忆。
3. 是否是拆分请求？拆分只交给 `ship-split` 产出建议；实际创建子 feature 仍由本技能执行。
4. 创建新目录前是否已读取 `.docs/ship/project.yml`？若存在，必须把其中 workspace 配置作为推荐答案给用户确认。

## Feature 目录

默认由 orchestrator 创建或恢复：

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
workflow: full_flow
workspace_mode: single_project # single_project | project_group
workspace_name: "my-workspace"
projects: []
current_stage: understand # understand | design | build | done
status: in_progress # in_progress | blocked | completed
created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T14:30:00Z"
source_refs:
  - id: SRC-001
    type: prd
    title: "登录 PRD"
    path_or_url: "resource/prd.md"
    role: primary
    status: available
    notes: ""
spec_refs: []
requested_design_template: ""
design_template_ref: ""
design_template_reason: ""
artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md
# blocked_reason: awaiting_grill_answers | awaiting_user_confirmation | test_failures | missing_feature_dir | missing_source | missing_workspace_scope
# parent_split_id: REQ-ROOT
# split_id: REQ-001
# split_dependency: []
# build_approved_at: ""
# build_approved_by: ""
# build_approval_note: ""
```

## 固定访谈

创建新 feature 目录前必须确认三类信息：

1. **需求目录名**：基于需求标题推荐 `.docs/feature-YYYYMMDD-slug`，允许用户修改。
2. **workspace scope**：
   - 先读取 `.docs/ship/project.yml`。
   - 若存在，展示检测到的 `workspace_mode/workspace_name/projects`，请用户确认本需求涉及哪些项目。
   - 若 `workspace_mode: single_project`，`projects` 可为空或写当前项目名。
   - 若 `workspace_mode: project_group`，`projects` 必须至少包含 1 个项目名，并且必须是 `project.yml.projects` 的子集。
   - 若项目配置不存在但用户选择 project group，必须确认每个项目名对应仓库内项目目录；不能确认时阻塞为 `missing_workspace_scope`。
3. **需求来源**：至少登记一个 primary `source_refs`，可以是 PRD、UI/UX、link、issue、meeting、note、screenshot 或 other。来源正文放 `resource/` 或外部链接，不塞进 `meta.yml`。

不把 Design 模板意图作为固定必问题；只有用户主动提出或来源材料明确要求时，才把原话写入 `requested_design_template`。

## 路由规则

```text
用户输入
  ├─ 恢复 feature？ → 读取 feature_dir/meta.yml → 按 current_stage 输出 handoff
  ├─ 拆分请求？ → 调用 ship-split 只生成 splits.yml 建议
  ├─ 用户确认进入 Build？ → 持久化 build_approved_* 并切到 build
  └─ 新建 feature？ → 访谈 → 创建目录/meta → handoff 到 ship-understand
```

阶段技能必须显式接收 `feature_dir`；orchestrator 的 handoff 必须包含目录、下一阶段技能名、workspace mode 和 projects。

## Design 模板意图传递

用户如果显式说“按某模板写设计”“按 .docs/技术方案模版.md”“这是 MQ/异步任务按异步模板走”，本技能只把原话写入 `meta.yml.requested_design_template`。

不做这些事：

- 不解析模板 ID。
- 不判断模板文件是否存在。
- 不自动选择内置模板。
- 不生成或修改 `design.md`。

解析、选择、`design_template_ref` 和 `design_template_reason` 都属于 `ship-design`。

## 阶段推进门禁

| 转换 | 门禁 | 动作 |
|---|---|---|
| Understand → Design | AI 自检 | `requirements.md` frontmatter `status: ready`；`validate_requirements.py <feature_dir>` 无 errors；无未解决 blocking review |
| Design → Build | **用户确认** | `design.md` `status: ready`；`validate_design.py <feature_dir>` 无 errors；已记录 `design_template_ref`；明确询问并收到用户确认 |
| Build → Done | AI 验证 | 项目真实测试通过；`verification.md` 记录所有 AC 覆盖；`validate_build.py <feature_dir>` 无 errors |

Design → Build 是唯一硬用户确认门禁。用户只确认需求范围、AC 或问题答案，不等于确认开始实现。

## Build approval 持久化

收到用户明确确认开始 Build 后，orchestrator 必须更新：

```yaml
current_stage: build
status: in_progress
build_approved_at: "<ISO_TIMESTAMP>"
build_approved_by: user
build_approval_note: "<用户确认原话或摘要>"
```

同时清理 `blocked_reason: awaiting_user_confirmation`。`ship-design` 自身不得把 `current_stage` 改为 `build`；`ship-build` 缺 `build_approved_at` 必须停止。

## 阻塞处理

`meta.yml.status: blocked` 时不要假装继续。按 `blocked_reason` 处理：

- `awaiting_grill_answers`：调用 `ship-grill-me` 继续只问阻塞问题。
- `awaiting_user_confirmation`：复述设计摘要，问是否进入 Build；提供 `[yes] [modify] [review]`。
- `test_failures`：展示失败测试和最小修复计划，停留在 Build。
- `missing_feature_dir`：要求用户提供明确 `feature_dir`。
- `missing_source`：要求用户提供可读需求来源或允许把当前输入写入 `resource/`。
- `missing_workspace_scope`：要求用户确认 workspace mode 和 projects。
- `split_dependency` 或 `blocked_by` 非空：检查上游 split 状态；不要绕过依赖。

解除阻塞后把 `status` 改回 `in_progress`，清理 `blocked_reason`，更新 `updated_at`。

## 输出格式

新建完成时：

```text
需求目录已创建：.docs/feature-20260610-user-login
当前阶段：understand
workspace：project_group
涉及项目：web, api
下一步请在新窗口调用 ship-understand，并明确传入 feature_dir：
.docs/feature-20260610-user-login
```

恢复时：

```text
已加载 feature：.docs/feature-20260610-user-login
当前阶段：design
状态：blocked(awaiting_user_confirmation)
workspace：project_group
涉及项目：web, api
下一步：设计方案已 ready，请确认是否进入 Build。
```

Build approval 后：

```text
已记录 Build 确认：build_approved_at=2026-06-10T12:00:00Z
当前阶段：build
workspace：project_group
涉及项目：web, api
下一步请在新窗口调用 ship-build，并明确传入 feature_dir：
.docs/feature-20260610-user-login
```

## 不做什么

- 不创建旧 ShipKit 的细阶段文档。
- 不在 Design 用户确认前改业务代码。
- 不把 `meta.yml` 外的隐式记忆当事实。
- 不解析 Design 参考模板；只传递用户显式模板意图。
- 不让 `ship-split` 或阶段技能创建初始 feature 目录。
- 不为了形式主义生成无用文档；产物必须推进交付。
