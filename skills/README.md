# skills-new — 开发工作流技能套件

> 一套从需求到交付的端到端开发工作流，把 PRD/原型/UI-UX 设计稿转化为可验证的可工作软件。前后端分离、契约先行、三道硬门禁、产物驱动。

## 设计目标

- **覆盖完整链路**: 需求 → 评审 → 调研 → 选型 → 契约 → 前后端方案 → 实施计划 → 编码 → 测试 → 验收
- **前后端分离**: tech-selection / api-contract / frontend-design / backend-design / frontend-plan / backend-plan 各自独立，可并行评审与并行执行
- **契约先行**: api-contract.md 是前后端协作的合同，所有页面-接口映射、Service-接口实现都基于它
- **门禁产物化**: 三道硬门禁产出独立的 `review-<stage>.md`，含 checklist + 问题分级 + 用户原话签字，比单字段 frontmatter 更结实
- **元数据集中索引**: feature 级 `meta.yml` 负责恢复和汇总；阶段事实仍以各产物 frontmatter 为准
- **共享协议单源**: 阶段标识、门禁字段、验收产物 ownership 统一收敛到 `ship-orchestrator/_templates/protocol/workflow-protocol.md`
- **可作为活示例**: 套件附带一份完整的 TODO Web App 范本，证明流程能端到端跑通

## 技能列表

| 阶段 | Skill | 类型 | 产物 |
|------|-------|------|------|
| 总调度 | `ship-orchestrator` | 路由器 | meta.yml + 路由决策 |
| 01 需求录入 | `ship-intake` | 阶段 | requirements.md |
| 02 需求评审 | `ship-intake-review` | **硬门禁** | review-requirement.md |
| 03 技术调研 | `ship-research` | 阶段 | tech-research.md |
| 04 技术选型 | `ship-stack` | 阶段 | tech-selection.md |
| 05 接口规约 | `ship-contract` | 阶段 | api-contract.md |
| 06 前端方案 | `ship-frontend-design` | 阶段 | frontend-design.md |
| 07 后端方案 | `ship-backend-design` | 阶段 | backend-design.md |
| 08 设计评审 | `ship-design-review` | **硬门禁** | review-design.md |
| 09 前端计划 | `ship-frontend-plan` | 阶段 | frontend-plan.md |
| 10 后端计划 | `ship-backend-plan` | 阶段 | backend-plan.md |
| 11 计划评审 | `ship-plan-review` | **硬门禁** | review-plan.md |
| 12 编码执行 | `ship-build` | 阶段 | 代码 + 任务状态 |
| 13 测试 | `ship-verify` | 阶段 | 测试代码 + `verification.md`（测试章节） |
| 14 验收 | `ship-handoff` | 阶段 | `verification.md`（验收结论）+ `handoff.md` |
| 工具 | `ship-spec` | utility | .docs/spec/ |

## 流程图

```
                 [ship-orchestrator] (放宽触发：一句话确认即启动)
                         │
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-intake  →  requirements.md           │
       └─────────────────────────────────────────────────────┘
                         │
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ★ ship-intake-review (硬门禁)  →  review-req.md  │
       └─────────────────────────────────────────────────────┘
                         │ approved
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-research → ship-stack (含 ADR)       │
       └─────────────────────────────────────────────────────┘
                         │
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-contract  →  api-contract.md          │
       └─────────────────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
       ┌──────────────┐   ┌──────────────┐
       │ 06-frontend  │   │ 07-backend   │
       │   -design    │   │   -design    │
       └──────────────┘   └──────────────┘
                │                 │
                └────────┬────────┘
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ★ ship-design-review (硬门禁)  →  review-design.md     │
       │     三方交叉验证: contract ↔ frontend ↔ backend       │
       └─────────────────────────────────────────────────────┘
                         │ approved
                         ▼
                ┌────────┴────────┐
                ▼                 ▼
       ┌──────────────┐   ┌──────────────┐
       │ 09-frontend  │   │ 10-backend   │
       │    -plan     │   │    -plan     │
       └──────────────┘   └──────────────┘
                │                 │
                └────────┬────────┘
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ★ ship-plan-review (硬门禁)  →  review-plan.md         │
       └─────────────────────────────────────────────────────┘
                         │ approved
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-build (Contract-First Slicing)          │
       │     契约层 → 前后端并行 → 集成                          │
       └─────────────────────────────────────────────────────┘
                         │
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-verify (前后端分轨 + 契约一致性测试)              │
       └─────────────────────────────────────────────────────┘
                         │
                         ▼
       ┌─────────────────────────────────────────────────────┐
       │  ship-handoff  →  verification.md + handoff.md      │
       └─────────────────────────────────────────────────────┘
```

## Feature 目录结构

```
.docs/feature-YYYYMMDD-<short-name>/
├── meta.yml                    # feature 级索引（恢复 / 汇总 / 路由）
├── requirements.md
├── review-requirement.md       # 硬门禁产物 ★
├── tech-research.md
├── tech-selection.md
├── api-contract.md
├── frontend-design.md
├── backend-design.md
├── review-design.md            # 硬门禁产物 ★
├── frontend-plan.md
├── backend-plan.md
├── review-plan.md              # 硬门禁产物 ★
├── verification.md
├── handoff.md
└── resource/                   # 需求资料：PRD / 原型 / Figma 截图 / 线框图
    └── README.md
```

## 启动方式

### 新建 feature

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流：<需求描述>

