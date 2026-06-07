---
name: ship-orchestrator
description: "ShipKit orchestrator. Routes development workflow stages. Use when user wants to start a new feature, continue an existing feature, or check feature status."
---

# Workflow Orchestrator

## Overview

Workflow Orchestrator 是开发工作流 skills 套件的总调度器，负责入口判断、阶段推断和路由分发。它不执行具体阶段工作，而是识别用户意图后将控制权交给对应的阶段 skill。

本 skill 支持三种入口模式：NEW_FEATURE（启动新功能开发）、CONTINUE_FEATURE（恢复中断的功能开发）、INSPECT_FEATURES（查看功能状态总览）。调度器通过读取 `meta.yml.current_stage`、`meta.yml.macro_stage`、各产物 frontmatter 和 `meta.yml` 摘要状态来判断当前位置，并根据门禁规则决定是否允许推进到下一阶段。若用户未指定 feature 目录，调度器必须先检查未完成 feature，再决定继续、选择新建模式或进入资料准备态。

设计原则是"放宽触发、严格推进"——用户无需记住 14 个内部阶段名，只要表达出开发意图，调度器就能识别并给出 5 个大阶段视图下的执行摘要。内部仍然按细阶段和门禁推进，但默认对外只展示：当前大阶段、当前目标、下一次需要用户确认的动作。

`ship-spec` 不作为 stage 进入 stage map。它以 workflow utility 的方式存在：orchestrator 负责在关键阶段前后触发 helper、维护 `meta.yml.spec_context`，具体阶段 skill 负责实际读取规范、把引用的 `spec_id` 写回产物与证据。

协议约束：
- Canonical stage id、门禁字段、`verification.md` ownership 统一以 [`workflow-protocol.md`](./_templates/protocol/workflow-protocol.md) 为准
- 阶段文档 frontmatter 是事实源；`meta.yml` 仅是 orchestrator 索引层
- 若产物 frontmatter 与 `meta.yml` 摘要冲突，先读取产物确认事实，再用 `sync_meta_from_artifacts(feature_dir)` 生成回写建议；不得只凭 stale meta 推进
- 默认对外展示 `macro_stage`，只在高级模式和诊断模式下展开 `current_stage`
- `ship-spec` hook 契约和 `meta.yml.spec_context` 统一以共享协议为准

## When to Use

- 用户表达"做一个功能""开发一个 feature""启动项目""新需求来了"等开发意图
- 用户说"继续上次的""接着做""回到 XX 功能"等恢复意图
- 用户问"现在到哪一步了""功能进度怎样""还有哪些没做完"等查询意图
- 任何阶段 skill 完成后需要判断下一步去向时

## When NOT to Use

- 用户在做与 feature 开发无关的事（修 bug、写文档、配置环境）
- 用户已明确指定要执行某个具体阶段 skill 且上下文无歧义
- 纯代码问答、技术咨询、不涉及工作流推进的对话

## Trigger Recognition

意图识别采用宽松匹配策略，以下模式均应触发：

| 意图类别 | 触发词/模式示例 |
|---------|---------------|
| 新功能启动 | "做一个…""开发…功能""新需求""启动…项目""我想加一个…""帮我实现…""搞一个…" |
| 恢复开发 | "继续""接着做""上次到哪了""回到…功能""还没做完的""刚才那个" |
| 状态查询 | "进度""到哪一步""状态""还剩什么""看看功能列表""哪些在做" |
| 阶段跳转 | "开始设计""进入实现""做技术选型"（需验证门禁后路由） |

意图歧义处理规则：
- 若用户输入同时匹配多个类别，优先级为 CONTINUE > NEW > INSPECT
- 若存在进行中的 feature 且用户说"做一个功能"但未明确是新功能，先询问是继续还是新建
- 若用户直接说阶段名（如"做技术选型"），先检查是否有活跃 feature，有则路由，无则启动 NEW 流程

识别到意图后的标准响应流程：
1. 判断入口模式（NEW / CONTINUE / INSPECT）
2. 若 NEW 且用户未指定 feature 目录：先扫描未完成 feature；若存在，先询问继续哪个或是否新建
3. 若 NEW 且确认新建：先做场景识别（见下节），再生成执行计划摘要，请用户确认
4. 若 CONTINUE：读取 meta.yml，定位 current_stage，并优先用 macro stage 报告当前状态后路由
5. 若 INSPECT：按 workspace `feature_root` 扫描所有 feature 目录，汇总状态表格

### Empty Entry Handling（未携带资料入口）

当用户只表达“开始需求 / 使用 ship-orchestrator / 继续开发”等意图，但没有指定 `feature_dir`、也没有携带资料时，必须先执行以下流程：

1. 若当前上下文已能确定 workspace，则扫描该 workspace `feature_root/feature-*`；否则先执行 Workspace Config Gate。
2. 过滤 `lifecycle_status: active | blocked` 的未完成 feature。
3. 若有多个未完成 feature：列表展示（功能名 / 当前大阶段 / updated_at / 阻塞原因），让用户选择继续哪个，或选择新建。
4. 若只有一个未完成 feature：也必须询问“是否继续这个 feature，还是新建？”，不可自动进入。
5. 若没有未完成 feature：直接列出五种新建模式，让用户选择。

五种新建模式展示文案：

```text
请选择进入方式：
1. PRD 直通：你已有完整 PRD，想直接粘贴/放资料，不做需求采访。
2. 产品提供：你有 PRD/原型/设计稿，但允许我继续澄清缺口。
3. 零到一：你只有想法，需要先头脑风暴产出需求。
4. 迭代增强：基于已有功能、feature 目录或代码路径做增强。
5. 技术方案选区：你已有技术方案，只围绕指定章节/接口/模块生成计划。
```

