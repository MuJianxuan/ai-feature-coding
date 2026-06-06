---
name: ship-define
description: "ShipKit stage 1 (Define). Parses requirement materials (PRD, prototypes, UI/UX designs, Figma) into structured requirements. Use when starting a new feature or when requirement materials are provided."
---

# 需求定义 (Requirement Define)

## Overview

需求定义是开发工作流的第一个阶段，负责将用户提供的各类需求资料（PRD、原型图、UI/UX 设计稿、Figma 链接、墨刀链接、会议纪要等）解析为结构化的需求文档。

核心目标：
- 消除需求模糊性，将"我大概想要..."转化为可验证的需求条目
- 建立 Domain ID 体系，为后续所有阶段提供统一引用锚点
- 识别隐含需求，避免开发中后期才发现遗漏
- 产出标准化的 `requirements.md`，作为后续设计与开发的唯一需求源

## When to Use

- 用户提供了新功能的 PRD / 原型 / 设计稿 / Figma 链接
- 用户口头描述了一个新需求，需要结构化整理
- 项目启动阶段，需要从零梳理需求
- 需求变更时，需要更新已有 requirements.md

## When NOT to Use

- 需求已经有完整的 requirements.md 且状态为 `ready` —— 直接进入下一阶段
- 纯 bug 修复 —— 使用 debugging 流程
- 纯技术重构且无功能变更 —— 直接进入技术设计阶段
- 用户只是想讨论方案可行性 —— 使用 brainstorming

## Input Materials (支持的输入类型)

| 类型 | 格式 | 处理方式 |
|------|------|----------|
| product-brief.md | 来自 ship-discover | 直接采纳为业务背景、方案选择、范围、成功标准章节；跳过开放式探索 |
| design-brief.md + resource/wireframes/ | 来自 ship-shape | 等同 Figma/原型输入；解析页面清单、用户流程、交互注释 |
| PRD 文档 | .md / .docx / .pdf / .notion | 逐章节解析，提取功能点与验收标准 |
| raw requirements.md inbox | 用户直接粘贴完整 PRD 原文 | 先作为原始输入读取，normalize 后改写为结构化 requirements contract |
| 原型图 | Figma / 墨刀 / Axure / 图片 | 逐页面解析交互流程与状态 |
| UI/UX 设计稿 | Figma / Sketch / 图片 | 提取组件结构、交互规则、响应式断点 |
| 会议纪要 | 文本 / 音频转录 | 提取决策点、待确认项、优先级信息 |
| 口头描述 | 对话 | 通过结构化提问补全信息 |
| 竞品参考 | URL / 截图 | 标注"参考范围"与"差异点" |
| 已有代码 | 仓库路径 | 分析现有实现，识别扩展点与约束 |

### 上游产物的短路逻辑

当 feature 目录中存在 `product-brief.md` 或 `design-brief.md`（来自 ship-discover / ship-shape）时：

- **直接采纳已结构化的部分**：问题陈述、方案选择、范围、成功标准、设计 token、页面清单等已在上游定稿，不再做开放式提问
- **聚焦补全 define 特有的内容**：Domain ID 体系、AC（Given/When/Then）、非功能需求量化、约束的技术化展开
- **保留上游 Open Questions**：将 product-brief 中未解决的非阻塞问题转化为 define 的"约束与假设"或新一轮提问的起点
- **evolve 分支特殊处理**：若 product-brief.discovery_mode=evolve，将影响分析章节中的"受影响 AC"作为已有 AC 的修订基线，新增/修改/删除明确标注

### 范围拆分规则

`ship-define` 不应把多个独立项目硬塞进一份 `requirements.md`。在进入正式澄清前，先判断输入是否过大：

- 若需求包含多个独立用户群、业务目标、数据模型、交付节奏或验收口径，必须先拆分 feature，或要求用户确认本次只定义其中一个子范围。
- 若只是同一业务目标下的多个模块，可以保留在同一份 requirements.md，但必须通过 Domain ID 和 MoSCoW 标清模块边界。
- 被拆出的内容写入 Out of Scope / Future Considerations，不得混入 Must 范围。

