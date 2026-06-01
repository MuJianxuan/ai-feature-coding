---
name: ship-tech-discovery
description: "ShipKit stage. Performs project-reality-first technical discovery, then turns evidence into stack decisions. Use after ship-define-review completes."
---

# 技术发现 (Tech Discovery)

## Overview

本阶段将“项目现状发现、技术调研、技术选型”收敛为一个技术发现阶段。它仍然保留两份独立产物：

- `tech-research.md`
- `tech-selection.md`

核心原则：
- **Project Reality First**：已有项目上的需求必须先发现真实代码、表、API、页面、服务、worker、MQ、权限和既有 feature 文档，再谈方案
- **Requirement-to-Reality Mapping**：按 requirements.md 的 Domain ID / AC ID 映射现有系统关系，区分 `reuse / extend / replace / new / avoid / unknown`
- **Source-Driven**：外部技术信息必须来自可追溯来源；项目事实必须来自代码路径、文档路径、命令输出或用户确认
- **Decision-Backed**：每个选型必须有证据、备选方案与 ADR
- **Sequential Within Stage**：阶段内固定先 research，后 selection

已有项目迭代时，本阶段优先级固定为：

```text
已有项目事实发现 > 需求与现有系统关联映射 > 产出前用户对齐 > 技术调研 / 技术选型
```

## When to Use

- `requirements.md` 已通过 `ship-define-review` gate
- 需要把需求和 workspace / feature `meta.yml.projects` 的真实现状对齐
- 需要确认已有功能、表结构、API、页面、服务、权限、worker、MQ topic、配置或测试是否可复用/扩展
- 需要确认最新技术信息并据此锁定技术栈
- 项目即将进入 `ship-contract`

## When NOT to Use

- `ship-define-review` 尚未通过
- workspace 未明确，且无法通过 `.docs/ship/project.yml` 或 feature `meta.yml.spec_context` 确定
- 用户只要求一次性技术咨询，不进入 ShipKit feature workflow

说明：即使本次“无新技术引入、无架构决策”，只要是在已有项目上做功能迭代，仍需要最小 Project Reality Scan；不能因为技术栈固定就跳过项目事实发现。

### technical_plan_provided 裁剪规则

当 `meta.yml.scenario: technical_plan_provided` 时，本阶段仍必须执行 Project Reality Scan，但扫描范围只围绕 `technical_plan_source.selected_scope`：

- 优先按 selected scope 的章节名、接口、模块、标题、代码路径和关键词搜索仓库。
- `Requirement-to-Reality Mapping` 只覆盖 selected scope 对应的 Domain ID / AC ID。
- 不扫描未选中章节对应的功能；未选中内容默认视为 out_of_scope。
- 若未选中内容构成 selected scope 的前置依赖或冲突，只记录为 risk / open question，并询问是否扩大 selected scope，不自动纳入本期。
- `repository_scan_status: ready` 只是 meta 索引；真正允许进入后续阶段的事实源仍是 `tech-research.md` 和 `tech-selection.md` 的 frontmatter 与内容校验。

## Stage Contract

本阶段属于单 stage 双产物：

1. **research 子段**
   - 产出 `tech-research.md`
   - frontmatter:

```yaml
---
stage: ship-tech-discovery
artifact_role: research
stage_status: draft
updated_at: ""
evidence_complete: false
---
```

2. **selection 子段**
   - 产出 `tech-selection.md`
   - frontmatter:

```yaml
---
stage: ship-tech-discovery
artifact_role: selection
stage_status: draft
updated_at: ""
evidence_complete: false
spec_checked_at: ""
referenced_spec_ids: []
spec_warnings: []
---
```

阶段退出条件：
- `tech-research.md.stage_status = ready`
- `tech-selection.md.stage_status = ready`

仅当两者都满足时，`ship-orchestrator` 才允许进入 `ship-contract`。

## Process

```
1. 读取 requirements.md + meta.yml + workspace 配置
   verify: project_context、project_scope、Domain ID、AC ID、workspace、feature `meta.yml.projects` 已确认
2. 执行 Project Reality Scan
   verify: 已发现与需求相关的代码、表、API、页面、服务、worker、MQ、权限、日志/metrics、测试和既有 feature 文档
3. 建立 Requirement-to-Reality Mapping
   verify: 每个关键 Domain ID / AC ID 都有 reuse / extend / replace / new / avoid / unknown 判断和证据
4. 执行 Research Alignment Check
   verify: 已向用户总结项目发现、准备复用/扩展的内容、不确定项和继续假设；若用户纠正，已回到代码路径重新探索
5. 执行 Technical Research
   verify: 形成 source-backed 的外部技术调研、版本核查或方案对比；无外部技术调研需求时说明不适用
6. 写出 tech-research.md
   verify: 项目事实、证据、不确定项、对齐记录、selection 输入完整
7. 读取 tech-research.md + requirements.md
   verify: 候选方案、约束、既有系统关系和评估维度完整
8. 执行 selection 子段
   verify: 形成带 ADR 的 tech-selection.md，并完成 spec compatibility check
9. 交叉校验 research → selection
   verify: 每个关键决策都能回指 research 证据；不得覆盖 Project Reality Scan 中的 avoid/unknown 约束
10. 标记两个产物为 ready
   verify: 两份文档均无 TODO/待确认阻塞项；assumptions 已显式记录
```