不要在“用户未携带资料”的入口里自行猜测模式。模式选择是用户显式决策点。

### Scenario Detection（场景识别）

NEW_FEATURE 确认启动前，必须先判定场景，决定是否进入 Discover 大阶段：

| 场景 | 入口信号 | 起点 stage | Discover 大阶段 |
|------|---------|------------|-----------------|
| A 零到一 | 用户只有一句话想法、无附件、无引用已有代码 | `ship-discover`（greenfield） | 激活 |
| B 产品提供 | 用户附了 PRD/Figma/原型/UIUX 文档，或选择先创建目录后补资料 | `ship-define`（interview mode） | 默认跳过；UIUX Gate 可插入 `ship-shape` |
| C 迭代增强 | 用户引用已有 feature 目录或具体代码路径并描述变更 | `ship-discover`（evolve） | 激活 |
| D PRD 直通 | 用户附了完整 PRD + 原型/设计稿，或选择先创建目录粘贴完整 PRD，且明确表示不需要需求录入 | `ship-define`（prd_direct mode） | 默认跳过；UIUX Gate 可插入 `ship-shape` |
| E 技术方案选区入口 | 用户提供已有技术方案文件或粘贴片段，并指定章节、接口、模块或标题；明确这是已有项目迭代；`scenario: technical_plan_provided` | `ship-tech-discovery`（technical plan entry） | 跳过 |

判定规则：
- 信号歧义时**必须显式询问用户**场景，不允许猜测
- 场景 A/C 的 `ship-discover` 通过 `meta.yml.scenario` 和产物 frontmatter `discovery_mode` 区分
- 场景 A/C 在 `ship-discover` 完成后，若 feature 涉及 UI 且无外部 UIUX 材料，进入 `ship-shape`；否则跳过
- 场景 B 不进 Discover 大阶段；`stages.ship-discover.status` 和 `stages.ship-shape.status` 记为 `skipped`
- 场景 D 不进 Discover 大阶段；`stages.ship-discover.status` 和 `stages.ship-shape.status` 记为 `skipped`；`stages.ship-define.generation_mode` 设为 `prd_direct`
- 若场景 B/D 是由“新建模式选择”进入且用户尚未放资料，则先创建 raw `requirements.md` inbox 和 `resource/README.md`，并将 `stages.ship-define.status` 设为 `blocked`、`block_reason` 设为 `awaiting_materials`
- 场景 B/D 若 `project_scope = fullstack | frontend_only` 且 feature 涉及 UI，必须执行 UIUX Material Gate：已有 Figma / 原型 / 截图 / `design-brief.md` 时继续 `ship-define`；缺少 UIUX 材料时，不得静默跳过到 `ship-frontend-design`，必须让用户选择补材料或显式授权生成线框。
- UIUX Material Gate 中用户选择补材料时，保持 `stages.ship-define.status: blocked`，`block_reason` 写 `awaiting_uiux_materials` 或在 `awaiting_materials` 中明确 UIUX 缺口；用户选择“按你的理解做线框 / 生成线框”时，必须覆写 `stages.ship-shape.status: pending`，记录 `activation_mode: uiux_material_gate_insert`、`uiux_gate_user_sign_off`、`uiux_gate_signed_at`，设置 `current_stage: ship-shape`，完成后再回到 `ship-define`。插入 `ship-shape` 后，`ship-shape` 不再视为 skipped；后续 transition 必须等待 `design-brief.md.stage_status=ready`。
- UIUX Material Gate Coverage：
  - `sufficient`：材料可访问，覆盖 Must Have 主流程、关键页面/状态、核心异常路径，可直接供 define 提取。
  - `partial`：可访问但只覆盖部分页面或缺少异常/状态；允许继续，但必须在 requirements/design 中记录 UIUX risk 或 open question。
  - `screenshot_only`：只有截图；主流程截图覆盖完整时可继续，否则按 `partial` 处理，并记录无法确认交互细节。
  - `inaccessible`：链接打不开、权限不足、文件损坏；视为缺材料，用户需补材料或授权 `ship-shape`。
- B/D inserted shape 回流 define normalize 顺序：先检查 `requirements.md` frontmatter，raw inbox 必须先 normalize；再读取 `resource/README.md` 和 source documents；再读取 `design-brief.md` 与 `resource/wireframes/`；把 `design-brief.md` 作为 UIUX source，不覆盖 PRD source，冲突写入 conflict/open question；保持 B 的 `generation_mode: interview`、D 的 `generation_mode: prd_direct`。
- 场景 C 必须有现状基线；若用户没有指定已有 feature 目录、代码路径或明确现有功能，不创建新目录，先询问基于哪个对象增强，并在 `meta.yml.evolve_source` 记录 `feature_dirs/code_paths/existing_behavior_summary` 至少一种基线
- 场景 C 与 E 的区别：C 从“变更意图 / 旧功能基线”出发，先做产品层影响扫描；E 从“已有技术方案 selected scope”出发，直接进入技术发现，但仍需仓库取证。
- 场景 E 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate；但 `ship-tech-discovery` 会为 selected scope 派生最小 `requirements.md` index，frontmatter 仍使用 `stage: ship-define`、`generation_mode: technical_plan`，仅用于 AC traceability。`stages.ship-discover.status`、`stages.ship-shape.status`、`stages.ship-define.status`、`stages.ship-define-review.status` 记为 `skipped`
- 场景 E 只允许 `project_context: existing_project`；若用户说是新项目，必须阻塞并建议改走场景 A/B/D
- 场景 E 必须写入 `technical_plan_source`，包含技术方案来源、selected scope、`ignored_source_policy: out_of_scope`、`repository_scan_required: true`
- 场景 E 只创建 `resource/README.md`，不创建 raw PRD inbox；`requirements.md` 由 `ship-tech-discovery` 开头围绕 selected scope 派生为最小 requirements index，用于后续 AC traceability；`selection_mode=pasted_excerpt` 时必须把粘贴内容归档为 `resource/technical-plan-excerpt.md` 并写入 `pasted_excerpt_file`

