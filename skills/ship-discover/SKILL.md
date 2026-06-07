---
name: ship-discover
description: "ShipKit pre-Define stage. Transforms vague ideas or change requests into structured product briefs. Use when user has no PRD/prototype/UIUX and only has a rough idea or wants to enhance an existing feature."
---

# 需求探索 (Requirement Discovery)

## Overview

需求探索是开发工作流的条件性前置阶段，负责将"模糊想法"或"变更请求"转化为结构化的产品简报 `product-brief.md`，质量足以喂给 `ship-define` 解析。

本阶段通过 `discovery_mode` 区分两条分支：

- **greenfield**（场景 A / 零到一）：从一句话想法出发，通过结构化发现过程产出产品简报
- **evolve**（场景 C / 迭代增强）：从已有功能/代码 + 变更请求出发，合成新需求

核心目标：
- 把"我大概想做..."转化为有明确边界、可衡量成功标准的产品简报
- 通过 2-3 方案对比帮助用户做出知情决策
- 严格 YAGNI——砍掉所有"以后可能需要"的功能
- 为下游 `ship-define` 提供足够结构化的输入，减少 define 阶段的开放式提问

## When to Use

- 用户只有一句话想法，没有 PRD/原型/设计稿（场景 A）
- 用户引用已有功能/代码并描述变更需求，但无新版完整 PRD（场景 C）
- orchestrator 场景识别判定为 greenfield 或 evolve

## When NOT to Use

- 用户已提供完整 PRD/Figma/原型/UIUX 设计稿——直接进 `ship-define`
- 纯 bug 修复——使用 debugging 流程
- 用户明确说"跳过探索直接录入需求"——尊重用户意图

## Process

```
┌─────────────────────────────────────────────────────────────┐
│                    需求探索流程                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 分支判定 ──→ greenfield / evolve                         │
│       │                                                     │
│       ├── [greenfield] ──→ 2a. 范围评估                      │
│       │                       │                             │
│       │                       ▼                             │
│       │                  3a. Fact Verification               │
│       │                       │                             │
│       │                       ▼                             │
│       │                  4a. 上下文采集 (3-5 题)              │
│       │                       │                             │
│       │                       ▼                             │
│       │                  5a. 方案探索 (2-3 方案)              │
│       │                       │                             │
│       │                       ▼                             │
│       │                  6a. 深挖选定方案 (3-5 题)            │
│       │                       │                             │
│       └── [evolve] ──→ 2b. 现状扫描                          │
│                            │                                │
│                            ▼                                │
│                       3b. 变更意图确认 (1-3 题)               │
│                            │                                │
│                            ▼                                │
│                       4b. 影响分析                            │
│                            │                                │
│       ┌────────────────────┘                                │
│       ▼                                                     │
│  7. 编写 product-brief.md                                    │
│       │                                                     │
│       ▼                                                     │
│  8. 规格自检 (Self-Review)                                   │
│       │                                                     │
│       ▼                                                     │
│  9. 用户确认 → stage_status: ready                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Greenfield 分支详解

**Step 2a: 范围评估（单题）**

第一个问题必须是范围判定：
- 这是单个功能、多子系统、还是对现有功能的修改？
- 若多子系统：强制拆解，先聚焦第一个子系统
- 若实际是修改现有功能：切换到 evolve 分支

**Step 3a: Fact Verification（Priority #0）**

若用户提到具体产品名、版本号、第三方服务、竞品：
- 先用 WebSearch 确认事实（产品是否存在、版本是否正确、API 是否可用）
- 将核查结果记入 `product-brief.md` 的约束章节
- 不要基于未验证的假设继续提问

**Step 4a: 上下文采集**

3-5 个问题，**单题问答**，多选优先：

1. 这个功能解决什么问题？（开放式，但给出 2-3 个常见方向供参考）
2. 目标用户是谁？（多选：终端用户 / 内部团队 / API 消费者 / 混合）
3. 成功信号是什么？（多选 + 开放：用户量 / 转化率 / 效率提升 / 错误减少）
4. 有什么硬约束？（多选：技术栈限制 / 时间线 / 团队规模 / 兼容性要求）
5. 什么明确不做？（开放式，帮助划定边界）

**Step 5a: 方案探索**

基于上下文采集结果，产出 2-3 个方案：

```markdown
## 方案对比

