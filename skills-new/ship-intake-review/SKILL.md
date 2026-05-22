---
name: ship-intake-review
description: "ShipKit hard gate. Reviews requirements for completeness and correctness. Produces review-requirement.md. Use after ship-intake completes."
---

# 需求评审 (Requirement Review)

## Overview

需求评审是开发工作流的第二个阶段，是一个**硬门禁 (Hard Gate)** 阶段。本阶段对 `requirements.md` 进行结构化评审，发现遗漏、矛盾、模糊点，确保需求质量达到可进入设计阶段的标准。

核心目标：
- 逐条检查需求的完整性、一致性、可验证性
- 发现并分级问题（Critical / Major / Minor）
- 确保所有 Critical 问题在通过前修复
- 产出 `review-requirement.md` 作为硬门禁产物
- 用户必须明确批准才能放行

**硬门禁含义**：此阶段不可跳过、不可自动通过。必须有用户明确的"通过/批准/approved"才能标记为 approved，进入下一阶段。

## When to Use

- `requirements.md` 的 `stage_status` 为 `ready`，需求录入已完成
- 需求变更后需要重新评审
- 从 revision_needed 状态修改后重新提交评审

## When NOT to Use

- `requirements.md` 尚未完成（`stage_status: draft`）—— 先完成需求录入
- 已通过评审且无变更 —— 直接进入下一阶段
- 纯技术调研阶段的问题 —— 使用 tech-research 流程

## Gate Protocol (硬门禁规则)

```
┌─────────────────────────────────────────────────────────────┐
│                    硬门禁状态机                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  pending ──→ 执行评审 ──→ 产出评审结果                        │
│                              │                              │
│                    ┌─────────┼─────────┐                    │
│                    ▼         ▼         ▼                    │
│              [无 Critical] [有 Critical] [严重缺陷]           │
│                    │         │         │                    │
│                    ▼         ▼         ▼                    │
│            等待用户确认  revision_needed  rejected            │
│                    │         │         │                    │
│                    ▼         │         │                    │
│    用户说"通过" → approved   │         │                    │
│    用户说"不通过" → rejected │         │                    │
│                              ▼         ▼                    │
│                    返回 ship-intake 修改            │
│                    修改完成后重新进入本阶段评审                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 状态流转规则

| 当前状态 | 触发条件 | 目标状态 |
|---------|---------|---------|
| pending | 开始评审 | 评审进行中 |
| 评审完成，无 Critical | 等待用户确认 | pending（等待用户决定） |
| 用户明确说"通过/批准/approved" | 状态变更 | approved |
| 用户说"不通过/拒绝/rejected" | 状态变更 | rejected |
| 存在 Critical 问题 | 自动判定 | revision_needed |
| revision_needed / rejected | 修改后重新提交 | pending（重新评审） |

### 不可妥协的规则

1. **Critical 问题零容忍**：存在任何 Critical 问题时，禁止标记 approved
2. **用户确认必须明确**：不接受模糊表态（如"差不多吧"、"应该可以"），必须是明确的通过/批准/approved
3. **不可自动通过**：即使 checklist 全部通过，仍需用户明确确认
4. **修改必须重审**：revision_needed 修改后必须从头执行完整评审流程

## Review Checklist (评审清单详细说明)

逐条检查，每条必须给出明确的 通过/不通过 判定及理由：

### 1. 需求目标明确且可衡量
- 检查点：是否有清晰的业务目标和成功指标
- 不通过标准：目标描述为"提升用户体验"等无法量化的表述
- 通过标准：有具体数值或可观测的行为变化作为衡量依据

### 2. 用户路径完整覆盖主流程和异常流程
- 检查点：用户故事是否覆盖 happy path + edge cases + error handling
- 不通过标准：只有正常流程，无异常处理描述
- 通过标准：每个核心流程至少有 1 个异常路径描述

### 3. 业务域划分合理，无遗漏
- 检查点：Domain ID 是否覆盖所有功能模块，粒度是否适中
- 不通过标准：存在功能点无法映射到任何 Domain ID
- 通过标准：所有功能点可追溯到 Domain ID，且无过粗/过细问题

### 4. AC 可验证、可测试
- 检查点：验收标准是否使用 Given/When/Then 格式，是否可自动化测试
- 不通过标准：AC 描述为"系统正常工作"等无法测试的表述
- 通过标准：每条 AC 可直接转化为测试用例

### 5. 非功能需求有量化指标
- 检查点：性能/安全/可用性是否有具体数值
- 不通过标准："响应要快"、"要安全"等无量化表述
- 通过标准：有具体数值（如"P95 响应时间 < 200ms"）

### 6. 约束和假设已确认
- 检查点：技术约束、业务约束、假设是否已记录并标注风险
- 不通过标准：存在未标注的隐含假设
- 通过标准：所有假设已列出，且标注了依据和风险等级

### 7. 待确认问题已清零或标注为 P2
- 检查点：待确认问题清单中是否有阻塞项
- 不通过标准：存在未解决的阻塞性问题
- 通过标准：所有阻塞问题已解决，剩余问题均为 P2 且不影响开发启动

### 8. 需求资料与文档内容一致
- 检查点：requirements.md 内容是否与原始资料（PRD/设计稿/原型）一致
- 不通过标准：文档描述与原始资料存在矛盾
- 通过标准：所有内容可追溯到原始资料，无自相矛盾

## Process (评审流程)

```
1. 读取 requirements.md，确认 stage_status 为 ready
   verify: 文件存在且 frontmatter 完整
