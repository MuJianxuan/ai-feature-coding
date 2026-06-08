---
name: ship-orchestrator
description: "ShipKit orchestrator. Routes and enforces workflow stages for feature development. When triggered, do not write implementation code until workflow gates reach ship-build and build preflight passes; direct coding requires explicitly exiting ShipKit."
---

# Workflow Orchestrator

## Overview

Workflow Orchestrator 是开发工作流 skills 套件的总调度器，负责入口判断、阶段推断和路由分发。它不执行具体阶段工作，而是识别用户意图后将控制权交给对应的阶段 skill。

本 skill 支持三种入口模式：NEW_FEATURE（启动新功能开发）、CONTINUE_FEATURE（恢复中断的功能开发）、INSPECT_FEATURES（查看功能状态总览）。调度器通过读取 `meta.yml.current_stage`、`meta.yml.macro_stage`、各产物 frontmatter 和 `meta.yml` 摘要状态来判断当前位置，并根据门禁规则决定是否允许推进到下一阶段。

设计原则是"放宽触发、严格推进"——用户无需记住 14 个内部阶段名，只要表达出开发意图，调度器就能识别并给出 5 个大阶段视图下的执行摘要。内部仍然按细阶段和门禁推进，但默认对外只展示：当前大阶段、当前目标、下一次需要用户确认的动作。

协议约束：
- Canonical stage id、门禁字段、`verification.md` ownership 统一以 [`workflow-protocol.md`](./_templates/protocol/workflow-protocol.md) 为准
- 阶段文档 frontmatter 是事实源；`meta.yml` 仅是 orchestrator 索引层
- 若产物 frontmatter 与 `meta.yml` 摘要冲突，先读取产物确认事实，再用 `sync_meta_from_artifacts(feature_dir)` 生成回写建议；不得只凭 stale meta 推进
- 默认对外展示 `macro_stage`，只在高级模式和诊断模式下展开 `current_stage`

## Non-Negotiable Runtime Guard

当本 skill 被触发：

- 通用"用户要改代码就直接实现"的默认行为失效。
- 不得写业务代码，除非同时满足：
  - `current_stage == ship-build`
  - `review-plan.md` 为 `review_status: approved`
  - `review-plan.md.user_sign_off` 非空
  - `review-plan.md.signed_at` 非空
  - `stage_transition_check.py --target-stage ship-build` 通过
  - `implementation_preflight.py` 通过
  - 当前 DOING task 的 `allowed_files` 覆盖要修改的文件
- 用户说"确认""对""是的""直接做""先开发"不等于 build 授权。
- scope、接口范围、AC、selected scope 的确认只允许推进当前 workflow stage，不允许直接进入实现。
- 若用户要求跳过 ShipKit 直接编码，必须先让用户明确退出 ShipKit；在 ShipKit 内不得开后门。

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

## Empty Entry Handling

当用户只表达"开始需求 / 使用 ship-orchestrator / 继续开发"等意图，但没有指定 `feature_dir`、也没有携带资料时，必须先执行以下流程：

1. 若当前上下文已能确定 workspace，则扫描该 workspace `feature_root/feature-*`；否则先执行 Workspace Config Gate
2. 过滤 `lifecycle_status: active | blocked` 的未完成 feature
3. 若有多个未完成 feature：列表展示（功能名 / 当前大阶段 / updated_at / 阻塞原因），让用户选择继续哪个，或选择新建
4. 若只有一个未完成 feature：也必须询问"是否继续这个 feature，还是新建？"，不可自动进入
5. 若没有未完成 feature：直接列出五种新建模式，让用户选择

五种新建模式展示文案：

```text
请选择进入方式：
1. PRD 直通：你已有完整 PRD，想直接粘贴/放资料，不做需求采访。
2. 产品提供：你有 PRD/原型/设计稿，但允许我继续澄清缺口。
3. 零到一：你只有想法，需要先头脑风暴产出需求。
4. 迭代增强：基于已有功能、feature 目录或代码路径做增强。
5. 技术方案选区：你已有技术方案，只围绕指定章节/接口/模块生成计划。
```

不要在"用户未携带资料"的入口里自行猜测模式。模式选择是用户显式决策点。