### 方案 A: [名称]
- 核心思路: ...
- 优势: ...
- 劣势: ...
- 适合场景: ...

### 方案 B: [名称]
- 核心思路: ...
- 优势: ...
- 劣势: ...
- 适合场景: ...

### 推荐: 方案 [X]
- 理由: ...
```

方案探索规则：
- 方案之间必须有实质差异（不是同一方案的微调）
- 每个方案必须有明确的 trade-off（没有"全面优于"的方案）
- 推荐必须给出具体理由
- YAGNI：砍掉所有"以后可能需要"的功能

**Step 6a: 深挖选定方案**

用户选定方案后，3-5 个深挖问题（此阶段可一次性提出 4-10 题）：
- 聚焦选定方案的具体实现细节
- 边界条件和异常路径
- 优先级排序（MoSCoW）
- 非功能性需求（性能、安全、可用性）

### Evolve 分支详解

**Step 2b: 现状扫描**

场景 C 必须读取并回写 `meta.yml.evolve_source`，与 `product-brief.md.base_feature` 保持一致。`ship-discover(evolve)` 只做产品/影响粗分：确认变更目标、用户影响、受影响 surface 候选和待技术验证项；完整仓库事实扫描由 `ship-tech-discovery` 执行。

必须先读取：
- 已有 feature 目录（如果有 `meta.yml`、`requirements.md`、`handoff.md`）
- 相关代码文件（API 路由、组件、数据模型）
- 过往 `handoff.md` 中的残余风险和 follow-up 建议

产出一段"现状摘要"，向用户确认理解是否正确。

**Step 3b: 变更意图确认**

1-3 个问题，聚焦变更本身：
1. 具体想改什么？（开放式，但基于现状扫描给出候选方向）
2. 改动的触发原因？（多选：用户反馈 / 性能问题 / 新业务需求 / 技术债）
3. 改动边界在哪？（多选：只改前端 / 只改后端 / 前后端都改 / 需要新增接口）

**Step 4b: 影响分析**

基于现状扫描 + 变更意图，自动分析：
- 受影响的 API 端点
- 受影响的前端组件/页面
- 受影响的数据模型/表结构
- 受影响的已有 AC（如果有 requirements.md）
- 不受影响的部分（明确标注"保持不动"）

### 规格自检 (Step 8)

编写完 `product-brief.md` 后，执行自检清单；`product-brief.md.stage_status=ready` 前必须记录产品方向确认：`user_direction_sign_off` 与 `direction_confirmed_at`。若用户只确认“先按这个方向走”，也要写入原话。

| 检查项 | 标准 |
|--------|------|
| 完整性 | 所有必填章节都有实质内容，无 TODO/TBD 占位 |
| 一致性 | 范围、成功标准、约束之间无矛盾 |
| 可衡量 | 成功标准可以被验证（不是"用户体验好"这种模糊表述） |
| YAGNI | 没有"以后可能需要"的功能混入范围 |
| 边界清晰 | In/Out 明确，不存在"视情况而定"的灰色地带 |
| 影响完整 | evolve 分支的影响分析覆盖了所有相关模块 |

自检可委派子代理执行，但结果必须由主上下文审核。

## Scope Adaptation

本阶段根据 `project_scope` 调整发现重心。`fullstack` 走现行流程；`backend_only` 与 `frontend_only` 走对应子分支。

| project_scope | greenfield 分支调整 | evolve 分支调整 |
|---------------|---------------------|-----------------|
| `fullstack`（默认） | 现行流程 | 现行流程 |
| `backend_only` | Step 4a 上下文采集改为后端导向；Step 5a 方案对比改为架构立场 | Step 2b 现状扫描聚焦 API surface 与消费者；Step 4b 影响分析按接口级而非组件级 |
| `frontend_only` | 镜像规则（聚焦交互/视觉/前端架构，不展开） | 镜像规则（聚焦组件/页面/路由影响，不展开） |

### `backend_only` × greenfield 子分支

Step 4a 上下文采集（替换默认问题集）：

1. 这个后端服务解决什么问题？（开放式，给出 2-3 个常见方向：内部 API / 对外 API / 异步任务 / 数据管道）
2. **消费者与调用方是谁？**（多选 + 开放：前端 SPA / 移动端 / 第三方集成方 / 内部其他服务 / 批处理 / 定时任务）
3. **吞吐与延迟预算**（开放式 + 量级：QPS 量级 / P99 延迟目标 / 数据规模）
4. **可用性目标**（多选：99% / 99.9% / 99.99%；故障容忍度；降级策略）
5. **兼容性约束**（多选 + 开放：必须兼容现有调用方 / 可发新版本 / 内部使用可以 break / 有 SLA 合同绑定）
6. 什么明确不做？（开放式，划定边界）

Step 5a 方案对比（架构立场而非产品立场）：

方案对比维度从"产品方向"切换到"架构方向"：

```markdown
### 方案 A: REST/HTTP API
- 适合场景: 通用 Web/移动端调用，资源导向
- 优势: 工具链成熟、缓存友好、易调试
- 劣势: 类型弱、流式支持差