## Execution Mode (执行模式)

`ship-define` 支持三种执行模式，由 `meta.yml.scenario` 决定：

| 模式 | 触发条件 | 行为 |
|------|----------|------|
| `interview`（默认） | scenario = greenfield / product_provided / evolve | 多轮采访 + 完整生成 requirements.md |
| `prd_direct` | scenario = prd_direct；用户提供完整 PRD + 原型且明确表示不需要需求录入 | 零提问、纯提取、产出索引式 requirements.md |
| `technical_plan`（兼容/手动） | 旧 feature 已停在 `ship-define`，或用户显式要求手动整理技术方案 selected scope | 只提取 selected scope 的最小 requirements / Domain / AC；新建 `technical_plan_provided` 默认由 `ship-tech-discovery` 开头派生 |

`requirements.md` 在 PRD 直通和产品提供入口中可能先由 `ship-orchestrator` 初始化为 raw PRD inbox。该状态下它只是原始输入，不是下游 contract；本阶段必须先执行 normalize，将 raw PRD 原文迁移或保留到 `resource/raw-prd.md`，再把 `requirements.md` 改写为结构化需求文档。

### 模式检测逻辑

在 Process 开始前，检查 `meta.yml.scenario`：

1. 若 `requirements.md` 是 raw PRD inbox → 先执行 [Raw Inbox Normalize](#raw-inbox-normalize)
2. 若 `scenario: prd_direct` → 跳转到 [PRD Direct Mode](#prd-direct-mode) 执行
3. 若 `generation_mode: technical_plan` 且当前 feature 已停在 `ship-define`，或用户显式要求手动整理技术方案 selected scope → 跳转到 [Technical Plan Mode](#technical-plan-mode) 执行；新建 `scenario: technical_plan_provided` 默认不进入本阶段
4. 否则 → 走下方标准 interview 流程

---

## Process (Interview Mode)

```
┌─────────────────────────────────────────────────────────┐
│                  需求录入流程                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 接收资料 ──→ 2. 资料分类与预处理                       │
│       │                    │                            │
│       ▼                    ▼                            │
│  3. 逐模块深度解析 ──→ 4. 识别信息缺口                    │
│       │                    │                            │
│       │              ┌─────┴─────┐                      │
│       │              │ 阻塞缺口？  │                      │
│       │              └─────┬─────┘                      │
│       │               Y/  │  \N                         │
│       │              ▼     │   ▼                        │
│       │     5. 结构化提问  │  6. 标注假设                 │
│       │   (按模块循环至阻塞缺口清零) │                   │
│       │              │    │                             │
│       │              ▼    ▼                             │
│       └──────→ 7. 业务域建模 (Domain ID)                 │
│                        │                                │
│                        ▼                                │
│               8. 编写 requirements.md                    │
│                        │                                │
│                        ▼                                │
│               9. 自检 (Verification Checklist)           │
│                        │                                │
│                        ▼                                │
│              10. 输出 & 标记 stage_status                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 步骤详解

**Step 1-2: 接收与预处理**
- 确认所有资料已收集完整
- 按类型分类，建立 `resource/` 目录索引
- 对图片/链接类资料进行可访问性验证
- 若存在 raw `requirements.md` inbox，先完成 normalize，不允许把 raw PRD 原文直接当作已完成需求合同

**Step 3: 逐模块深度解析**
- 若存在上游产物（product-brief.md / design-brief.md）：直接采纳已结构化的章节，跳过开放式探索；本步骤聚焦补全 define 特有的内容（Domain ID、AC、NFR 量化）
- PRD：逐章节提取功能点，不能只看标题和摘要
- 原型 / wireframes：逐页面分析交互流程、状态变化、异常路径
- 设计稿 / design-brief.md：逐组件分析结构、交互规则、边界情况；design-brief 中的 Visual System token 作为前端设计约束传递给下游

**Step 4-6: 信息缺口处理**
- 识别缺失信息，区分"可合理假设"与"必须确认"
- 阻塞性缺口触发结构化提问（见下节），按模块/流程循环，直到阻塞缺口清零
- 非阻塞缺口可标注为假设，记入"约束与假设"章节，并说明依据、风险和影响范围
- 不允许因为提问轮次、时间压力或问题较多而跳过核心需求澄清

**Step 7: 业务域建模**
- 为每个业务实体/模块分配 Domain ID
- Domain ID 格式：`D-{模块缩写}-{序号}`，如 `D-AUTH-001`

**Step 8-10: 编写与输出**
- 按产物模板编写 requirements.md
- 执行 Verification Checklist
- 设置 `stage_status: draft` 或 `ready`

## Structured Questioning Protocol (澄清提问规则)

### 规则

1. **完整性优先，不设固定轮次上限**：持续澄清，直到所有阻塞性需求缺口清零；不能用轮次限制替代需求完整性。
2. **按模块/流程分批提问**：每轮聚焦一个业务模块、用户流程或风险主题，把该模块问完整；不要把多个无关模块混在一轮里。
3. **复杂决策给出 2-3 个选项**：当业务规则、范围裁剪、异常处理或优先级存在多种合理解释时，提出 2-3 个实质不同的选项，说明 trade-off，并给出推荐理由。
4. **问题必须具体**，不能问"你还有什么要补充的吗？"；每个问题必须指向明确的功能、规则、角色、状态、边界或验收结果。
5. **每个问题附带默认建议**，降低用户决策负担；默认建议必须说明依据，不能替用户决定核心业务规则。
6. **按风险优先级排序**：阻塞 `ready` 的问题优先，其次是会影响设计/开发拆分的问题，最后是可记录为低风险假设的问题。
7. **每轮结束后更新缺口状态**：把已确认答案写入需求理解，把剩余问题标注为阻塞/非阻塞，并说明对 `stage_status` 的影响。

### 完整性退出条件

只有同时满足以下条件，interview 模式才能停止澄清并允许 `stage_status: ready`：

- 每一项 In Scope 功能都有明确的业务规则、参与角色、主路径、关键异常路径和可验证 AC。
- 权限/角色、安全、数据一致性、范围边界、外部系统依赖等高风险问题没有未确认阻塞项。
- Domain ID 能覆盖所有功能模块，且每个 Domain ID 至少能绑定 1 条可测试 AC。
- 非功能需求至少覆盖性能、安全、可用性；缺少明确指标时，已记录默认值、依据和风险。
- 待确认问题清单中不存在阻塞项；剩余非阻塞问题均已标注假设、影响范围和后续确认方式。

禁止以下行为：

- 因为已经提问若干轮就停止澄清。
- 将核心业务逻辑、权限、安全、数据一致性、范围边界等阻塞问题降级为假设。
- 在阻塞问题未解决时把 `requirements.md.stage_status` 标记为 `ready`。

### 提问模板

```markdown
## 需求澄清 - 第 N 轮：[本轮聚焦模块/流程]

基于已有资料，我已确认：
- [已确认的关键需求事实]

本轮目标：
- [说明本轮要清零的模块/流程缺口]

### Q1: [具体问题]
- 背景：[为什么需要确认这个]
- 选项：
  - A. [选项名]：[适用场景 / 代价]
  - B. [选项名]：[适用场景 / 代价]
  - C. [可选]：[适用场景 / 代价]
- 建议：[推荐选项及理由；若是核心业务规则，要求用户明确确认]
- 影响范围：[如果不确认会影响什么]
- 阻塞级别：[阻塞 ready / 影响设计 / 可作为低风险假设]

### Q2: ...

回答后我会更新：
- requirements.md 中的章节：[章节名]
- 待确认问题清单：[会清零/新增/降级哪些问题]
- stage_status 影响：[是否仍保持 draft，或满足 ready 条件]
```

### 提问触发条件

| 缺失信息类型 | 是否必须提问 | 说明 |
|-------------|-------------|------|
| 核心业务逻辑 | 是 | 无法合理假设 |
| 范围边界 | 是 | In Scope / Out of Scope 不清会导致需求蔓延 |
| 权限/角色 | 是 | 安全相关，必须明确 |
| 安全/合规 | 是 | 涉及数据、认证、授权、审计时不可假设 |
| 数据一致性/状态流转 | 是 | 影响业务正确性和测试设计 |
| 外部系统依赖 | 是 | 缺少接口/责任边界会阻塞设计 |
| 验收标准缺失 | 是 | 无法验证则不能进入 ready |
| 边界条件/异常处理 | 视情况 | 核心流程相关异常必须提问；低风险 UI/文案异常可标注假设 |
| UI 细节 | 否 | 可参考设计稿或行业惯例，但影响主流程时必须提问 |
| 性能指标 | 视情况 | 有业务承诺或高并发风险时必须提问；否则可标注默认值、依据和风险 |

## Scope Control (YAGNI)

- 未被用户明确要求、且没有业务目标或成功指标支撑的功能，不得写入 Must。
- "以后可能需要"、"顺手做一下"、"看起来会有用"默认进入 Out of Scope / Future Considerations。
- 若某个扩展功能会显著影响数据模型、接口、权限或交付节奏，必须单独确认是否纳入本次范围；未确认前保持 draft 或移出本次范围。
- requirements.md 中的 Must 项必须能追溯到用户目标、输入材料或明确确认记录。

## Incremental Confirmation (大型需求分段确认)

当需求规模较大、涉及多个模块、或存在多个高风险业务规则时，不要等整份 requirements.md 写完才确认。按以下段落分批确认：

1. **目标与范围**：业务目标、成功指标、In Scope / Out of Scope、MoSCoW。
2. **核心流程与业务规则**：用户路径、关键状态、权限、异常路径、数据一致性。
3. **AC / NFR / 约束**：Given/When/Then、性能/安全/可用性、外部依赖、假设。

分段确认规则：
- 每段只确认已经有证据支撑或用户已回答的内容。
- 某段仍有阻塞问题时，继续围绕该段澄清；不要带着阻塞问题进入后续段落。
- 小型需求可以跳过显式分段确认，但仍必须执行完整性退出条件和自检。

## Delegation Boundary

本阶段只允许**辅助委派**，不允许把 `requirements.md` 的正式定稿分叉给多个子代理。

允许委派的子任务：
- 资料索引整理
- 外部链接/截图/原型可访问性检查
- 原始资料的初步摘录与证据归类

禁止委派的动作：
- 生成多个彼此独立的 Domain ID 体系
- 直接改写 `requirements.md.stage_status`
- 替用户回答“必须确认”的业务问题

主上下文负责：
- 统一需求理解
- 建立唯一的 Domain ID 体系
- 写出并定稿 `requirements.md`
- 合并所有辅助委派返回的证据包；子代理不直接编辑 `requirements.md` 正文或 frontmatter

## Output: requirements.md (产物结构说明)

### Frontmatter

```yaml
---
stage: ship-define
stage_status: draft  # draft → 待确认问题未清零; ready → 可进入下一阶段
generation_mode: interview  # interview | prd_direct；raw_prd_input 只允许出现在 normalize 前
source_documents: []        # technical_plan 模式必须引用 selected scope 来源位置
selected_scope: []          # technical_plan 模式必须列出本次选区
updated_at: "2026-05-22T00:00:00+08:00"
evidence_complete: false  # 所有资料是否已收集完整
---
```

### 核心章节

#### 1. 需求背景与目标
- 项目/功能背景（为什么要做）
- 业务目标（做了之后期望达到什么）
- 成功指标（如何衡量"做好了"）

#### 2. 用户故事 / 用户路径
- 格式：`As a [角色], I want [功能], so that [价值]`
- 附带用户路径流程图（关键路径 + 异常路径）

#### 3. 功能范围
- **In Scope**：本次必须实现的功能
- **Out of Scope**：明确不做的功能（避免范围蔓延）
- **MoSCoW 优先级**：Must / Should / Could / Won't

#### 4. 业务域建模
- Domain ID 列表及描述
- 实体关系图（如适用）
- 核心业务规则

#### 5. 验收标准 (Acceptance Criteria)
- 每条绑定 Domain ID
- 格式：`Given [前置条件], When [操作], Then [预期结果]`
- 覆盖正常路径 + 异常路径

#### 6. 非功能需求
- 性能：响应时间、并发量、数据量
- 安全：认证、授权、数据加密
- 可用性：可访问性、国际化、浏览器兼容

#### 7. 约束与假设
- 技术约束（已有技术栈、第三方依赖）
- 业务约束（合规、时间线）
- 假设（标注依据与风险）

#### 8. 待确认问题清单
- 格式：`[ ] Q-{序号}: [问题] | 影响: [High/Medium/Low] | 阻塞: [是/否]`
- `stage_status` 只有在所有阻塞问题清零后才能设为 `ready`

#### 9. 需求资料索引
- `resource/` 目录下的文件清单
- 外部链接（Figma / 墨刀 / Notion 等）
- 每项标注类型与状态（已解析 / 待解析）

## Domain Modeling Rules (业务域建模规则)

### Domain ID 命名规范

```
格式: D-{MODULE}-{NNN}
示例:
  D-AUTH-001  用户认证模块
  D-AUTH-002  权限管理
  D-ORD-001   订单创建
  D-ORD-002   订单状态流转
  D-PAY-001   支付处理
```

### 建模原则

1. **单一职责**：每个 Domain ID 对应一个内聚的业务概念
2. **边界清晰**：不同 Domain 之间的依赖关系必须显式标注
3. **可追溯**：后续所有文档（设计、计划、测试）通过 Domain ID 回溯到需求
4. **粒度适中**：
   - 太粗（整个"用户管理"一个 ID）→ 无法精确追踪
   - 太细（每个字段一个 ID）→ 管理成本过高
   - 合适粒度：一个 Domain ID 对应 1-3 个用户故事

### 实体关系标注

```markdown
## 实体关系

D-AUTH-001 (用户认证)
  ├── depends_on: D-AUTH-002 (权限管理)
  └── used_by: D-ORD-001 (订单创建)

D-ORD-001 (订单创建)
  ├── depends_on: D-AUTH-001 (用户认证)
  ├── depends_on: D-PAY-001 (支付处理)
  └── triggers: D-ORD-002 (订单状态流转)
```

## Anti-Rationalizations

1. **"需求文档太长没人看"** —— 结构化文档不是给人"通读"的，是给人"查阅"的。Domain ID 就是索引。
2. **"用户说的就是需求"** —— 用户说的是"想要什么"，需求分析要挖掘"真正需要什么"。隐含需求往往比显式需求更关键。
3. **"先做了再说，敏捷嘛"** —— 敏捷不是不做需求分析，是快速迭代需求分析。没有清晰需求的代码是技术债的温床。
4. **"这个需求很简单不用写文档"** —— "简单"是主观判断。写下来才能发现你以为简单的东西其实有 5 个边界条件。
5. **"设计稿就是需求"** —— 设计稿描述的是"长什么样"，不是"怎么运作"。交互逻辑、异常处理、数据流转都不在设计稿里。

## Red Flags

以下情况出现时，必须暂停并处理：

- **需求来源单一且无验证**：只有一个人口头描述，无任何书面资料 → 要求补充书面确认
- **核心业务逻辑存在矛盾**：不同资料对同一功能描述不一致 → 标记冲突，要求澄清
- **范围无边界**："把这个系统做出来" → 必须通过提问明确 In/Out of Scope
- **验收标准无法量化**："用户体验要好" → 转化为可测量指标
- **依赖外部系统但无接口文档**：→ 标记为阻塞项，要求提供或确认接口规格
- **时间线与范围明显不匹配**：→ 主动提出 MoSCoW 优先级裁剪建议

## Verification (退出 Checklist)

在标记 `stage_status: ready` 之前，必须逐项确认：

```markdown
## 退出检查

- [ ] 所有输入资料已逐页/逐模块解析（非仅标题级别）
- [ ] Domain ID 列表完整，覆盖所有功能模块
- [ ] 每个 Domain ID 至少有 1 条验收标准
- [ ] In Scope / Out of Scope 边界清晰
- [ ] MoSCoW 优先级已标注
- [ ] 隐含需求已识别并记录（至少审视过以下维度：权限、并发、异常、数据一致性）
- [ ] 待确认问题清单中无阻塞项（或已标注为 draft 状态）
- [ ] 非功能需求已覆盖（性能/安全/可用性至少各一条）
- [ ] 需求资料索引完整，所有引用资料可访问
- [ ] Must 范围内无未确认的扩展功能或"以后可能需要"功能
- [ ] 大型需求已完成目标与范围、核心流程与业务规则、AC/NFR/约束的分段确认
- [ ] requirements.md 已通过自检（完整性、一致性、清晰度、范围、YAGNI）
- [ ] Frontmatter 字段已正确填写
```

### Requirements Self-Review

写完 requirements.md 后，必须先自检并修正，再决定 `stage_status`：

| 检查项 | 不通过标准 | 处理方式 |
|--------|------------|----------|
| 完整性 | 存在 TODO/TBD/空章节，或核心章节只有占位描述 | 补全内容；无法补全则加入待确认问题并保持 draft |
| 一致性 | 目标、范围、AC、NFR、假设之间互相矛盾 | 修正冲突；无法判断时提问 |
| 清晰度 | 实现者可能把同一条需求解释成两个不同结果 | 改写为可验证规则或 AC |
| 范围 | 一份 requirements.md 覆盖多个独立交付项目 | 拆分 feature 或收窄本次 In Scope |
| YAGNI | Must 中混入未请求、无成功指标支撑的扩展功能 | 移入 Out of Scope / Future Considerations |

### stage_status 判定规则

| 条件 | status |
|------|--------|
| 存在阻塞性待确认问题 | `draft` |
| 所有阻塞问题已解决，非阻塞问题已标注假设 | `ready` |
| 资料未收集完整 | `draft` + `evidence_complete: false` |

---

## Raw Inbox Normalize

当 `requirements.md` frontmatter 中出现 `generation_mode: raw_prd_input` 或 `input_kind: raw_prd` 时，说明该文件仍是用户粘贴完整 PRD 原文的 inbox。此时必须先 normalize，不能直接进入 review 或后续设计阶段。

### Normalize 规则

1. 读取 raw `requirements.md`，确认正文不是空模板。
2. 将 raw PRD 原文迁移或保留到 `resource/raw-prd.md`。
3. 建立 `resource/` 资料索引，将 `resource/raw-prd.md` 标记为 PRD source。
4. 根据 `meta.yml.scenario` 决定后续生成方式：
   - `prd_direct`：按 PRD Direct Mode 零提问提取，缺口标记为 `[GAP]`。
   - `product_provided`：按 Interview Mode 解析资料，并对阻塞缺口发起结构化提问。
5. 改写 `requirements.md` 为结构化 requirements contract，frontmatter 不再使用 `generation_mode: raw_prd_input`。

### Normalize 后的约束

- `requirements.md` 必须包含 Domain ID、Acceptance Criteria、In Scope / Out of Scope、NFR、约束与假设、待确认问题、资料索引。
- 若仍存在阻塞缺口，`stage_status: draft`。
- 只有无阻塞缺口，且资料索引完整时，才允许 `stage_status: ready`。
- 下游阶段只能消费 normalize 后的 structured contract。

---

## PRD Direct Mode

当 `meta.yml.scenario: prd_direct` 时激活此模式。适用于用户已有公司提供的完整 PRD + 原型 + 设计稿，不需要多轮采访的场景。

### 核心原则

1. **引用不复制**：requirements.md 中每个条目标注来源位置（"见 PRD §3.2" / "见原型 page-3"），不搬运 PRD 原文段落
2. **结构化补全**：PRD 中没有的结构（Domain ID 编号体系、AC 的 Given/When/Then 格式化）由本阶段补全
3. **缺口标记**：PRD 缺失的关键信息标记为 `[GAP]`，不自行编造内容
4. **零提问**：不向用户发起结构化提问轮次；所有信息从材料中提取
5. **适应不固定格式**：不假设 PRD 有固定模板结构，通过语义理解定位对应内容

### PRD Direct 流程

```
┌─────────────────────────────────────────────────────────┐
│              PRD Direct 提取流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 接收并索引所有材料（PRD / 原型 / 设计稿）              │
│       │                                                 │
│       ▼                                                 │
│  2. 通读材料，建立功能模块清单                             │
│       │                                                 │
│       ▼                                                 │
│  3. 推导 Domain ID 体系（从功能模块结构映射）              │
│       │                                                 │
│       ▼                                                 │
│  4. 提取并格式化各章节（引用模式）                         │
│       │                                                 │
│       ▼                                                 │
│  5. 标记缺口 [GAP]                                      │
│       │                                                 │
│       ▼                                                 │
│  6. 产出 requirements.md + 自检                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 步骤详解

**Step 1: 接收并索引材料**
- 确认 `resource/` 目录下所有文件
- 若 PRD 原文来自 raw `requirements.md` inbox，先按 Raw Inbox Normalize 迁移或保留到 `resource/raw-prd.md`
- 建立材料清单：PRD 文件路径、原型文件路径、设计稿路径
- 验证文件可读性

**Step 2: 通读材料，建立功能模块清单**
- 通读 PRD 全文（逐章节，非仅标题）
- 浏览原型所有页面
- 列出功能模块清单，标注各模块在 PRD 中的章节位置

**Step 3: 推导 Domain ID 体系**
- 从功能模块清单推导 Domain ID（格式同 interview 模式：`D-{MODULE}-{NNN}`）
- 标注每个 Domain ID 对应的 PRD 章节/原型页面

**Step 4: 提取并格式化各章节**

对 requirements.md 的每个核心章节，采用"引用 + 结构化"方式：

| 章节 | 提取逻辑 |
|------|----------|
| 需求背景与目标 | 引用 PRD 背景章节位置，提取量化的成功指标 |
| 用户故事/用户路径 | 从原型页面流程提取，转写为 User Story 格式，标注来源页面 |
| 功能范围 | 引用 PRD 范围章节，整理为 In/Out of Scope + MoSCoW |
| 业务域建模 | Step 3 产出的 Domain ID 体系 |
| 验收标准 | 从 PRD 需求条目转写为 Given/When/Then，绑定 Domain ID，标注原文出处 |
| 非功能需求 | 从 PRD 非功能章节提取，量化（若 PRD 未量化则标记 `[GAP]`） |
| 约束与假设 | 引用 PRD 约束/依赖章节 |
| 待确认问题 | 仅记录 `[GAP]` 项，标注影响和阻塞级别 |
| 需求资料索引 | 列出所有源文件及其在 requirements.md 中被引用的位置 |

**Step 5: 标记缺口**
- 扫描所有章节，对 PRD 中确实缺失的关键信息标记 `[GAP]`
- 每个 `[GAP]` 标注：缺失内容描述、影响范围、是否阻塞（阻塞 = 影响 stage_status）

**Step 6: 产出与自检**
- 执行 PRD Direct Verification Checklist（见下方）
- 设置 frontmatter

### PRD Direct Frontmatter

```yaml
---
stage: ship-define
stage_status: ready  # 若存在阻塞性 [GAP] 则为 draft
generation_mode: prd_direct
source_documents:
  - path: "resource/raw-prd.md"
    type: prd
  - path: "resource/prd.docx"
    type: prd
  - path: "resource/prototype.html"
    type: prototype
  - path: "resource/design.fig"
    type: design
extraction_gaps: []  # [GAP] 项汇总列表
updated_at: ""
evidence_complete: true
---
```

### PRD Direct 产出格式示例

```markdown
#### 5. 验收标准

| AC ID | Domain | 验收标准 | 来源 |
|-------|--------|----------|------|
| AC-AUTH-001 | D-AUTH-001 | Given 用户在登录页, When 输入正确凭证并提交, Then 跳转到首页且显示用户名 | PRD §4.1.2 |
| AC-AUTH-002 | D-AUTH-001 | Given 用户在登录页, When 连续 5 次输入错误密码, Then 账户锁定 15 分钟 | PRD §4.1.3 |
| AC-ORD-001 | D-ORD-001 | Given 用户已登录且购物车非空, When 点击"提交订单", Then 生成订单并跳转支付页 | 原型 page-7 |

#### 6. 非功能需求

| 类别 | 指标 | 来源 |
|------|------|------|
| 性能 | 页面首屏加载 < 2s (P95) | PRD §6.1 |
| 性能 | API 响应 < 500ms (P95) | `[GAP]` PRD 未量化，建议补充 |
| 安全 | 支持 OAuth 2.0 + JWT | PRD §6.2 |
```

### PRD Direct Verification Checklist

```markdown
## PRD Direct 退出检查

- [ ] 所有源文件已通读（非仅标题级别）
- [ ] Domain ID 列表完整，覆盖 PRD 中所有功能模块
- [ ] 每个 Domain ID 至少有 1 条 AC，且标注了来源位置
- [ ] AC 格式为 Given/When/Then，可直接转化为测试用例
- [ ] 引用位置准确（章节号/页面号与源文件对应）
- [ ] [GAP] 项已全部标记，阻塞性 GAP 影响 stage_status
- [ ] 非功能需求已提取，未量化的标记 [GAP]
- [ ] 用户路径覆盖主流程 + 关键异常流程
- [ ] Frontmatter 字段已正确填写（generation_mode: prd_direct）
- [ ] source_documents 列表与 resource/ 目录一致
```

### PRD Direct stage_status 判定规则

| 条件 | status |
|------|--------|
| 存在阻塞性 `[GAP]`（核心业务逻辑缺失、安全需求未明确） | `draft` |
| 无阻塞性 GAP，非阻塞 GAP 已标记 | `ready` |
| 源文件不完整或不可读 | `draft` + `evidence_complete: false` |

## Technical Plan Mode

当旧 feature 已停在 `ship-define` 且 `requirements.md.generation_mode: technical_plan`，或用户显式要求手动整理技术方案 selected scope 时激活。新建 `meta.yml.scenario: technical_plan_provided` 默认直接进入 `ship-tech-discovery`，由 `ship-tech-discovery` 在开头派生最小 `requirements.md` index。该兼容模式只服务已有项目迭代：技术方案原文描述“怎么实现”，不是 `requirements.md` 合同本身；本阶段必须只围绕 `technical_plan_source.selected_scope` 提取“做到什么算完成”的最小 requirements 和最小 AC。

执行规则：

1. 读取 `meta.yml.technical_plan_source`，确认 `source_files` 或 `pasted_excerpt_file` 至少存在一种，且 `selected_scope` 非空。
2. 只解析 selected scope；未选中内容写入 Out of Scope 或资料索引说明，不得进入 In Scope、Domain ID 或 AC。
3. 若未选中内容是前置依赖或冲突，只写入待确认问题 / risk，不自动扩大 selected scope。
4. 为 selected scope 建立最小 Domain ID，避免把整份技术方案拆成完整 PRD。
5. 若技术方案已有明确验收标准，标准化为 AC ID；若没有，只提取最小可验收结果草案，并在待确认问题中要求用户确认。新建场景 E 的确认记录写入 `ship-tech-discovery` 的 Research Alignment Check。
6. `requirements.md.stage_status: ready` 必须满足：Domain ID、AC ID、In Scope / Out of Scope、待确认问题、资料索引、`source_documents` 或等价 selected scope 来源索引齐全，且不存在阻塞性 AC 缺口。

Technical Plan frontmatter 示例：

```yaml
---
stage: ship-define
stage_status: draft
generation_mode: technical_plan
source_documents:
  - path: "resource/order-export-tech-design.md"
    selected_scope: "3.2 Order export async task"
selected_scope:
  - "3.2 Order export async task"
updated_at: ""
evidence_complete: true
---
```

退出检查：

- [ ] In Scope 只覆盖 selected scope
- [ ] Out of Scope 明确说明未选中技术方案内容不进入本期
- [ ] 每个 AC 都绑定 Domain ID，并能回指 selected scope 来源位置
- [ ] 没有把未选中章节、接口或模块纳入 requirements 合同
- [ ] 缺失 AC 或用户未确认的最小 AC 草案未被标记为 ready