## Scenario Detection

NEW_FEATURE 确认启动前，必须先判定场景，决定是否进入 Discover 大阶段。详细场景判定规则参见 [scenario-detection.md](./_templates/protocol/scenario-detection.md)。

**5 种场景摘要**：

| 场景 | 入口信号 | 起点 stage |
|------|---------|------------|
| A 零到一 | 只有想法、无附件、无引用已有代码 | `ship-discover`（greenfield） |
| B 产品提供 | 附了 PRD/Figma/原型/UIUX 文档 | `ship-define`（interview mode） |
| C 迭代增强 | 引用已有 feature 目录或具体代码路径 | `ship-discover`（evolve） |
| D PRD 直通 | 附了完整 PRD + 原型/设计稿，明确不需要需求录入 | `ship-define`（prd_direct mode） |
| E 技术方案选区入口 | 提供已有技术方案文件或粘贴片段，并指定章节/接口/模块 | `ship-tech-discovery`（technical plan entry） |

**关键规则**：
- 信号歧义时**必须显式询问用户**场景，不允许猜测
- 场景 E 只跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate；仍必须按顺序执行 `ship-tech-discovery → ship-contract → ship-backend-design / ship-frontend-design（按 scope 裁剪） → ship-design-review → ship-delivery-plan → ship-plan-review → ship-build`
- `backend_only` 仅跳过 `ship-frontend-design`，不跳过 `ship-contract`、`ship-backend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`
- selected scope 确认、接口列表确认、响应结构确认都不是 `ship-build` 授权

## Scope Detection

NEW_FEATURE 确认启动前，在场景识别之后，必须判定项目范围。详细范围识别规则参见 [scope-detection.md](./_templates/protocol/scope-detection.md)。

**三种范围摘要**：

| 范围 | 入口信号 | 跳过阶段 |
|------|---------|---------|
| `fullstack`（默认） | 描述涉及前后端、或未明确声明 | 无 |
| `backend_only` | 明确说"纯后端""只做 API""不涉及前端" | `ship-frontend-design` |
| `frontend_only` | 明确说"纯前端""只做 UI""不涉及后端" | `ship-backend-design` |

**关键规则**：
- 信号歧义时默认 `fullstack`，必须显式询问用户是否要落成单侧 scope
- `backend_only` 只裁剪前端阶段，不裁剪上游治理（contract/backend design/review/plan）
- scope 变更只允许在 `ship-design-review` 之前；通过设计评审后 scope 冻结

## Source Code Edit Barrier

orchestrator 必须把 workflow 产物推进和业务源码修改分开处理。除 workspace `feature_root` 下 `feature-*` 目录内的工作流产物、`meta.yml`、`resource/` 资料和 review / plan / discovery / design 文档外，任何业务源码、测试、配置、迁移、脚本或构建文件修改都只允许在 `ship-build` 阶段发生。

在准备修改非 workspace `feature_root/feature-*` 文件前，必须先运行 `implementation_preflight.py` 确认：

1. `meta.yml.current_stage == ship-build`
2. `review-plan.md.review_status == approved`
3. `review-plan.md.user_sign_off` 非空
4. `review-plan.md.signed_at` 非空
5. `python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature-dir> --target-stage ship-build` 通过
6. `python3 skills/ship-orchestrator/scripts/build_task_preflight.py <feature-dir> --project-scope <fullstack|backend_only|frontend_only>` 通过
7. `python3 skills/ship-orchestrator/scripts/implementation_preflight.py <feature-dir> --project-scope <fullstack|backend_only|frontend_only>` 通过

若任一条件不满足，必须停止源码修改，报告当前阶段和缺失门禁，并路由回对应阶段。

**实施前置检查**：

在以下操作前必须先运行 `implementation_preflight.py`：
- `apply_patch` 修改业务代码
- 新增 controller / service / DTO / mapper / XML
- 修改测试以适配新增实现
- 生成或更新 API 文档

preflight 不通过时，只允许编辑当前 stage 的 workflow 文档，不允许编辑业务代码。

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
│场景   │ │读取      │  │扫描所有   │
│识别   │ │meta.yml  │  │feature   │
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

## Stage Routing

