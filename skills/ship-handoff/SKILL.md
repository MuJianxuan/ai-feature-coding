---
name: ship-handoff
description: "ShipKit stage. Consumes verification.md from ship-verify, completes AC acceptance, and produces delivery summary."
---

# 实施验收 (Acceptance)

## Overview

实施验收是开发工作流的最终阶段，负责消费 `ship-verify` 产出的 `verification.md`，对照 requirements.md 中的 Acceptance Criteria (AC) 做最终验收，评估残余风险，并产出交付总结。核心原则：**每条 AC 必须有可追溯的验证证据，未通过项必须显式记录而非隐藏**。

核心目标：
- AC 全量映射验证：每条 AC 对应至少一项验证证据
- 残余风险显式登记：FAIL / BLOCKED 项不能藏起来
- 交付边界清晰：变更范围、部署事项、后续建议形成可移交文档
- 规范沉淀闭环：汇总本次引用过的规范，并以 Proposal-First 方式记录新增规范建议

产物：
- `verification.md` —— 共享验收证据文件；本阶段补齐 AC 映射、手工验证、残余风险与最终结论
- `handoff.md` —— 交付摘要与移交清单

## When to Use

- `ship-verify` 已完成，且 `verification.md.stage_status = ready`
- 进入用户/QA 验收前的最后一道闸口
- 需要向团队/客户交付一个完整可审计的实施记录时

## When NOT to Use

- `ship-verify` 尚未将 `verification.md` 置为 `ready` —— 自动化验证未完成谈不上验收
- 仅是临时实验/原型 —— 不进入正式交付链路
- 需要跨需求合并验收 —— 应分别验收后再做集成验收

## AC Mapping Protocol

### 映射强制规则

1. **AC 不漏**：requirements.md 中的每条 AC 都必须出现在映射表中
2. **证据不空**：每条 AC 必须至少绑定一项可追溯证据（测试 ID、命令输出、截图、代码引用）
3. **结果分级**：PASS / FAIL / BLOCKED / N/A 四态显式标注，禁止灰色"基本可用"
4. **N/A 必须解释**：出现 N/A 时必须写明原因（例如 AC 涉及尚未上线的依赖）

### AC ID 引用规则

- 每条 AC 在 requirements.md 中已有 ID（推荐格式 `AC-{Domain}-{NNN}`）
- verification.md 中按相同 ID 引用，便于跨文档跳转
- 若 AC 在 `ship-verify` 中被拆分为多个测试用例，需在证据列中列出所有相关用例

## Process