2. 逐条执行 Review Checklist（8 项全部检查）
   verify: 每条有明确的 通过/不通过 判定
3. 对不通过项进行问题分级（Critical / Major / Minor）
   verify: 每个问题有分级和修改建议
4. 汇总评审结果，撰写评审摘要
   verify: 摘要准确反映整体质量
5. 写入 review-requirement.md
   verify: frontmatter 和所有章节完整
6. 向用户呈现评审结果，等待用户决定
   verify: 用户给出明确的通过/不通过/需修改
7. 根据用户决定更新 review_status
   verify: 状态与用户决定一致
```

## Severity Classification (问题分级标准)

### Critical（必须修复，阻塞通过）

- 核心业务逻辑缺失或矛盾
- 验收标准无法测试或存在歧义
- 安全相关需求缺失（认证/授权/数据保护）
- 需求范围无边界，存在无限蔓延风险
- 不同章节对同一功能描述矛盾

### Major（应当修复，影响质量）

- 异常流程覆盖不完整
- 非功能需求缺少量化指标
- Domain ID 粒度不当（过粗或过细）
- 假设未标注风险等级
- 用户路径存在断点（某步骤后无后续描述）

### Minor（建议修复，不阻塞）

- 文档格式不规范
- 描述可以更精确但不影响理解
- 优先级标注缺失但功能边界清晰
- 术语使用不一致但含义明确
- 资料索引不完整但核心资料已覆盖

## Output: review-requirement.md (产物结构)

### Frontmatter

```yaml
---
stage: ship-intake-review
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""  # 用户身份
reviewed_at: ""
requirement_version: ""  # 对应 requirements.md 的版本/更新时间
---
```

### 核心章节

```markdown
## 1. 评审摘要

[一句话结论：本次评审的整体判定及核心发现]

## 2. 评审 Checklist

- [x/×] 需求目标明确且可衡量 — [判定理由]
- [x/×] 用户路径完整覆盖主流程和异常流程 — [判定理由]
- [x/×] 业务域划分合理，无遗漏 — [判定理由]
- [x/×] AC 可验证、可测试 — [判定理由]
- [x/×] 非功能需求有量化指标 — [判定理由]
- [x/×] 约束和假设已确认 — [判定理由]
- [x/×] 待确认问题已清零或标注为 P2 — [判定理由]
- [x/×] 需求资料与文档内容一致 — [判定理由]

## 3. 发现的问题