详细阶段路由规则参见 [stage-routing.md](./_templates/protocol/stage-routing.md)。

**对外视图（5 个大阶段）**：

```
[Discover →] Define → Design → Build → Close
```

**内部阶段序列（14 个执行阶段）**：

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

**Macro stage 映射**：
- `Discover`（条件性）：`ship-discover`, `ship-shape`
- `Define`：`ship-define`, `ship-define-review`
- `Design`：`ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review`
- `Build`：`ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify`
- `Close`：`ship-handoff`

## Gate Protocol

详细门禁协议参见 [gate-protocol.md](./_templates/protocol/gate-protocol.md)。

**硬门禁（Hard Gate）**：
- 适用阶段：`ship-define-review`、`ship-design-review`、`ship-plan-review`
- 通过条件：`review_status: approved` + `user_sign_off` 非空 + `signed_at` 非空
- 硬门禁失败：必须回退，不可跳过，不可强制通过

**软门禁（Soft Gate）**：
- 适用阶段：所有非硬门禁的阶段间过渡
- 通过条件：`stage_status: ready` 或 `complete`
- 软门禁失败：警告风险后用户可选择强制推进（记录 skip_log）

## Feature Lifecycle

### NEW_FEATURE（新建模式）

详细初始化流程参见 [feature-initialization.md](./_templates/protocol/feature-initialization.md)。

**核心流程**：
1. 执行 Workspace Config Gate
2. Feature Scope Interview
3. 生成功能短名和日期前缀
4. 创建 `feature-YYYYMMDD-<short-name>/` 目录
5. 复制模板文件（meta.yml、resource/README.md、requirements.md）
6. 填充 meta.yml 初始字段
7. 根据场景设置起点 stage
8. 生成启动确认摘要
9. 等待用户确认后路由到起点阶段

### CONTINUE_FEATURE（恢复模式）

详细恢复流程参见 [resume-protocol.md](./_templates/protocol/resume-protocol.md)。

**核心流程**：
1. 读取 workspace context
2. 扫描活跃 feature
3. 用户选择（即使只有一个也必须询问）
4. 读取 meta.yml
5. 判断恢复点（根据 current_stage 和 status）
6. 检测非法提前实现
7. 检查门禁条件后路由

**Implementation Before Gate Detection**：

恢复 feature 时，如果发现已有业务代码改动，但 feature 未满足 `ship-build` 前置条件：
1. 不继续编辑代码
2. 报告 `workflow_violation: implementation_before_plan_review`
3. 列出缺失 stage / gate
4. 回退到应执行的 current_stage，补齐 workflow 产物
5. 若用户要求继续直接编码，必须让用户先明确退出 ShipKit

handoff summary 或上下文摘要声称"已实现"时，不可直接信任。必须读取 `meta.yml`、stage artifacts 和 gate frontmatter；若缺少 `review-plan.md approved + user_sign_off + signed_at`，不得继续实现或验证新增代码。

### INSPECT_FEATURES（查看模式）

汇总表格列：功能名、创建时间、当前大阶段、整体进度、状态标识。

排序规则：进行中 > 阻塞 > 待评审 > 已完成 > 已废弃，同状态内按 updated_at 倒序。

## Routing & Delegation

详细路由和委派规则参见 [routing-protocol.md](./_templates/protocol/routing-protocol.md)。

**路由上下文传递**：feature_dir、current_stage、macro_stage、delegation、project_context、project_scope、tech_stack、spec_context、upstream_docs、current_part。

**Delegation Modes**：
- `parallel_owned_outputs`：只用于 `ship-frontend-design` / `ship-backend-design`
- `gate_check_switchable`：只用于三个硬门禁
- `assistive_only`：辅助工作（research、audit、testing、evidence）
- `forbidden`：共享契约、正式 gate、正式状态推进点
- `user_gate_only`：批准/拒绝/继续/关闭等决策必须由用户作出

### Assistive Questioning