场景 B 与 D 的区分：
- 场景 B：用户提供了 PRD/原型等材料，但未明确表示跳过需求录入 → `ship-define` 走 interview 模式（多轮采访）
- 场景 D：用户提供了完整 PRD + 原型，且明确信号表示不需要需求录入（如"PRD 已完整"/"跳过需求录入"/"不需要生成需求文档"/"直接用 PRD"/"PRD 直通"） → `ship-define` 走 prd_direct 模式（零提问纯提取）
- 若用户提供了材料但未明确表态，默认走场景 B；可在启动确认时询问用户偏好

### Scope Detection（范围识别）

NEW_FEATURE 确认启动前，在场景识别之后，必须判定项目范围：

| 范围 | 入口信号 | 跳过阶段 |
|------|---------|---------|
| `fullstack`（默认） | 用户描述涉及前后端、或未明确声明 | 无 |
| `backend_only` | 用户明确说"纯后端""只做 API""不涉及前端" | `ship-frontend-design` |
| `frontend_only` | 用户明确说"纯前端""只做 UI""不涉及后端" | `ship-backend-design` |

判定规则：

- 信号歧义时默认 `fullstack`。此时必须显式询问用户是否要落成单侧 scope；在用户确认前不得写回单侧 `project_scope`
- 用户可在启动确认时声明 scope，也可在 `ship-tech-discovery` 完成后由 orchestrator 基于明确证据确认 scope
- 证据要求：仅当 `tech_stack`、现有 surface、consumer/entrypoint、以及项目边界四类证据都指向单侧时，才允许回写 `meta.yml.project_scope` 和 `project_scope_evidence`
- 若证据不足或存在双侧迹象，默认保持 `fullstack`，并要求用户显式确认；不得仅凭某个 `tech_stack` 字段为空就下结论
- scope 变更只允许在 `ship-design-review` 之前；一旦通过设计评审，scope 冻结，并写入 `scope_freeze.status=frozen`、`frozen_scope`、`frozen_at`、`frozen_by_gate: ship-design-review`、`user_sign_off`。
- 设计评审通过后如确需变更 scope，必须 reopen `ship-design-review`，说明 `reopen_reason`，并重新跑受影响的 contract/design/plan；不得静默修改 `project_scope`。
- scope 为 `backend_only` 时：`stages.ship-frontend-design.status = skipped`；`stages.ship-shape.status = skipped`
- scope 为 `frontend_only` 时：`stages.ship-backend-design.status = skipped`
- `ship-contract` 在所有 scope 下默认保留（形态可能不同：REST/gRPC/消息/CLI/SDK）

Scenario × Scope 组合矩阵：

| 组合 | 是否允许 | 处理规则 |
|------|---------|---------|
| A + `backend_only` | 允许 | `ship-discover` 走 backend 子分支（聚焦消费者画像/SLA/契约形态），`ship-shape` 自动跳过 |
| A + `frontend_only` | 允许 | `ship-discover` 走 frontend 子分支，`ship-shape` 正常激活 |
| B + `backend_only` | 允许 | 标准路径，跳过 `ship-frontend-design` |
| B + `frontend_only` | 允许 | 标准路径，跳过 `ship-backend-design` |
| C + `backend_only` | 允许 | `ship-discover` evolve 子分支聚焦 API surface 与消费者 |
| C + `frontend_only` | 允许 | `ship-discover` evolve 子分支聚焦组件/页面影响 |
| D + `backend_only` | 允许（材料类型确认） | D + backend_only 需要 PRD 同时具备契约级材料（OpenAPI / endpoint list / 接口文档 / API spec / message protocol / 消息协议 / CLI spec / SDK / request-response 等）。该材料类型会在 `ship-define-review` hard gate 复核；若只有产品 PRD，无接口或技术规约，默认建议降级为 B/interview 补齐契约信息 |
| D + `frontend_only` | 允许 | 标准路径 |

NEW_FEATURE 启动确认模板：
- 简述功能名称和目标
- 标明识别到的场景（A/B/C/D/E）及起点阶段
- 标明识别到的范围（fullstack / backend_only / frontend_only）及跳过的阶段
  - `backend_only` 时显式列出："将跳过 `ship-frontend-design`；若场景为 A/C，`ship-shape` 因 `backend_only` 路由跳过，不代表 UI 原型遗漏"
  - `frontend_only` 时显式列出："将跳过 `ship-backend-design`"
- 列出将要经历的大阶段序列（含 Discover 是否激活）
- 预估涉及的技术领域
- 标明下一次需要用户确认的门禁时点
- 若组合为 `D + backend_only`，必须做材料类型确认：用户提供的"PRD"应包含 OpenAPI / endpoint list / 接口文档 / API spec / message protocol / 消息协议 / CLI spec / SDK / request-response 等契约级材料；该确认会在 `ship-define-review` hard gate 复核，若仅有产品文档无技术规约，默认建议降级为 B（interview 模式）以补足契约信息
- 若场景为 E，必须额外按顺序展示：
  1. 技术方案来源与 selected scope。
  2. 未选中内容按 `ignored_source_policy: out_of_scope` 忽略。
  3. 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate。
  4. 直接进入 `ship-tech-discovery`，并执行 repository scan。
  5. `ship-tech-discovery` 开头派生最小 `requirements.md` index。
  6. 进入 `ship-contract` 前必须完成 `selected_scope_ac_confirmation`。
  7. 完成 contract 和按 scope 裁剪的 frontend/backend design。
  8. 进入 `ship-delivery-plan` 前必须通过 `ship-design-review`。
