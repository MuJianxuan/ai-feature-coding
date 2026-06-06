---
name: ship-define-review
description: "ShipKit hard gate. Reviews requirements for completeness and correctness. Produces review-define.md. Use after ship-define completes."
---

# 需求评审 (Requirement Review)

## Overview

需求评审是开发工作流的第二个阶段，是一个**硬门禁 (Hard Gate)** 阶段。本阶段对 `requirements.md` 进行结构化评审，发现遗漏、矛盾、模糊点，确保需求质量达到可进入设计阶段的标准。

核心目标：
- 逐条检查需求的完整性、一致性、可验证性
- 发现并分级问题（Critical / Major / Minor）
- 确保所有 Critical 问题在通过前修复
- 产出 `review-define.md` 作为硬门禁产物
- 用户必须明确批准才能放行

**硬门禁含义**：此阶段不可跳过、不可自动通过。必须有用户明确的"通过/批准/approved"才能标记为 approved，进入下一阶段。

## When to Use

- `requirements.md` 的 `stage_status` 为 `ready`，需求定义已完成
- 需求变更后需要重新评审
- 从 revision_needed 状态修改后重新提交评审

## When NOT to Use

- `requirements.md` 尚未完成（`stage_status: draft`）—— 先完成需求定义
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
│                    返回 ship-define 修改            │
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

## Delegation Boundary

本阶段的质量门禁检查执行者由 orchestrator 基于 delegation 配置决定：

- `current_context`：主代理直接执行需求评审并写 `review-define.md`
- `gate_check_subagent`：子代理执行需求评审并直接写正式 `review-define.md` 草案

配置解释：

- `node_overrides[ship-define-review]` 优先于 `delegation.default_mode`
- `assistive_subagent` 在本阶段解释为 `gate_check_subagent`
- `parallel_subagent` 在本阶段无效；记录 warning 后回退到 `default_mode`，仍无法解析则回退 `current_context`

约束：

- 若由子代理起草，frontmatter 中的 `review_status` 必须保持 `pending`
- 若由子代理起草，`user_sign_off`、`signed_at` 必须保持为空
- 主代理必须重新读取正式草案、复核检查结果并按需要修订
- 只有主代理可以把 `review_status` 改成 `approved / rejected / revision_needed`
- 子代理不可替用户做 `approved / rejected / revision_needed` 决策

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

### 模式判定

评审开始前，检查 `requirements.md` 的 `generation_mode` 字段：

- `generation_mode: prd_direct` → 执行 **PRD Direct 评审流程**（含 PRD 源文件质量审核 + 提取准确性审核 + 标准 Checklist）
- `generation_mode: technical_plan` → 仅对旧 feature 或用户显式手动整理的 technical plan requirements 执行 **技术方案选区评审流程**；新建 `technical_plan_provided` 默认跳过本 gate，直接由 `ship-tech-discovery` 派生最小 requirements index
- 其他（无此字段或 `interview`）→ 执行标准评审流程

### 标准评审流程

```
1. 读取 requirements.md，确认 stage_status 为 ready
   verify: 文件存在且 frontmatter 完整
2. 逐条执行 Review Checklist（8 项全部检查）
   verify: 每条有明确的 通过/不通过 判定
3. 对不通过项进行问题分级（Critical / Major / Minor）
   verify: 每个问题有分级和修改建议
4. 汇总评审结果，撰写评审摘要
   verify: 摘要准确反映整体质量
5. 写入 review-define.md
   verify: frontmatter 和所有章节完整
6. 向用户呈现评审结果，等待用户决定
   verify: 用户给出明确的通过/不通过/需修改
7. 根据用户决定更新 review_status
   verify: 状态与用户决定一致
```

### PRD Direct 评审流程

当 `generation_mode: prd_direct` 时，评审分三个阶段执行：

```
Phase 1: PRD 源文件质量审核
  ↓
Phase 2: 提取准确性审核
  ↓
Phase 3: 标准 Checklist（8 项）
  ↓
汇总 → 呈现 → 用户确认
```

#### Phase 1: PRD 源文件质量审核

读取 `source_documents` 中列出的所有源文件，逐项检查：

| # | 检查项 | 通过标准 | 不通过标准 |
|---|--------|----------|-----------|
| P1-1 | 材料齐全性 | PRD + 原型/设计稿均存在且可读 | 缺少关键文件（如有原型但无 PRD） |
| P1-2 | 功能覆盖完整性 | PRD 覆盖了原型中所有可见页面/功能 | 原型中有页面但 PRD 未提及 |
| P1-3 | 内容无歧义 | 同一功能在 PRD 和原型中描述一致 | PRD 文字与原型交互存在矛盾 |
| P1-4 | 非功能需求可执行 | 有量化指标或明确的技术约束 | 仅有"要快"/"要安全"等模糊表述 |
| P1-5 | 角色/权限明确 | 角色定义清晰，权限边界可判定 | 角色描述模糊或权限未覆盖关键操作 |

Phase 1 发现的问题归入 Critical 或 Major（视影响范围）。

#### Phase 2: 提取准确性审核

对照 PRD 源文件，检查 requirements.md 中的提取结果：

| # | 检查项 | 通过标准 | 不通过标准 |
|---|--------|----------|-----------|
| P2-1 | Domain ID 映射准确 | 每个 Domain ID 对应 PRD 中一个明确的功能模块 | Domain ID 与 PRD 模块不对应或遗漏模块 |
| P2-2 | AC 忠实反映需求 | AC 的 Given/When/Then 准确表达了 PRD 中的需求条目 | AC 曲解或遗漏了 PRD 中的关键需求 |
| P2-3 | 引用位置正确 | 标注的"PRD §X.X"/"原型 page-N"与实际位置对应 | 引用位置错误或不存在 |
| P2-4 | [GAP] 标记合理 | 标记的缺口确实在 PRD 中找不到对应信息 | 将 PRD 中已有的信息误标为 [GAP] |
| P2-5 | 无遗漏提取 | PRD 中的所有功能需求都有对应的 Domain ID 和 AC | PRD 中有需求但 requirements.md 中未体现 |