## Delegation Boundary

本阶段采用“`research` 可辅助委派，`selection` 不可分叉”的策略。

- `research` 子段允许子代理协助做项目现状扫描、资料搜集、版本信息核验、对比矩阵初稿和来源清单整理
- `selection` 子段必须由主上下文统一完成，因为每个 ADR 都必须能回指 `tech-research.md` 的证据链
- 子代理不得直接把 `tech-selection.md.stage_status` 置为 `ready`，也不得跳过 spec compatibility check
- 子代理返回的只能是 research 证据包或候选矩阵，不直接编辑 `tech-research.md` / `tech-selection.md` 正文或 frontmatter
- 若 workspace 未明确，不允许进入 `selection`

## Part 1: Research

research 子段先做 Project Reality Scan，再做外部 Technical Research。对 `new_project`，Project Reality Scan 可以写“不适用：new_project，无既有代码基线”，但章节不能消失。

### Project Reality Scan / 项目现状发现

必须回答：
- 当前 workspace 是什么？若是 project_group，本需求默认关联哪些 `meta.yml.projects`？
- `project_context` 是 `existing_project`、`new_project` 还是 `unknown`？
- 本需求关联哪些已有业务域？
- 现有代码里是否已有相关功能？
- 现有 feature 文档里是否已有相同或相近功能？
- 现有 DB / ORM / migration 是否已有相关表或字段？
- 现有 API / route / RPC / message topic / cron / CLI 是否已有相关入口？
- 现有前端页面 / 组件 / store / API client 是否已有相关消费路径？
- 现有权限 / 角色 / 租户 / 审计 / 日志 / metrics 是否有约束？

### Requirement-to-Reality Mapping / 需求与已有系统映射

按 `requirements.md` 的 Domain ID / AC ID 建立映射：

```markdown
| Domain / AC | 需求摘要 | 现有项目发现 | 关系类型 | 证据路径 | 不确定项 |
|---|---|---|---|---|---|
| D-USER-001 / AC-USER-001 | 用户可查看资料 | 已有 users 表和 user profile API | extend | src/modules/user/user.service.ts | profile 字段归属需确认 |
```

关系类型固定为：
- `reuse`：直接复用
- `extend`：扩展已有功能
- `replace`：替换旧实现
- `new`：新增
- `avoid`：明确不触碰
- `unknown`：证据不足，需要用户确认

### Existing Surface Inventory / 现有表面清单

按层面梳理现有 surface：

```markdown
| Surface | Existing Item | Path / Source | Relation | Notes |
|---|---|---|---|---|
| DB | users | prisma/schema.prisma | extend | 已有 id/email/name |
| API | GET /api/users/:id | src/routes/user.ts | reuse | 当前返回字段不足 |
| Frontend | UserProfilePage | src/pages/user/Profile.tsx | extend | 已有展示，无编辑 |
| Backend Service | UserService | src/modules/user/user.service.ts | extend | 需要确认权限逻辑 |
```

Surface 类型建议包括：`DB`、`API`、`Frontend`、`Backend Service`、`Repository / DAO`、`Worker / MQ`、`Cron`、`Config`、`Auth / Permission`、`Observability`、`Test`、`Docs / Existing Feature`。

### Evidence and Uncertainty / 证据与不确定项

必须区分三类：

```markdown
### Confirmed Facts
- FACT-001: ...

### Conflicting Evidence
- CONFLICT-001: ...

### Open Questions
- Q-001: ...
```

规则：
- `Confirmed Facts` 必须有代码路径、文档路径、命令输出或用户确认作为证据
- `Conflicting Evidence` 必须说明冲突来源
- `Open Questions` 必须说明影响范围

### Research Alignment Check / 产出前对齐记录

这是过程动作，不是 hard gate；不新增 review 文档，不要求 `review_status / user_sign_off / signed_at`。

推荐记录格式：

```markdown
## Research Alignment Check / 产出前对齐记录

### Alignment Summary Presented to User
- 当前理解：
- 准备复用 / 扩展：
- 不确定项：
- 若按当前理解继续，将影响：

### User Feedback
- 用户确认：
- 用户纠正：
- 用户要求按假设继续：

### Follow-up Exploration
- 重新探索的路径：
- 修正后的结论：

### Final Research Baseline
- 本 research 产物基于哪些已确认事实：
- 哪些仍是 assumptions：
```