- 等待用户一句话确认（"好的""开始""go"等均视为确认）

## Process

```
用户输入
    │
    ▼
┌─────────────────────┐
│  意图识别 & 分类     │
│  NEW / CONTINUE /   │
│  INSPECT            │
└─────────┬───────────┘
          │
    ┌─────┼─────────────────┐
    │     │                 │
    ▼     ▼                 ▼
  NEW   CONTINUE         INSPECT
    │     │                 │
    ▼     ▼                 ▼
┌──────┐ ┌──────────┐  ┌──────────┐
│创建   │ │读取      │  │扫描所有   │
│feature│ │meta.yml  │  │feature   │
│目录   │ │定位阶段   │  │目录      │
└──┬───┘ └────┬─────┘  └────┬─────┘
   │          │              │
   ▼          ▼              ▼
┌──────┐ ┌──────────┐  ┌──────────┐
│初始化 │ │检查门禁   │  │输出状态   │
│meta  │ │条件      │  │汇总表    │
│.yml  │ │          │  │          │
└──┬───┘ └────┬─────┘  └──────────┘
   │          │
   ▼          ▼
┌─────────────────────┐
│  路由到目标阶段 skill │
│  传递 feature_dir    │
│  + context          │
└─────────────────────┘
```

## Stage Routing Rules

默认对外阶段视图（5 个大阶段，Discover 可选）：

```
[Discover →] Define → Design → Build → Close
```

内部阶段序列（14 个执行阶段，前 2 个条件性）：

```
[ship-discover → ship-shape →]
ship-define → ship-define-review [硬门禁]
→ ship-tech-discovery
→ ship-contract → ship-frontend-design → ship-backend-design
→ ship-design-review [硬门禁]
→ ship-delivery-plan
→ ship-plan-review [硬门禁]
→ ship-build → ship-verify → ship-handoff
```

各阶段入口/出口条件：

| 阶段 | 入口条件 | 出口产物 | 出口条件 |
|------|---------|---------|---------|
| ship-discover | 场景 A/C 确认启动 | product-brief.md | frontmatter stage_status: ready |
| ship-shape | product-brief.md ready + feature 有 UI + 无外部 UIUX | design-brief.md + resource/wireframes/ | stage_status: ready + 3+ 变体验证通过 |
| ship-define | NEW_FEATURE 确认启动（场景 B）或 ship-discover/ship-shape 完成；场景 E 跳过 | requirements.md | frontmatter stage_status: ready |
| ship-define-review | requirements.md 存在且 stage_status: ready；场景 E 跳过 | review-define.md | review_status: approved + user_sign_off/signed_at |
| ship-tech-discovery | review-define.md review_status: approved；或场景 E 已提供 technical_plan_source selected scope | tech-research.md + tech-selection.md；场景 E 同时派生 requirements.md index | 两份产物均 `stage_status: ready`；场景 E 还要求 derived `requirements.md.stage_status: ready` |
| ship-contract | tech-selection.md ready | api-contract.md | stage_status: ready |
| ship-frontend-design | api-contract.md ready；不要求 backend-design 已完成 | frontend-design.md | stage_status: ready |
| ship-backend-design | api-contract.md ready；不要求 frontend-design 已完成 | backend-design.md | stage_status: ready |
| ship-design-review | `project_scope` 对应设计文档 ready（fullstack: frontend+backend；backend_only: backend；frontend_only: frontend） | review-design.md | review_status: approved + user_sign_off/signed_at |
| ship-delivery-plan | review-design.md review_status: approved | `project_scope` 对应 plan（fullstack: frontend+backend+sync；backend_only: backend；frontend_only: frontend） | 对应 plan `stage_status: ready`，fullstack 还要求 sync 完成 |
| ship-plan-review | `project_scope` 对应 plan ready | review-plan.md | review_status: approved + user_sign_off/signed_at |
| ship-build | review-plan.md review_status: approved | 代码产物 | 所有 task 完成 |
| ship-verify | ship-build 完成 | verification.md | `stage_status: ready` |
| ship-handoff | verification.md stage_status: ready | handoff.md + verification.md | `handoff.md` 完成且 `verification.md stage_status: complete` |

并行规则：
- ship-frontend-design 和 ship-backend-design 是 sibling stages，可并行执行；fullstack 下任一侧启动只依赖 api-contract.md ready，另一侧不作为启动前置，ship-design-review 才统一收口两侧设计产物
- ship-tech-discovery 阶段内固定顺序：research → selection
- ship-delivery-plan 阶段内固定顺序：frontend → backend → sync
- ship-build 正式任务保持单 `DOING`；只读准备、验证和证据支线才允许辅助委派
- ship-verify 可按 backend unit / backend integration / backend contract / frontend component / frontend E2E 分轨并行，但 `verification.md` 仍由主上下文统一归档

Macro stage 映射：
- `Discover`（条件性）：`ship-discover`, `ship-shape`
- `Define`：`ship-define`, `ship-define-review`
- `Design`：`ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review`
- `Build`：`ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify`
- `Close`：`ship-handoff`

`Discover` 是条件性大阶段：`ship-discover` 只在场景 A/C 出现；`ship-shape` 默认随 A/C 出现。场景 B/D 默认跳过 Discover，但若 UIUX Material Gate 中用户显式授权生成线框，可临时插入 `ship-shape`（不执行 `ship-discover`）。场景 E、backend_only、无 UI 禁止 `ship-shape`。场景 D 与 B 的区别在于 `ship-define` 的执行模式：D 走 `prd_direct`（零提问纯提取），B 走 `interview`（多轮采访）。

