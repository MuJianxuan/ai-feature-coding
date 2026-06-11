---
name: ship-understand
description: "ShipKit Understand 阶段。必须接收 feature_dir，读取 meta/source_refs/spec，做 blocking review，产出 requirements.md(status: ready)。"
---

# ship-understand

## 目标

把 `feature_dir` 中登记的需求来源变成可设计、可验证的 `requirements.md`。它是后续 Design 和 Build 的唯一需求源。

## 硬前置

必须同时满足：

- 用户明确提供 `feature_dir`。
- `feature_dir/meta.yml` 存在且可读取。
- `meta.yml.source_refs` 至少包含一个 primary 来源。
- primary 来源可读或状态为 `available`；不可读时先阻塞质询。

缺 `feature_dir` 时停止，不自动扫描 `.docs/feature-*`，不创建新目录。

## TODO preflight

开始阶段工作前，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Understand 阶段 TODO：

1. 加载 `feature_dir` 与 `meta.yml`。
2. 读取 `source_refs` 与 `resource/` 来源材料。
3. 根据 `workspace_mode/projects` 限定仓库探索范围。
4. 加载 Understand 阶段 spec。
5. 探索仓库中相关现有功能。
6. 提取目标、边界、Domain、AC、NFR、约束。
7. 调用 `ship-grill-me` 做 blocking 质询。
8. 写入 `requirements.md(status: ready)`。
9. 运行 `validate_requirements.py <feature_dir>`。
10. 更新 `meta.yml.current_stage: design`。

## 输入

- `feature_dir/meta.yml`。
- `meta.yml.source_refs` 指向的 PRD、UI/UX、link、issue、meeting、note、screenshot 或 other。
- `resource/` 下的可读快照。
- `ship-spec` 按 workspace scope 加载的 existing-features、domain glossary、naming conventions。

`source_refs.type` 是输入形态，不是流程分支；所有 ShipKit feature 都走完整推进。

## Workspace scope

- `workspace_mode: single_project`：默认只探索当前项目；`projects` 若非空，用作项目名记录。
- `workspace_mode: project_group`：只探索 `meta.yml.projects` 指定项目和必要 `_shared` 内容。
- 需要扩大范围时先向用户说明证据和影响，得到确认后再更新 `meta.yml.projects`。

## 流程

1. 校验 `feature_dir`、`meta.yml`、`source_refs`。
2. 读取来源材料；外部链接不可访问时，更新 `meta.yml.status: blocked`、`blocked_reason: missing_source`，请用户提供可读快照。
3. 调用 `ship-spec` 加载 Understand 阶段上下文。
4. 按 workspace scope 探索相关现有功能，不读取无关项目。
5. 提取功能目标、用户、边界、Domain、AC、NFR、约束和风险。
6. 调用 `ship-grill-me` 做 blocking review；只问会阻塞实现的决策。
7. 生成或更新 `requirements.md`。
8. 运行 `validate_requirements.py <feature_dir>`；有 error 不得 ready。
9. 标记 `requirements.md status: ready`，更新 `meta.yml.current_stage: design`、`status: in_progress`。
10. 输出 handoff，要求新窗口调用 `ship-design <feature_dir>`。

## blocking review

Understand 阶段必须执行 `ship-grill-me`。blocking 问题包括：

- 没有可测试 AC。
- AC 缺 Given/When/Then 且会影响实现。
- 需求互相冲突。
- 引用不存在或未定义的现有功能。
- 边界条件缺失会改变数据模型/API。
- primary source 不可读或来源状态为 `inaccessible/needs_user`。
- project group 下 `projects` 缺失或与 `.docs/ship/project.yml` 不一致。

## requirements.md 结构

```markdown
---
status: ready
updated_at: "2026-06-09T12:00:00Z"
spec_refs: ["auth-flow", "user-domain"]
---

# 需求：用户登录

## 功能概述
一句话说明用户价值和功能边界。

## Domain 模型
- D-AUTH-001: 用户认证流程

## 验收标准 (AC)

### AC-1: 正常登录
**Given** 用户已注册  
**When** 输入正确的邮箱和密码  
**Then** 跳转到首页并显示用户名

## 非功能需求
- 响应时间：P95 < 500ms
- 并发：支持 1000 QPS

## 约束
- 复用现有 User 表
- 兼容移动端

## 假设和风险
- 假设现有邮箱服务可复用。
```

## 质量标准

必须满足：

- frontmatter 有 `status` 和 `updated_at`。
- 至少 1 个 AC。
- 每个 AC 使用 Given/When/Then。
- 有 Domain 模型或明确说明不涉及业务域。
- 非功能需求若存在，尽量量化。
- 与现有功能冲突必须解决或写入风险。
- 引用来源必须能追溯到 `meta.yml.source_refs`。

## 状态更新

成功后：

```yaml
current_stage: design
status: in_progress
artifacts:
  requirements: requirements.md
```

失败或等待回答：

```yaml
current_stage: understand
status: blocked
blocked_reason: awaiting_grill_answers # 或 missing_source / missing_workspace_scope
```

## 输出 handoff

```text
requirements.md 已 ready，并通过 validate_requirements.py。
当前阶段：design
workspace：project_group
涉及项目：web, api
下一步请在新窗口调用 ship-design，并明确传入 feature_dir：
.docs/feature-20260610-user-login
```

## 不做什么

- 不创建 feature 目录。
- 不自动猜测 `feature_dir`。
- 不做技术方案细节；那是 `ship-design`。
- 不写业务代码。
- 不为了填模板编造需求；无法确定就质询。