### Critical
- [C-001] [问题描述] | 影响范围: [xxx] | 关联 Domain ID: [xxx]
- ...

### Major
- [M-001] [问题描述] | 影响范围: [xxx] | 关联 Domain ID: [xxx]
- ...

### Minor
- [m-001] [问题描述] | 影响范围: [xxx]
- ...

## 4. 修改建议

| 问题编号 | 建议修改方案 | 优先级 | 预计影响范围 |
|---------|------------|--------|------------|
| C-001   | [具体建议]  | 必须   | [涉及章节]  |
| M-001   | [具体建议]  | 建议   | [涉及章节]  |

## 5. 用户签字

- 评审结论：[pending / approved / rejected / revision_needed]
- 用户确认原话："[用户原话]"
- 确认时间：[timestamp]
```

## Revision Loop (修改-重审循环)

当 `review_status` 为 `revision_needed` 或 `rejected` 时：

```
1. 将问题清单传递给 ship-intake 阶段
2. 在 requirements.md 中修复所有 Critical 问题（Major 视情况）
3. 更新 requirements.md 的 updated_at 时间戳
4. 重新进入 ship-intake-review，执行完整评审流程
5. 不可只检查"修改的部分"，必须全量重审
```

### 循环次数限制

- 建议最多 3 轮修改-重审循环
- 超过 3 轮仍有 Critical 问题，需要升级讨论：
  - 是否需求本身不可行？
  - 是否需要拆分为更小的需求范围？
  - 是否需要引入更多 stakeholder？

## Anti-Rationalizations

1. **"这个问题不严重，先过了再说"** —— Critical 问题没有"先过了再说"。现在不修，后面改的成本是 10 倍。评审门禁存在的意义就是在这里拦住问题。
2. **"用户催得急，赶紧通过吧"** —— 时间压力不是降低质量标准的理由。如果时间紧，应该裁剪范围（Out of Scope），而不是放过有缺陷的需求。
3. **"这条 checklist 对这个项目不适用"** —— 每条都必须检查。如果确实不适用，在判定理由中写明"不适用，原因：xxx"，而不是跳过。
4. **"用户说差不多就行"** —— "差不多"不是明确批准。必须引导用户给出明确的"通过/approved"或指出具体不满意的地方。
5. **"只改了一点点，不用全量重审"** —— 修改可能引入新的不一致。全量重审是保证质量的底线，不可省略。

## Red Flags

以下情况出现时，必须标记为 Critical 并阻塞通过：

- **需求目标自相矛盾**：如"既要极致性能又要零成本" → 要求明确优先级取舍
- **验收标准无法转化为测试用例**：如"系统应该智能地处理" → 要求具体化
- **安全需求完全缺失**：涉及用户数据但无认证/授权/加密描述 → 必须补充
- **范围边界模糊**：无明确的 Out of Scope 列表 → 要求划定边界
- **关键依赖未确认**：依赖第三方 API 但无接口文档或确认 → 标记为阻塞

## Verification (退出 Checklist)

在完成评审并获得用户确认后，执行以下检查：

```markdown
## 退出检查

- [ ] Review Checklist 8 项全部已检查（无跳过）
- [ ] 每个不通过项有明确的问题分级（Critical/Major/Minor）
- [ ] 每个问题有具体的修改建议
- [ ] review-requirement.md 的 frontmatter 字段完整
- [ ] review_status 与用户明确表态一致
- [ ] 如果 approved：无未解决的 Critical 问题
- [ ] 如果 revision_needed：问题清单已明确传递给 requirement-intake
- [ ] 用户签字章节有用户原话记录
```

### review_status 判定规则

| 条件 | status |
|------|--------|
| 评审未开始或进行中 | `pending` |
| 无 Critical 问题 + 用户明确说"通过/approved" | `approved` |
| 用户明确说"不通过/rejected" | `rejected` |
| 存在 Critical 问题，需修改后重审 | `revision_needed` |
| 用户表态模糊 | 保持 `pending`，继续引导确认 |