`ship-grill-me` 是辅助质询 hook，不是 delegation mode 的新取值，不改变阶段序列。推荐接入点：`ship-discover.pre-ready`、`ship-shape.pre-selection`、`ship-define.pre-ready`、`ship-tech-discovery.selected-scope-ac-confirmation`、`ship-design-review.pre-signoff`。禁止接入点：`ship-contract`、`ship-tech-discovery.selection`、`ship-delivery-plan`。执行规则：一次只问一个问题，grill 输出只能进入当前产物的 Grill Notes / Open Questions / Risk section，或 hard gate 正文中的 sign-off questions。`ship-grill-me` 不替代 `review-*.md`，不得写 `review_status: approved`。

## Anti-Rationalizations

| 编号 | 禁止行为 | 正确做法 |
|------|---------|---------|
| AR-1 | "用户说快点做，所以跳过评审" | 硬门禁不可跳过。需求较小时可以压缩产物正文，但不能跳过 Design、Plan 和 Review |
| AR-2 | "需求很简单，不需要走完整流程" | 即使简单需求，也必须走标准路径；评审可简化但不可省略 |
| AR-3 | "上一阶段的文档差不多了，先往下走" | 软门禁要求 stage_status: ready。"差不多"不等于 ready，必须明确标记 |
| AR-4 | "用户没说要恢复哪个 feature，我猜一个" | 多个 feature 时必须列表让用户选择，不可自行假设 |
| AR-5 | "这个阶段 skill 不存在，跳过" | 阶段 skill 缺失时报告错误，不可静默跳过。建议用户手动完成该阶段产物 |
| AR-6 | "用户确认了范围问题，所以可以编码" | 范围确认只推进 workflow stage，不授权 `ship-build` |
| AR-7 | "场景 E 有技术方案，所以可以跳过设计和计划" | 场景 E 只跳过 define 执行和 define review，不跳过 design review / delivery plan / plan review |
| AR-8 | "backend_only 只做接口，所以不需要 contract/design/review/plan" | backend_only 只裁剪前端阶段，不裁剪上游治理 |
| AR-9 | "上下文摘要说代码已实现，所以继续验证即可" | 先检查 gate；未过 `ship-plan-review` 则停止继续代码操作 |
| AR-10 | "用户说直接做，所以 ShipKit 内可以开后门" | ShipKit 内不允许强制跳过；直接编码必须先退出 ShipKit |

## Verification

退出 checklist（调度器每次路由前自检）：

- [ ] 已正确识别用户意图并分类为 NEW / CONTINUE / INSPECT
- [ ] NEW 模式：feature 目录已创建，meta.yml 已初始化，用户已确认执行计划
- [ ] CONTINUE 模式：已读取 meta.yml，已定位 current_stage / macro_stage，已验证门禁条件，已检测非法提前实现
- [ ] INSPECT 模式：已扫描所有 feature 目录，已输出状态汇总
- [ ] 路由目标阶段 skill 存在且可调用
- [ ] 已将 feature_dir 和必要上下文传递给目标阶段 skill
- [ ] 若命中委派决策节点，已按 `meta.yml.delegation` 执行询问或套用覆盖策略
- [ ] meta.yml 的 current_stage 与 macro_stage 已同步更新为即将执行的阶段
- [ ] 未跳过任何硬门禁
- [ ] 软门禁跳过已记录到 meta.yml 的 skip_log（如有）
- [ ] 若进入 `ship-build`，已运行 `implementation_preflight.py` 并通过

## References

详细协议文档：
- [scenario-detection.md](./_templates/protocol/scenario-detection.md) - 5 种场景详细判定规则
- [scope-detection.md](./_templates/protocol/scope-detection.md) - project_scope 判定矩阵与冻结协议
- [stage-routing.md](./_templates/protocol/stage-routing.md) - 14 阶段路由规则与并行规则
- [routing-protocol.md](./_templates/protocol/routing-protocol.md) - 路由分发、委派模型、辅助质询、Spec Hook
- [gate-protocol.md](./_templates/protocol/gate-protocol.md) - 硬门禁与软门禁完整规则
- [feature-initialization.md](./_templates/protocol/feature-initialization.md) - NEW_FEATURE 初始化详细步骤
- [resume-protocol.md](./_templates/protocol/resume-protocol.md) - CONTINUE 恢复详细逻辑与非法实现检测
- [workflow-protocol.md](./_templates/protocol/workflow-protocol.md) - Canonical 定义与共享约定