```
┌──────────────────────────────────────────────────────┐
│              实施验收流程                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 读取 requirements.md，提取所有 AC                  │
│         │                                            │
│         ▼                                            │
│  2. 读取 verification.md（由 ship-verify 生成）          │
│         │                                            │
│         ▼                                            │
│  3. 对每条 AC 执行映射                                 │
│      ├── 自动化测试覆盖？ → 引用测试 ID                │
│      ├── 手工验证覆盖？  → 记录步骤与结果              │
│      └── 未覆盖？        → 标 BLOCKED 并补验证         │
│         │                                            │
│         ▼                                            │
│  4. 收集证据（命令输出 / 截图 / 文件引用）             │
│         │                                            │
│         ▼                                            │
│  5. 评估残余风险（FAIL / BLOCKED / 未覆盖场景）        │
│         │                                            │
│         ▼                                            │
│  6. 生成 spec proposal（如有）                        │
│         │                                            │
│         ▼                                            │
│  7. 编写 handoff.md（变更范围、部署、建议）            │
│         │                                            │
│         ▼                                            │
│  8. 自检（Verification Checklist）                    │
│         │                                            │
│         ▼                                            │
│  9. 设置 stage_status（complete 或 draft）             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 步骤详解

**Step 1-2: 上下文准备**
- 提取 requirements.md 中所有 AC，建立完整列表
- verification.md 已有测试章节（来自 `ship-verify`），在此基础上扩展 AC 映射和验收结论
- 不放过任何一条 AC，包括非功能 AC（性能、安全、可访问性）

**Step 3: AC 映射**
- 优先匹配自动化测试（最强证据）
- 自动化未覆盖的，组织手工验证流程
- 手工验证也无法完成的（依赖未就绪、环境缺失），标 BLOCKED

**Step 4: 证据收集**
- 测试证据：测试 ID + 测试运行命令输出片段
- 命令证据：命令本身 + 关键输出
- 视觉证据：截图文件路径 + 简短描述
- 代码证据：文件路径 + 行号区间

**Step 5: 残余风险评估**
- 列出所有 FAIL / BLOCKED 的 AC
- 评估影响（用户影响 / 业务影响 / 安全影响）
- 给出处理建议（修复 / 接受 / 回退）

**Step 6: Spec Proposal**
- 读取 `meta.yml.spec_context.referenced_spec_ids`
- 若发现重复模式、临时约定或 review 中反复出现的问题，生成待沉淀 proposal
- proposal 摘要先写入 `meta.yml.spec_context.pending_proposals`
- 详细 proposal 在 Step 7 编写 `handoff.md` 时落盘
- 默认不直接创建或修改 `.docs/spec/*.md`

**Step 7: 交付文档**
- handoff.md 即使没有变更/部署事项，也要显式写"无"
- 后续建议要具体（哪个文件、哪个模块、什么时机），不要泛泛"建议优化性能"

**Step 8-9: 自检与状态设定**
- 完成 Verification Checklist
- `stage_status: complete` 仅当 Checklist 全部通过
- 否则维持 `draft`，列出待补项

## Delegation Boundary

本阶段只允许**证据收集型辅助委派**。

允许委派的子任务：
- 按 AC 分组搜集测试证据、命令输出、截图和代码引用
- 整理部署事项原材料
- 梳理 spec proposal 候选

对应的 canonical `node_id`：
- `ship-handoff.ac-evidence`
- `ship-handoff.deploy-materials`
- `ship-handoff.spec-proposals`

禁止委派的动作：
- 最终判定 AC 是 `PASS / FAIL / BLOCKED / N/A`
- 最终判定 P0/P1/P2/P3 风险级别
- 直接把 `verification.md.stage_status` 置为 `complete`
- 替用户做 close / follow-up / proposal 取舍
- 不直接编辑 `handoff.md` / `verification.md` 正文或 frontmatter

## Verification Evidence Standards

### 证据类型与质量分级

| 类型 | 强度 | 适用场景 | 记录格式 |
|------|------|---------|---------|
| 自动化测试 | 强 | 可重复验证 | `test_id` + 套件名称 + 通过状态 |
| 命令输出 | 中强 | CLI 工具/构建/部署 | 命令 + 关键输出片段 |
| 截图 | 中 | UI 行为、视觉效果 | 文件路径 + 描述 |
| 代码引用 | 中弱 | 文档/配置类 AC | `file:line` 引用 |
| 口头确认 | 弱 | 仅作辅助，不能单独使用 | 谁在何时确认了什么 |

### 证据组合原则

- UI 类 AC：自动化测试 + 截图
- 数据类 AC：自动化测试 + 命令输出（DB 查询）
- 性能类 AC：基准测试输出 + 数值对比
- 安全类 AC：自动化测试 + 安全扫描报告
- 可访问性 AC：自动化检查 + 手工辅助技术验证

## Risk Assessment

### 残余风险分类

```
P0 (Blocker): AC 失败，影响核心功能上线
  → 必须修复或显式延期，并与用户对齐

P1 (High):   AC 失败，影响非核心功能
  → 建议修复，否则在 handoff 标注为"已知缺陷"

P2 (Medium): 未覆盖场景，潜在风险但无证据
  → 列入"后续建议"，分配 owner

P3 (Low):    优化建议、非功能性改进
  → 列入"后续建议"，无需立即行动
```

### 风险登记格式（在 verification.md 中）

```markdown
## 残余风险

### R-001 [P0] AC-AUTH-003 未通过
- 描述：登录失败 5 次后未触发账户锁定
- 影响：安全风险，可能被暴力破解
- 当前状态：FAIL
- 建议：在 `ship-build` 阶段补充锁定逻辑后重新验收
- Owner: TBD

### R-002 [P1] AC-ORD-007 BLOCKED
- 描述：订单导出 PDF 功能依赖第三方服务，测试环境未配置
- 影响：用户无法导出订单
- 当前状态：BLOCKED
- 建议：协调 ops 配置测试环境后补验收
- Owner: ops-team
```

## Output: verification.md + handoff.md

### verification.md Frontmatter

```yaml
---
stage: ship-handoff
stage_status: ready  # ship-verify 结束时应为 ready；ship-handoff 完成后改为 complete 或回退为 draft
updated_at: ""
all_ac_verified: false  # 所有 AC 都有明确结果（含 N/A）则为 true
spec_checked_at: ""
referenced_spec_ids: []
spec_warnings: []
---
```

### verification.md 核心章节

**1. AC 映射表**（核心产物，每条 AC 一行）

| AC ID | 描述 | 验证方式 | 结果 | 证据 |
|-------|------|---------|------|------|
| AC-AUTH-001 | 邮箱密码可登录 | 自动化 E2E | PASS | `e2e/auth.spec.ts:12` |
| AC-AUTH-003 | 5 次失败后锁定 | 自动化单元 | FAIL | `auth.test.ts:80` |
| AC-PERF-001 | P95 < 300ms | 基准测试 | PASS | `bench-results.txt`（实测 245ms） |

**2. 自动化测试结果汇总**：分类列出各测试套件 passed/failed/覆盖率

**3. 手工验证记录**：每项含 验证人 / 时间 / 步骤 / 结果 / 证据文件

**4. 未覆盖场景**：列出明确不验证的场景及原因（范围外、依赖未就绪等）

**5. 残余风险**：见 Risk Assessment 章节格式

**6. Spec Proposals**：列出“无新增规范”或待沉淀 proposal（proposal_id / target_spec_id / summary）

### handoff.md 核心章节

**1. 交付摘要**：一段话说清涉及需求、AC 通过率、已知缺陷、可上线阶段

**2. 变更范围**：列出新增 / 修改 / 删除的文件清单（与 git diff 一致）

**3. 部署事项**：四个子项必须显式存在，无内容时写"无"
- 环境变量（新增/修改的 env 字段）
- 数据库迁移（migration 文件 + 是否可逆）
- 配置变更（配置文件、Feature Flag）
- 第三方依赖（新增 SDK / 服务 / 二进制依赖）

**4. 后续建议**：每条带优先级 + owner（可 TBD）
```
- [P0] 补齐 AC-AUTH-003 账户锁定逻辑（owner: 后续迭代）
- [P2] AuthService 魔法数字提取到 config（owner: TBD）
```

**5. Spec Proposals**：记录本次是否产生规范沉淀建议；若产生，需与 `meta.yml.spec_context.pending_proposals` 一致

## Anti-Rationalizations

1. **"这条 AC 测过了，不用再写证据"** —— 验收文档的价值在可审计，不是"我测过了"。证据是给未来的自己和团队看的。
2. **"FAIL 项太敏感，先不写吧"** —— 隐藏失败比承认失败的代价大得多。残余风险登记是诚实交付的底线。
3. **"handoff 没什么变化，不用写"** —— 即使没有部署事项，也要显式写"无"。空白与"已确认无"是两种语义。
4. **"AC 太细了，合并几条吧"** —— AC 是用户的契约，不是开发的工作量度量。逐条映射才能逐条交代。
5. **"覆盖率 80% 就算 AC 都过了"** —— 覆盖率是行级度量，AC 是行为级要求。两者不能互相替代。

## Red Flags

以下情况必须暂停处理：

- **存在未映射的 AC**：requirements.md 有但 verification.md 没出现的 AC
- **PASS 但无证据**：标 PASS 却找不到对应的测试 ID 或命令输出
- **N/A 无解释**：直接标 N/A 不说明原因
- **FAIL 项数 > 总 AC 的 20%**：实施质量明显不达标，回到 `ship-build` 阶段
- **handoff 中部署事项与代码改动不匹配**：例如新增了环境变量但 handoff 没列出
- **all_ac_verified=false 但 stage_status=complete**：状态机被破坏
- **存在待沉淀模式但 handoff / meta 没有 proposal**：规范闭环失效

## Verification (退出 Checklist)

设置 `stage_status: complete` 之前逐项确认：

```markdown
## 实施验收退出检查

### AC 完整性
- [ ] requirements.md 中每条 AC 都出现在 verification.md 的映射表
- [ ] 每条 AC 都有 PASS / FAIL / BLOCKED / N/A 明确结果
- [ ] 每条 PASS 的 AC 都有可追溯证据
- [ ] 所有 N/A 项都附带解释
- [ ] 所有 FAIL / BLOCKED 项都登记到残余风险

### 证据质量
- [ ] 自动化测试证据引用了具体测试 ID 或文件位置
- [ ] 手工验证证据包含步骤、时间、验证人
- [ ] 视觉证据文件可访问（路径正确）

### 交付文档
- [ ] handoff.md 包含交付摘要、变更范围、部署事项、后续建议
- [ ] 部署事项即使为空也显式写"无"
- [ ] 变更文件清单与实际 git diff 一致
- [ ] 后续建议条目带优先级与 owner（可为 TBD）
- [ ] handoff.md 已记录“无新增规范”或完整 spec proposal

### 风险登记
- [ ] 所有 P0 风险已与用户对齐处理方案
- [ ] P1 风险列入 handoff 的"已知缺陷"
- [ ] P2/P3 风险列入"后续建议"

### 规范沉淀
- [ ] 已读取 `meta.yml.spec_context.referenced_spec_ids`
- [ ] 若发现可沉淀模式，proposal 已同步写入 `meta.yml.spec_context.pending_proposals`
- [ ] 未经用户确认，不直接修改 `.docs/spec/*.md`

### Frontmatter
- [ ] stage_status 与实际验收结果一致
- [ ] all_ac_verified 字段已正确填写
- [ ] updated_at 已更新
```

### stage_status 判定规则

| 条件 | status |
|------|--------|
| `ship-verify` 产物不完整或 `verification.md` 未达到 `ready` | `draft` |
| 存在 P0 残余风险且未与用户对齐 | `draft` |
| 存在未映射的 AC | `draft` |
| AC 全部 PASS / N/A 已解释，FAIL/BLOCKED 已登记并对齐 | `complete` |