Phase 2 发现的问题归入 Major（提取错误）或 Minor（引用位置偏差）。

#### Phase 3: 标准 Checklist

执行与 interview 模式相同的 8 项 Checklist（见上方 Review Checklist 章节）。prd_direct 模式下的适配说明：

- Checklist 第 8 项"需求资料与文档内容一致"：重点检查引用是否准确，而非内容是否完整复制
- 若 requirements.md 中存在 `[GAP]` 标记，对应 Checklist 项按"已标注缺口"处理，不自动判定为不通过

### PRD Direct 修订回路

当 prd_direct 模式评审结果为 `revision_needed` 时：

```
1. 区分问题来源：
   - PRD 源文件质量问题 → 用户需补充/修改 PRD 源文件，然后重新执行 ship-define（prd_direct 模式）
   - 提取准确性问题 → 直接修改 requirements.md 或重新执行 ship-define（prd_direct 模式）
2. 修改完成后重新进入 ship-define-review，执行完整评审流程
3. 不可只检查"修改的部分"，必须全量重审
```

### 技术方案选区评审流程

当旧 feature 或手动整理产物使用 `generation_mode: technical_plan` 时，评审分三个阶段执行。新建 `technical_plan_provided` 入口不进入本评审流程，selected scope 边界和最小 AC 确认写入 `ship-tech-discovery` 的 Research Alignment Check。

```
Phase 1: selected scope 边界审核
  ↓
Phase 2: 最小 AC 与用户确认审核
  ↓
Phase 3: 标准 Checklist（8 项）
  ↓
汇总 → 呈现 → 用户确认
```

检查项：

| ID | 检查项 | 通过标准 | 不通过标准 |
|----|--------|----------|------------|
| TP-1 | selected scope 明确 | `source_documents` 或等价来源索引指向技术方案文件/片段和章节、接口、模块或标题 | selected scope 缺失、不可定位，或只写“按方案” |
| TP-2 | 未选中内容未被错误纳入 | In Scope / Domain / AC 只覆盖 selected scope；未选中内容在 Out of Scope 或资料索引中说明 | 未选中章节、接口或模块进入本期 scope |
| TP-3 | AC 覆盖 selected scope | 每个 selected scope 关键结果至少有一条 AC，且 AC 可测试 | 只有实现步骤，没有用户可验收结果 |
| TP-4 | 既有项目前提确认 | meta.yml 为 `technical_plan_provided` 时 `project_context: existing_project`，后续需要 Project Reality Scan | 试图把技术方案选区用于新项目 |
| TP-5 | 最小 AC 草案需用户确认 | 由 agent 推导的 AC 标为待确认；未确认时不得 ready | 推导 AC 被当作已确认事实 |

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

## Output: review-define.md (产物结构)

### Frontmatter

```yaml
---
stage: ship-define-review
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""  # 用户身份
reviewed_at: ""
reviewed_documents: ["requirements.md"]  # prd_direct 模式下追加源文件: ["requirements.md", "resource/prd.docx", "resource/prototype.html"]
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
requirement_version: ""  # 对应 requirements.md 的版本/更新时间
generation_mode: ""  # 从 requirements.md 继承: interview | prd_direct
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

- 建议结论：[recommended_status: approved / rejected / revision_needed]
- 正式评审状态：[pending / approved / rejected / revision_needed]
- 用户确认原话："[用户原话]"
- 确认时间：[timestamp]
```

## Revision Loop (修改-重审循环)

当 `review_status` 为 `revision_needed` 或 `rejected` 时：

### Interview 模式（默认）

```
1. 将问题清单传递给 ship-define 阶段
2. 在 requirements.md 中修复所有 Critical 问题（Major 视情况）
3. 更新 requirements.md 的 updated_at 时间戳
4. 重新进入 ship-define-review，执行完整评审流程
5. 不可只检查"修改的部分"，必须全量重审
```

### PRD Direct 模式

```
1. 区分问题来源（见 PRD Direct 修订回路）
2. PRD 质量问题 → 用户补充 PRD → 重新执行 ship-define（prd_direct 模式）
3. 提取准确性问题 → 直接修改 requirements.md 或重新执行 ship-define（prd_direct 模式）
4. 更新 requirements.md 的 updated_at 时间戳
5. 重新进入 ship-define-review，执行完整评审流程
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
- [ ] review-define.md 的 frontmatter 字段完整
- [ ] 等待用户批准时 review_status 保持 pending，正文已记录 recommended_status
- [ ] 若 review_status 为 approved，已一次性写入用户明确批准、user_sign_off 和 signed_at
- [ ] 如果 approved：无未解决的 Critical 问题
- [ ] 如果 revision_needed：问题清单已明确传递给 `ship-define`
- [ ] 用户签字章节有用户原话记录
```

### review_status 判定规则

| 条件 | status |
|------|--------|
| 评审未开始或进行中 | `pending` |
| 无 Critical 问题，但尚未获得用户明确批准 | `pending`，正文记录 `recommended_status: approved` |
| 无 Critical 问题 + 用户明确说"通过/approved" | `approved`，并同时写入 `user_sign_off` 与 `signed_at` |
| 用户明确说"不通过/rejected" | `rejected` |
| 存在 Critical 问题，需修改后重审 | `revision_needed` |
| 用户表态模糊 | 保持 `pending`，继续引导确认 |