### Workflow Path

默认路径固定为 `[Discover →] Define → Design → Build → Close`。

- 场景 A/C 内部执行 14 个阶段（含 Discover 前置）；场景 B/D 跳过 Discover 直接从 Define 开始
- 场景 E 直接从 `ship-tech-discovery` 开始，但仍保留后续设计评审、交付计划和计划评审
- 所有硬门禁必须通过：`ship-define-review`、`ship-design-review`、`ship-plan-review`（场景 E 跳过 define gate）
- Build 必须消费经过 `ship-plan-review` 审批的 `frontend-plan.md` / `backend-plan.md`
- 所有文档产物必须按 `project_scope` 完整产出；单侧 scope 只裁剪不适用侧，不跳过上游治理

### 路由分发机制

调度器路由到阶段 skill 时传递的上下文包：
- feature_dir：feature 目录绝对路径
- current_stage：当前阶段标识
- macro_stage：当前大阶段标识与摘要
- delegation：当前 feature 的子代理偏好（default_mode / ask flags / node_overrides；override 值为 current_context / assistive_subagent / parallel_subagent / gate_check_subagent）
- project_context：unknown / existing_project / new_project
- project_scope：fullstack / backend_only / frontend_only
- tech_stack：已确定的技术栈信息（可能为空）
- spec_context：最近一次规范解析结果摘要（index_status / referenced_spec_ids / warnings / pending_proposals）
- upstream_docs：上游阶段产出文档路径列表
- current_part：双产物阶段内的子段索引（如 `research` / `selection` / `frontend` / `backend` / `sync`）

