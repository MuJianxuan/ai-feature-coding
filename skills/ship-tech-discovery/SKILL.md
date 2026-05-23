---
name: ship-tech-discovery
description: "ShipKit stage. Combines source-driven research and stack decisions into one technical discovery stage. Use after ship-intake-review completes."
---

# 技术发现 (Tech Discovery)

## Overview

本阶段将“技术调研”和“技术选型”合并为一个技术发现阶段。目标不是减少治理，而是把“先调研、再决策”的强顺序收敛到一个 skill 内完成，同时仍保留两份独立产物：

- `tech-research.md`
- `tech-selection.md`

核心原则：
- **Source-Driven**：最新信息必须来自可追溯来源
- **Decision-Backed**：每个选型必须有证据、备选方案与 ADR
- **Sequential Within Stage**：阶段内固定先 research，后 selection

## When to Use

- `requirements.md` 已通过 `ship-intake-review` gate
- 需要确认最新技术信息并据此锁定技术栈
- 项目即将进入 `ship-contract`

## When NOT to Use

- `ship-intake-review` 尚未通过
- 技术栈已完全固定且本次无需重新验证
- 仅是纯业务改动，无新技术引入、无架构决策

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
1. 读取 requirements.md
   verify: 技术约束、非功能需求、外部依赖已提取
2. 执行 research 子段
   verify: 形成 source-backed 的 tech-research.md
3. 读取 tech-research.md + requirements.md
   verify: 候选方案、约束和评估维度完整
4. 执行 selection 子段
   verify: 形成带 ADR 的 tech-selection.md，并完成 spec compatibility check
5. 交叉校验 research → selection
   verify: 每个关键决策都能回指 research 证据
6. 标记两个产物为 ready
   verify: 两份文档均无 TODO/待确认阻塞项
```

## Delegation Boundary

本阶段采用“`research` 可辅助委派，`selection` 不可分叉”的策略。

- `research` 子段允许子代理协助做资料搜集、版本信息核验、对比矩阵初稿和来源清单整理
- `selection` 子段必须由主上下文统一完成，因为每个 ADR 都必须能回指 `tech-research.md` 的证据链
- 子代理不得直接把 `tech-selection.md.stage_status` 置为 `ready`，也不得跳过 spec compatibility check
- 子代理返回的只能是 research 证据包或候选矩阵，不直接编辑 `tech-research.md` / `tech-selection.md` 正文或 frontmatter

## Part 1: Research

research 子段遵循 Source-Driven 纪律：

- 从 requirements.md 提取调研点，按 `P0 / P1 / P2` 分级
- 优先使用官方文档、官方 release notes、官方 repo、registry 信息
- 所有 P0 项至少 2 个独立来源
- 所有 P1 项至少 1 个官方来源
- 输出对比矩阵、健康度信号、与非功能需求的匹配度

`tech-research.md` 必须至少包含：

1. 调研范围
2. 技术调研结果
3. 框架/库对比矩阵
4. 社区活跃度和生态评估
5. 与项目需求的匹配度分析
6. 信息来源清单

## Part 2: Selection

selection 子段遵循 ADR 决策纪律：

- 读取 `tech-research.md` 中的候选与证据
- 读取 `requirements.md` 中的非功能需求与约束
- 通过 `ship-spec` hook 检查已有规范是否与选型冲突，并记录 `referenced_spec_ids`
- 定义评估维度与权重
- 逐项做出技术栈和架构决策
- 每项决策必须有至少 1 个备选方案和不选理由
- 新项目必须给出官方推荐的初始化方案

`tech-selection.md` 必须至少包含：

1. 选型摘要
2. 技术栈决策表
3. ADR 列表
4. Spec Compatibility（引用规范、冲突结果、warnings）
5. 架构模式选择
6. 关键约束
7. 与 requirements.md 非功能需求的对齐验证
8. 项目初始化方案（仅新项目）

## Cross-Checks

在本阶段结束前必须执行以下一致性检查：

- `tech-selection.md` 中每个关键决策都能回指 `tech-research.md` 中的证据
- 若存在匹配规范，`tech-selection.md` 已记录对应 `spec_id`
- research 中识别出的高风险项在 selection 中有处理策略
- requirements.md 的非功能需求没有被 research 或 selection 漏掉
- `tech-selection.md` 中的新项目初始化命令与选定技术栈一致

## Evidence Rules

- 不允许只写 `tech-selection.md` 而跳过 `tech-research.md`
- 不允许 research 完成后直接进入 `ship-contract`
- 不允许 selection 使用“业界主流”“我记得”作为主要理由
- 如某信息无法确认最新状态，必须在 research 中显式标注风险

## Verification

退出前逐项确认：

```markdown
- [ ] tech-research.md frontmatter 已设置 `stage: ship-tech-discovery` 和 `artifact_role: research`
- [ ] tech-selection.md frontmatter 已设置 `stage: ship-tech-discovery` 和 `artifact_role: selection`
- [ ] 所有 P0/P1 调研点已完成
- [ ] 所有关键决策都有 ADR
- [ ] 已完成 ship-spec compatibility check，并记录 `referenced_spec_ids` 或“无匹配规范”
- [ ] selection 中每个决策都引用了 research 证据
- [ ] 两份文档都无阻塞性 TODO
- [ ] 两份文档的 `stage_status` 都已正确置为 `ready`
```