要求：
- 若用户纠正，必须有 `Follow-up Exploration`，并回到相关代码路径重新探索
- 若用户未明确确认但允许继续，必须记录 assumptions、风险和影响范围
- `tech-research.md.stage_status: ready` 不要求签字，但要求对齐记录存在
- 不得把假设伪装成已确认事实

### Technical Research / 技术调研

外部技术调研仍遵循 Source-Driven 纪律：

- 从 requirements.md 和 Project Reality Scan 提取调研点，按 `P0 / P1 / P2` 分级
- 优先使用官方文档、官方 release notes、官方 repo、registry 信息
- 所有 P0 项至少 2 个独立来源
- 所有 P1 项至少 1 个官方来源
- 输出对比矩阵、健康度信号、与非功能需求的匹配度
- 若当前 feature 无外部技术调研需求，写明“不适用 + 原因”

`tech-research.md` 必须至少包含：

1. Project Reality Scan / 项目现状发现
2. Requirement-to-Reality Mapping / 需求与已有系统映射
3. Existing Surface Inventory / 现有表面清单
4. Evidence and Uncertainty / 证据与不确定项
5. Research Alignment Check / 产出前对齐记录
6. Technical Research / 技术调研
7. Selection Inputs / 给 tech-selection.md 的输入
8. 信息来源清单

## Part 2: Selection

selection 子段遵循 ADR 决策纪律：

- 读取 `tech-research.md` 中的项目事实、候选与证据
- 读取 `requirements.md` 中的业务域、AC、非功能需求与约束
- 不得忽略 Project Reality Scan 中的现有表、API、页面、服务、权限、MQ、cron、测试和 docs 发现
- 通过 `ship-spec` hook 检查 workspace `spec_root` 下的已有规范是否与选型冲突，并记录 `referenced_spec_ids`
- 定义评估维度与权重
- 逐项做出技术栈和架构决策
- 每项决策必须有至少 1 个备选方案和不选理由
- 新项目必须给出官方推荐的初始化方案

`tech-selection.md` 必须至少包含：

1. 选型摘要
2. Project Reality Inputs（复用/扩展/替换/新增/避免的关键约束）
3. 技术栈决策表
4. ADR 列表
5. Spec Compatibility（引用规范、冲突结果、warnings）
6. 架构模式选择
7. 关键约束
8. 与 requirements.md 非功能需求的对齐验证
9. 项目初始化方案（仅新项目）

## Cross-Checks

在本阶段结束前必须执行以下一致性检查：

- `tech-selection.md` 中每个关键决策都能回指 `tech-research.md` 中的证据
- 若存在匹配规范，`tech-selection.md` 已记录对应 `spec_id`
- research 中识别出的高风险项、avoid 项和 unknown 项在 selection 中有处理策略
- requirements.md 的 Domain ID、AC ID 和非功能需求没有被 research 或 selection 漏掉
- `tech-selection.md` 中的新项目初始化命令与选定技术栈一致
- 已有项目的 selection 没有把“新增”当作默认答案；必须先说明为什么不能复用或扩展

## Evidence Rules

- 不允许只写 `tech-selection.md` 而跳过 `tech-research.md`
- 不允许 research 完成后直接进入 `ship-contract`
- 不允许 selection 使用“业界主流”“我记得”作为主要理由
- 不允许已有项目的 Project Reality Scan 只写“已检查，无影响”这类空话
- 如某信息无法确认最新状态，必须在 research 中显式标注风险
- 项目事实证据优先使用代码路径、文档路径、命令输出或用户确认；外部资料不能替代本地项目事实

## Verification

退出前逐项确认：

```markdown
- [ ] tech-research.md frontmatter 已设置 `stage: ship-tech-discovery` 和 `artifact_role: research`
- [ ] tech-selection.md frontmatter 已设置 `stage: ship-tech-discovery` 和 `artifact_role: selection`
- [ ] tech-research.md 包含 Project Reality Scan / Requirement-to-Reality Mapping / Existing Surface Inventory / Evidence and Uncertainty / Research Alignment Check
- [ ] existing_project 场景下 Project Reality Scan 有真实路径、接口、表、服务、组件、配置、测试或既有 feature 文档证据
- [ ] new_project 场景下 Project Reality Scan 写明“不适用：new_project，无既有代码基线”
- [ ] Research Alignment Check 已记录用户确认、纠正或按假设继续的事实
- [ ] 所有 P0/P1 调研点已完成，或明确不适用
- [ ] 所有关键决策都有 ADR
- [ ] 已完成 ship-spec compatibility check，并记录 `referenced_spec_ids` 或“无匹配规范”
- [ ] selection 中每个决策都引用了 research 证据
- [ ] 两份文档都无阻塞性 TODO
- [ ] 两份文档的 `stage_status` 都已正确置为 `ready`
```