阶段 skill 完成后必须回调调度器：
- 先读取对应产物 frontmatter，确认事实状态
- 将 `meta.yml` 中对应阶段状态回写为摘要状态（如 `ready` / `approved` / `completed`）
- 更新 `current_stage` 为下一阶段 canonical stage id
- 若当前阶段为双产物阶段，同步刷新对应 `current_part`
- 同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`
- 若发现 `meta.yml` 与产物 frontmatter 不一致，优先修正 `meta.yml`
- 若进入 `ship-tech-discovery / ship-frontend-design / ship-backend-design / ship-build / ship-handoff`，先刷新 `meta.yml.spec_context` 再传递上下文
- 若命中配置驱动节点或子代理决策节点，先读取 `meta.yml.delegation` 判定是自动解析执行方式还是询问用户
- 若当前阶段存在 unresolved blocking `ship-grill-me` question，不得推进下一阶段；若只剩 non-blocking grill question，必须作为 Open Questions / Risk 传递并写清影响范围

### Delegation Model

orchestrator 是唯一状态推进者。子代理只是执行策略，不是额外阶段。

委派原则：

- `parallel_owned_outputs`：只用于 `ship-frontend-design` / `ship-backend-design`
- `gate_check_switchable`：只用于 `ship-define-review` / `ship-design-review` / `ship-plan-review`
- `assistive_only`：用于 research 取证、计划审计、测试分轨、证据整理等辅助工作
- `forbidden`：共享契约、正式 gate、正式状态推进点不委派
- `user_gate_only`：`approved / rejected / revision_needed`、`ship-build` 是否继续、`ship-handoff` 是否关闭等决策必须由用户作出

补充约定：

- `Delegation Modes` 描述节点能力边界
- `node_overrides` 记录运行时执行选择值
- `node_overrides` 合法值固定为 `current_context | assistive_subagent | parallel_subagent | gate_check_subagent`
- `node_overrides` 的 key 必须来自共享协议定义的 canonical `node_id`
- `delegation.warnings` 专门记录委派解析告警，不复用 `spec_context.warnings`
- 节点是否接受某个 override 值，由该节点自己的运行时规则决定

节点级行为：

1. `ship-contract` 完成后：默认询问是否并行启动前后端设计子代理
2. `ship-plan-review` 通过后：默认询问是否开启 build 辅助委派模式
3. `ship-build` 每个 verified slice 完成后：默认询问下一个正式任务继续由当前上下文执行，还是附带启动只读准备/验证子代理
4. `ship-verify` 入口：默认询问是否按测试轨道分派子代理
5. `ship-handoff` 收尾前：只询问 accept / follow-up / proposal 处理，不委派关闭判定

canonical `node_id` 摘要：

- pre-Define stage 级（条件性）：`ship-discover`、`ship-shape`
- stage 级：`ship-define`、`ship-define-review`、`ship-contract`、`ship-frontend-design`、`ship-backend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`
- substage 级：`ship-tech-discovery.research`、`ship-tech-discovery.selection`
- build 辅助节点：`ship-build.read-next-task`、`ship-build.spec-scan`、`ship-build.env-precheck`、`ship-build.evidence-pack`
- verify 测试轨：`ship-verify.backend-unit`、`ship-verify.backend-integration`、`ship-verify.backend-contract`、`ship-verify.frontend-component`、`ship-verify.frontend-e2e`
- handoff 辅助节点：`ship-handoff.ac-evidence`、`ship-handoff.deploy-materials`、`ship-handoff.spec-proposals`

自动委派解析规则：

- `forbidden` 节点不可启动任何子代理；若存在 override，记录 warning 后强制回退 `current_context`
- `parallel_owned_outputs` 只接受 `current_context | parallel_subagent`
- `assistive_subagent` 不得在 `parallel_owned_outputs` 节点上被解释成 `parallel_subagent`
- `assistive_only` 只接受 `current_context | assistive_subagent`
- 当 `ask_on_parallel_stage = false` 时，只有显式 `node_overrides[node_id] = parallel_subagent` 才能自动委派；否则回退 `current_context`
- 当 `ask_on_assistive_node = false` 时，`assistive_only` 节点可在 override 缺失时回落到 `default_mode`
- 用户对某个节点的临时回答写入 `node_overrides[node_id]`；只有用户明确说“以后默认都这样”时才更新 `default_mode`

hard gate 的运行时模型：

- `current_context`：主代理直接执行 gate 检查并写正式 `review-*.md`
- `gate_check_subagent`：子代理执行 gate 检查并直接写正式 `review-*.md` 草案
- hard gate 的执行方式先读 `node_overrides[stage]`，再读 `default_mode`，最后回退 `current_context`
- 对 hard gate 而言，`assistive_subagent` 解释为 `gate_check_subagent`
- 对 hard gate 而言，`parallel_subagent` 是无效值；记录 warning 后回退
- 无论哪种方式，主代理都必须重新读取正式 gate 文档并复核
- 只有主代理可以把 `review_status` 从 `pending` 改成终态；等待用户批准时正式 frontmatter 仍保持 `pending`，可在正文记录 `recommended_status`
- 若主代理判断可通过，只有在用户明确批准后，才能一次性写入 `review_status: approved`、`user_sign_off` 和 `signed_at`
- 三个 hard gate 的执行方式复用 `node_overrides` 与 `default_mode`，不再每次进入都单独询问

写权限约束：

- 子代理不得修改 `meta.yml`
- 子代理可以起草正式 `review-*.md`，但 gate frontmatter 的最终结论必须由主代理确认
- 子代理起草正式 gate 文档时，必须保持 `review_status: pending`，且 `user_sign_off`、`signed_at` 为空
- `assistive_only` 子代理不得直接改正式产物的正文、`stage_status` / `review_status`
- 只有主上下文可以合并子代理结果并推进 `current_stage`

### Assistive Questioning

`ship-grill-me` 是辅助质询 hook，不是 delegation mode 的新取值，不写入 `node_overrides`，也不改变 5 个 macro stages 或 14 个 canonical stages。orchestrator 在进入允许节点时，可根据用户请求、阶段风险或未关闭的 blocking gap 使用它做逐题压力测试。

推荐接入点：

1. `ship-discover.pre-ready`：方案选择后、`product-brief.md` ready 前。
2. `ship-shape.pre-selection`：3+ wireframe / design variants 产出并浏览器验证后、用户选定方向前。
3. `ship-define.pre-ready`：`requirements.md` 成稿后、ready 前。
4. `ship-tech-discovery.selected-scope-ac-confirmation` 与 `ship-tech-discovery.research-alignment`：selected scope AC 确认前，或 Research Alignment Check 发现影响 contract / design 的 unknown 时。
5. `ship-frontend-design.pre-ready` / `ship-backend-design.pre-ready`：各自设计文档 ready 前；因这两个阶段是 `parallel_owned_outputs`，grill 由当前产物 owner 内部执行，不能另启 `assistive_subagent` 修改同一正式文档。
6. `ship-design-review.pre-signoff`：`review-design.md` 草案完成后、用户 approved 前。

禁止接入点：

- `ship-contract`
- `ship-tech-discovery.selection`
- `ship-delivery-plan`
- 任何正式状态推进动作

执行规则：

- 一次只问一个问题，并给出 recommended answer。
- 能从仓库、已有 feature 文档、API、DB、页面、权限或测试命令确认的问题，先探索证据，不问用户。
- grill 输出只能进入当前产物正文的 Grill Notes / Open Questions / Risk section，或 hard gate 正文中的 sign-off questions / risk acceptance candidates / conditions candidates。
- `ship-grill-me` 不替代 `review-*.md`，不得写 `review_status: approved`；`user_sign_off` 和 `signed_at` 仍必须由主上下文在用户明确批准后写入。

### Spec Hook Model

`ship-spec` 的 ownership 采用 Hybrid 模式：

- orchestrator：负责 workspace resolution，调用 `spec_runtime.py` / `feature_meta_runtime.py sync-spec`，维护 `meta.yml.spec_context`，把规范摘要透传给阶段 skill
- 阶段 skill：根据 `spec_context` 和本阶段输入实际读取规范，并把 `referenced_spec_ids`、`spec_warnings`、`spec_checked_at` 写入产物或任务证据
- `ship-handoff`：只记录 proposal，不直接写回 workspace `spec_root`；真正沉淀由用户确认后执行

workspace resolution 规则：

- NEW_FEATURE 创建 feature 前必须先通过 Workspace Config Gate
- NEW_FEATURE / CONTINUE_FEATURE / `sync-spec` 都以 workspace 为边界，而不是当前 cwd
- 显式配置源是 workspace `.docs/ship/project.yml`
- project_group 下 feature 目录写入 workspace `feature_root`
- CONTINUE_FEATURE 优先信任已有 `meta.yml.spec_context.workspace_*` 字段，不重新按 cwd 猜测
- 无法确定 workspace 时阻塞；workspace 已确定但 spec 缺失时只 warning
- feature `projects` 是默认执行范围，不是硬安全边界

默认缺规策略：

- 缺少 `INDEX.md`、找不到匹配规范、规范 frontmatter 不合法时，记录 warning 并继续
- 只有用户显式要求严格模式时，缺规才升级为阻塞条件
- `ship-build` 和 `ship-handoff` 都需要汇总规范引用与待沉淀 proposal，不能因为需求较小而跳过规范检查

## Gate Protocol

### 硬门禁（Hard Gate）

适用阶段：ship-define-review、ship-design-review、ship-plan-review

执行规则：
1. 生成 review-<stage>.md 文档，包含以下必填字段：
   - reviewer：执行评审的角色（AI / 用户 / 两者）
   - checklist：评审检查项列表，每项标注 pass/fail/na
   - issues：发现的问题列表，含严重级别和处理建议
   - review_status：pending / approved / rejected / revision_needed
   - user_sign_off：用户确认文本
   - signed_at：用户确认时间戳
   - conditions：必须解决的条件列表（如有）
2. 只有 `review_status=approved` 且 `user_sign_off`、`signed_at` 非空时，才允许推进
3. 若 `rejected`：回退到对应的产出阶段重新执行
4. 若 `revision_needed`：列出必须解决的问题，解决后重新提交评审

### 软门禁（Soft Gate）

适用阶段：所有非硬门禁的阶段间过渡

执行规则：
1. 检查上游文档 frontmatter 中 stage_status 字段
2. stage_status: ready 或 complete → 允许推进
3. stage_status: draft → 提示用户当前阶段未完成，询问是否允许软门禁强制推进
4. 若 meta.yml.stages.<stage>.status 为 in_progress/blocked，但 artifact 已 ready，以 artifact frontmatter 为事实源并回写 meta.yml
5. 上游文档不存在 → 阻断，路由回上游阶段

### 门禁失败处理

- 硬门禁失败：必须回退，不可跳过，不可强制通过
- 软门禁失败：警告用户风险后，用户可选择强制推进（记录到 meta.yml 的 skip_log）
- hard gate 永远不可通过 skip_log 跳过或强制通过；必须产生正式 review 文档并满足 `approved + user_sign_off + signed_at`
- 连续两次门禁失败：建议用户重新审视需求或方案
- 评审产物缺失：阻断推进，路由回评审阶段重新生成

### 门禁文档 frontmatter 规范

每个评审产物必须包含 frontmatter，字段约定：
- stage：所属阶段标识
- gate_type：固定为 `hard`
- review_status：`pending / approved / rejected / revision_needed`
- reviewer：评审者标识
- reviewed_at：评审时间
- reviewed_documents：本轮评审涉及文档
- revision_count：重审次数
- user_sign_off：用户签字文本
- signed_at：签字时间戳（ISO 8601）
- conditions：若 `revision_needed`，列出待解决条件

调度器读取 frontmatter 后才判定门禁结果，正文内容仅作参考不影响判定。

## Feature Directory Initialization

NEW_FEATURE 模式下的目录创建流程：

1. 执行 Workspace Config Gate：读取当前目录 `.docs/ship/project.yml`；若不存在，暂停创建并询问 `single_project` 或 `project_group`
2. 若是 `project_group` 初始化，列举当前目录一级目录候选项目，排除隐藏目录、依赖目录和产物目录，用户确认后写入 `.docs/ship/project.yml`
3. 执行 Feature Scope Interview：确认短名，并在 `project_group` 下让用户选择本 feature 默认关联 projects
4. 若用户选择的新项目不在 workspace config 中，先检查同名一级目录；存在时询问是否追加到 `.docs/ship/project.yml.projects`
5. 根据用户输入提取功能短名（short-name），转换为 kebab-case
6. 生成日期前缀 YYYYMMDD（基于当前日期）
7. 在 workspace `feature_root` 下创建目录 `feature-YYYYMMDD-<short-name>/`
8. 创建 resource/ 子目录用于存放 PRD、原型、截图等参考资料
9. 复制 `./_templates/meta/meta.yml.template` 到 feature 目录，重命名为 `meta.yml`
10. 场景 B/D：复制 `./_templates/requirements/raw-prd-inbox.md.template` 到 `requirements.md`，复制 `./_templates/resource/README.md.template` 到 `resource/README.md`；场景 E 只复制 `resource/README.md`
11. 填充 meta.yml 初始字段：feature_name、feature_id、created_at、current_stage、workspace_mode、projects
12. 初始化 `macro_stage.current`、`macro_stage.label`
13. 初始化 `macro_stage.summary` 与 `macro_stage.next_user_decision`
14. 初始化 `delegation.default_mode: current_context`、`ask_on_parallel_stage: true`、`ask_on_assistive_node: true`
15. 初始化 `spec_context.workspace_mode / workspace_name / spec_root / feature_root / resolution_source`
16. 将所有阶段的 status 初始化为 pending
17. 场景 A：`current_stage: ship-discover`，不创建 raw `requirements.md` inbox，直接进入 `ship-discover`
18. 场景 B/D：将 `stages.ship-discover.status` 和 `stages.ship-shape.status` 设为 `skipped`，`current_stage: ship-define`，`stages.ship-define.status: blocked`，`block_reason: awaiting_materials`
19. 场景 D：将 `stages.ship-define.generation_mode` 设为 `prd_direct`；场景 B：设为 `interview`
20. 场景 C：若已有 feature/code 基线，`current_stage: ship-discover` 且 `discovery_mode: evolve`；若无基线，先询问，不创建目录
21. 场景 E：确认 `project_context: existing_project`，写入 `technical_plan_source`，将 `current_stage` 设为 `ship-tech-discovery`，将 `stages.ship-define.status` 和 `stages.ship-define-review.status` 设为 `skipped`，将 `stages.ship-define.generation_mode` 设为 `technical_plan`，不创建 raw `requirements.md` inbox

资料准备态解除规则：

1. 当用户说“资料放好了 / PRD 填好了”，检查 `requirements.md` 是否不是空 raw inbox 模板，或 `resource/` 下存在至少一个非 `README.md` 文件。
2. 若两者都为空，继续保持 `stages.ship-define.status: blocked` 和 `block_reason: awaiting_materials`，提示用户补资料。
3. 若存在资料，清空 `block_reason`，将 `stages.ship-define.status` 改为 `pending`。
4. 将控制权交给 `ship-define`；`ship-define` 启动后再将状态改为 `in_progress`。

短名生成规则：
- 优先使用用户输入中的功能名词
- 若用户未提供，从需求描述中提取核心动词+名词组合
- 长度控制在 2-5 个英文单词或拼音
- 避免特殊字符，仅保留字母数字和连字符

目录命名冲突处理：
- 同日同短名：追加 -v2、-v3 后缀
- 短名为空：使用 feature-YYYYMMDD-<timestamp> 兜底

## Resume Protocol

中断恢复流程（CONTINUE_FEATURE 模式）：

1. 优先读取已有 feature 的 `meta.yml.spec_context.workspace_*`
2. 在已解析的 workspace `feature_root` 下扫描 `feature-YYYYMMDD-*` 目录
3. 读取每个 feature 的 meta.yml，过滤出 `ship-handoff` 尚未 `completed` 的活跃 feature
4. 若只有一个进行中的 feature：也必须询问用户是否继续这个 feature，不能自动选中
5. 若有多个：列表展示（功能名 / 当前大阶段 / 最后更新时间），让用户选择
6. 若无活跃 feature：提示用户是否启动新功能或查看历史 feature
7. 读取选中 feature 的 meta.yml
8. 根据 current_stage 和该阶段 status 判断恢复点：
   - status: completed → 检查门禁后推进到下一阶段
   - status: in_progress → 恢复当前阶段（传递已有产物作为上下文）
   - status: approved / ready → 检查门禁后推进到下一阶段
   - status: blocked → 报告阻塞原因，询问用户决策（解除阻塞 / 切换 feature / 终止）
   - status: pending → 路由到该阶段重新启动
9. 检查门禁条件后路由到目标阶段 skill

恢复时的默认输出：
- 优先报告 `macro_stage.label`
- 说明当前阶段目标与下一次用户确认点
- 仅在用户要求详情或遇到阻塞时展开 `current_stage`

恢复时的上下文传递：
- 将 feature 目录绝对路径作为 feature_dir 传递
- 将 meta.yml 中的 tech_stack 和 project_context 作为环境信息传递
- 将 meta.yml 中的 delegation 偏好透传给目标阶段 skill
- 将当前阶段已有的文档内容作为续写上下文传递
- 若当前阶段为双产物阶段，将 `current_part` 一并透传给目标阶段 skill

恢复时的状态校验：
- 若 meta.yml 中 current_stage 与实际文档产出不一致（如 current_stage 为 `ship-tech-discovery` 但 `tech-research.md` 不存在），优先信任文件系统状态，回退 current_stage
- 若发现孤立产物（如存在 frontend-plan.md 但无 review-design.md），警告用户并询问处理方式
- 若 `meta.yml` 摘要状态与产物 frontmatter 冲突，优先信任产物 frontmatter 并回写 `meta.yml`

## Inspect Protocol

INSPECT_FEATURES 模式输出规范：

汇总表格列：
- 功能名（feature_name）
- 创建时间（created_at）
- 当前大阶段（macro_stage.label）
- 当前内部阶段（current_stage，仅高级视图显示）
- 整体进度（已完成阶段数 / 总阶段数）
- 状态标识（in_progress / blocked / completed / abandoned）

排序规则：进行中 > 阻塞 > 待评审 > 已完成 > 已废弃，同状态内按 updated_at 倒序。

输出后追加可选行动建议：
- 进行中 feature：提示可输入"继续 <name>"恢复
- 阻塞 feature：提示阻塞原因摘要
- 已完成 feature：提示可查看 handoff.md 总结

## Anti-Rationalizations

| 编号 | 禁止行为 | 正确做法 |
|------|---------|---------|
| AR-1 | "用户说快点做，所以跳过评审" | 硬门禁不可跳过。需求较小时可以压缩产物正文，但不能跳过 Design、Plan 和 Review |
| AR-2 | "需求很简单，不需要走完整流程" | 即使简单需求，也必须走标准路径；评审可简化但不可省略 |
| AR-3 | "上一阶段的文档差不多了，先往下走" | 软门禁要求 stage_status: ready。"差不多"不等于 ready，必须明确标记 |
| AR-4 | "用户没说要恢复哪个 feature，我猜一个" | 多个 feature 时必须列表让用户选择，不可自行假设 |
| AR-5 | "这个阶段 skill 不存在，跳过" | 阶段 skill 缺失时报告错误，不可静默跳过。建议用户手动完成该阶段产物 |

## Verification

退出 checklist（调度器每次路由前自检）：

- [ ] 已正确识别用户意图并分类为 NEW / CONTINUE / INSPECT
- [ ] NEW 模式：feature 目录已创建，meta.yml 已初始化，用户已确认执行计划
- [ ] CONTINUE 模式：已读取 meta.yml，已定位 current_stage / macro_stage，已验证门禁条件
- [ ] INSPECT 模式：已扫描所有 feature 目录，已输出状态汇总
- [ ] 路由目标阶段 skill 存在且可调用
- [ ] 已将 feature_dir 和必要上下文传递给目标阶段 skill
- [ ] 若命中委派决策节点，已按 `meta.yml.delegation` 执行询问或套用覆盖策略
- [ ] meta.yml 的 current_stage 与 macro_stage 已同步更新为即将执行的阶段
- [ ] 未跳过任何硬门禁
- [ ] 软门禁跳过已记录到 meta.yml 的 skip_log（如有）