附件资料：resource/<file>.md / Figma 链接 / ...
```

orchestrator 会识别意图，给出执行计划摘要，用户一句话确认（"go" / "继续" / "开始"）即进入 ship-intake。

### 继续已有 feature

```text
继续 .docs/feature-20260522-todo-app/
```

orchestrator 读 `meta.yml.current_stage` 和各产物文档 frontmatter，从断点恢复。

### 直接调用某阶段

```text
使用 ship-frontend-design，基于 .docs/feature-20260522-todo-app/api-contract.md 做前端方案
```

## 核心设计原则

### 1. 产物驱动而非对话驱动

- 每个阶段的"完成"不依赖 agent 自我评估，而是产物文件 + frontmatter 字段是否齐备
- 阶段文档 frontmatter 是事实源；`meta.yml` 只做索引和摘要缓存
- `stage_status: ready` 与 `evidence_complete: true` 双字段解耦，防止 agent 把"流程上可推进"当成"证据已齐备"

### 2. 三道硬门禁

| 门禁 | 时机 | 目的 |
|------|------|------|
| ship-intake-review | 进入技术阶段前 | 确认需求清晰、AC 可验证、无歧义 |
| ship-design-review | 进入计划阶段前 | 三方交叉验证 contract ↔ frontend ↔ backend |
| ship-plan-review | 进入编码前 | 任务粒度合理、依赖正确、AC 全覆盖 |

每道硬门禁产出 `review-<stage>.md`，必须有用户原话签字，禁止 agent 自审自批。

### 3. Contract-First Slicing

实施阶段任务排序：
1. **契约层任务**（前后端共享）：mock 服务、共享类型、API client、API 路由骨架
2. **前后端并行任务**：组件 / 服务 / 业务逻辑
3. **集成任务**：E2E 测试、契约测试

这是前后端能并行开发的前提。任何"页面任务排在 mock 之前"或"业务任务排在路由骨架之前"都是反模式。

### 4. Anti-Rationalization

每个 SKILL.md 包含 3-5 条"agent 可能跳步的借口 + 反驳"。这是防 AI 走捷径的核心机制。

### 5. Progressive Disclosure

- 主 SKILL.md 控制在 200-400 行
- 详细模板放在 `ship-orchestrator/_templates/` 共享目录（由 orchestrator 统一管理）
- 范本放在 `ship-orchestrator/_templates/todo-app-example/`，按需加载，不污染初始 context

## 与旧 skills/ 的差异

| 维度 | 旧 skills/ | skills-new/ |
|------|-----------|-------------|
| 阶段数 | 6 | 14 |
| 前后端分离 | 无（design.md 单体） | tech / contract / fe / be 各自独立 |
| 接口规约承载 | 无 | api-contract.md 独立产物 |
| UI-UX 资料承载 | resource/ 弱索引 | frontend-design.md 含页面-接口映射表 |
| 门禁形式 | 单字段 frontmatter（仅 design） | 三道硬门禁产出独立评审文档 |
| 元数据维护 | 6 处 frontmatter 重复 | frontmatter 为准 + meta.yml 摘要索引 |
| 触发方式 | 必须用户原话写 skill 名 | 识别意图后一句话确认即启动 |
| 测试 | verification 单一映射 | ship-verify 前后端分轨 + 契约测试 |
| Anti-Rationalization | 无 | 每个 SKILL 必备 |
| 范本 | 无端到端示例 | TODO Web App 完整范本 |

## 范本

`ship-orchestrator/_templates/todo-app-example/` 提供一套完整的 TODO Web App 范本，技术栈：

- 前端: React 18 + Vite 5 + TypeScript 5 + TailwindCSS + TanStack Query + Zustand
- 后端: Node 20 + Express 4 + Prisma 5 + SQLite + zod + pino
- 测试: Vitest + Testing Library + Playwright + Supertest

可作为：
- 学习 skills-new 流程的标准答案
- 实际项目启动时的详细程度下限
- 验证 skills 套件能端到端跑通的最小可运行示例

## 最佳实践

### 启动前

1. 准备需求资料（PRD、原型、Figma 链接、墨刀链接），放到 `resource/`
2. 资料越完整，ship-intake 阶段越快
3. 一个 feature 一个目录，不混合

### 推进中

4. 不跳阶段：每个阶段产物是下一阶段的输入
5. 三道硬门禁不能合并：每道独立产出 review 文档
6. 任务粒度：每个任务能在一次对话中完成并验证
7. DOING 唯一性：同一时间只有一个 DOING 任务

### 验收

8. 每条 AC 必须有验证证据
9. FAIL/BLOCKED 写入残余风险，不隐藏
10. handoff.md 即使无变更也写"无"

## 反模式

| 反模式 | 正确做法 |
|--------|---------|
| 简单 bug fix 跳过需求和评审直接编码 | 走 fast-track 最小路径，仍保留 `ship-intake` 和 `ship-intake-review` |
| 跳过 02 评审直接进技术阶段 | 必须等 review-requirement.md approved |
| 把 frontend/backend design 合并写 | 拆开，独立 review |
| 没有 api-contract.md 就开始前后端方案 | api-contract 是 fe/be 设计的输入 |
| 实施任务里页面任务排在 mock 之前 | Contract-First Slicing 必须先做契约层 |
| 用 frontmatter 单字段做门禁 | 硬门禁必须出独立 review 文档 |
| 测试只做单元测试 | 必须有契约测试和 E2E |
| 验收只看测试通过 | 必须做 AC 全量映射 |

## 维护

修改 SKILL.md 后：
- 检查与 `ship-orchestrator/_templates/protocol/workflow-protocol.md` 的协议对齐
- 检查与 `ship-orchestrator/_templates/meta/meta.yml.template` 的字段对齐
- 检查与 `ship-orchestrator/_templates/review/review.md.template` 的章节对齐
- 用 `ship-orchestrator/_templates/todo-app-example/` 验证流程仍可端到端跑通