### 方案 B: gRPC
- 适合场景: 内部微服务高频调用，强类型
- 优势: 性能好、proto 即文档、双向流
- 劣势: 浏览器支持弱、调试链路长

### 方案 C: 消息总线（事件驱动）
- 适合场景: 异步、解耦、削峰
- 优势: 高吞吐、容错好
- 劣势: 一致性弱、调试复杂、延迟高

### 方案 D: CLI / 内部 SDK
- 适合场景: 工具类、库类
- 优势: 无网络层、本地直接调用
- 劣势: 部署形态受限
```

每个方案必须给出 trade-off，YAGNI 原则保持不变。

### `backend_only` × evolve 子分支

Step 2b 现状扫描（替换默认扫描清单）：

必须先读取：
- 已有 feature 目录的 `api-contract.md` / `backend-design.md` / `handoff.md`
- 当前对外 API surface（路由表、proto 文件、消息 topic 列表、CLI 命令清单）
- 当前消费者清单（前端调用点、其他服务调用方、定时任务触发器）
- 监控/日志中暴露的吞吐、延迟、错误率基线

产出"API surface 现状摘要"，向用户确认理解是否正确。

Step 4b 影响分析（按接口级而非组件级）：

基于现状扫描 + 变更意图，自动分析：
- 受影响的 endpoint / proto method / topic schema / CLI 子命令
- 每个受影响项的变更类型：**新增 / 兼容修改 / breaking change / 废弃 / 删除**
- 受影响的消费者：哪些调用方会感知到变更，是否需要协调升级
- 数据模型/Schema 变更对持久化层的影响（迁移、回滚）
- 兼容性策略：版本并存 / 平滑迁移 / 强制升级 / deprecation 周期



本阶段只允许**辅助委派**。

允许委派的子任务：
- 现有代码扫描与摘要
- 过往 feature 目录索引
- 外部产品/版本/API 的事实核查（Fact Verification）
- 规格自检（Self-Review）

禁止委派的动作：
- 方案选择决策
- 范围判定
- `product-brief.md` 的正式定稿
- 替用户回答方案选择问题

## Output: product-brief.md

### Frontmatter

```yaml
---
stage: ship-discover
stage_status: draft  # draft → 用户未确认; ready → 可进入下一阶段
discovery_mode: greenfield  # greenfield | evolve
approach_selected: ""        # greenfield: 选定的方案名; evolve: 留空
base_feature: ""             # evolve: 基线 feature 路径; greenfield: 留空
discovery_rounds: 0          # 已完成的发现/澄清轮次
fact_check_done: false       # 涉及具体产品/版本时是否完成 Fact Verification
updated_at: ""
evidence_complete: false
---
```

### 章节结构

#### 1. 问题陈述
- 为什么要做这个（痛点/机会）
- 当前状态是什么（现状描述）

#### 2. 目标用户与使用场景
- 主要用户角色
- 核心使用场景（1-3 个）
- 用户当前如何解决这个问题

`backend_only` 适配：本节改为 **消费者与调用方**：
- 调用方清单（前端 SPA / 移动端 / 第三方 / 内部服务 / 批处理 / 定时任务）
- 每类调用方的核心使用场景
- 调用方当前如何与本服务（或前身）交互

#### 3. 选定方案
- 方案名称与核心思路
- 选择理由
- 被否决的备选方案及否决原因（保留决策上下文）

`backend_only` 适配：方案立场从"产品方向"切换到"架构方向"（REST / gRPC / 消息总线 / CLI / SDK 中的一个或几个），并衔接 `ship-contract` 的契约形态选择。

#### 4. 范围 (In/Out)
- Must Have（必须）
- Should Have（应该）
- Won't Have（明确不做）

#### 5. 成功标准
- 可衡量的指标（至少 2 个）
- 验证方式

#### 6. 约束与假设
- 技术约束（栈、兼容性、性能）
- 业务约束（时间线、合规、依赖）
- 假设（标注为假设，后续可验证）

#### 6.1 非功能预算（`backend_only` 必填）
- 吞吐目标（QPS 量级 / 峰值容量）
- 延迟目标（P50 / P99 / 超时阈值）
- 可用性目标（SLA / 故障容忍度 / 降级策略）
- 数据规模（单次请求体量 / 总数据量级）

`fullstack` / `frontend_only` 下本节可省略或仅记录前端相关性能预算（首屏、交互响应）。

#### 6.2 契约形态预判（`backend_only` 必填）
- 拟采用的契约形态（REST / gRPC / 消息 / 定时任务 / CLI / SDK 中的一个或几个）
- 选择理由（与 §3 选定方案呼应）
- 备选形态及否决原因
- 给 `ship-contract` 阶段的输入提示（哪些调用方走哪种形态）

`fullstack` / `frontend_only` 下本节可省略；`ship-contract` 阶段会基于 tech-selection 自行决定。

#### 7. 影响分析（仅 evolve 分支）
- 受影响的 API/模块/组件
- 受影响的已有 AC
- 不受影响的部分
- 数据迁移需求（如有）

`backend_only` 适配：影响分析按接口级而非组件级，每个受影响项必须标注变更类型 —— **新增 / 兼容修改 / breaking change / 废弃 / 删除**；并显式列出受影响的消费者及兼容性策略（版本并存 / 平滑迁移 / 强制升级 / deprecation 周期）。

#### 8. Open Questions
- 非阻塞性问题（向下游传递，不阻止 stage_status: ready）
- 每个问题标注影响范围和建议默认值

## Exit Condition

- `product-brief.md.stage_status: ready`
- 所有阻塞性问题已关闭（Open Questions 章节只剩非阻塞项）
- 用户明确确认简报内容（口头"确认""可以""没问题"等均视为确认）
- 无独立 review gate——下游 `ship-define-review` 是统一的需求质量门

## Transition Rules

- greenfield 分支完成后：若 feature 涉及 UI 且无外部 UIUX 材料 → 进入 `ship-shape`
- greenfield 分支完成后：若 feature 无 UI 或用户将另行提供设计稿 → 跳过 `ship-shape`，进入 `ship-define`
- evolve 分支完成后：若变更涉及 UI 改动且无设计稿 → 进入 `ship-shape`
- evolve 分支完成后：若变更不涉及 UI 或 UI 改动极小 → 跳过 `ship-shape`，进入 `ship-define`
