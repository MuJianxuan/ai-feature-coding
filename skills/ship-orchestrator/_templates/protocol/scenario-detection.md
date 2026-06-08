# Scenario Detection Protocol

本协议定义 ship-orchestrator 在 NEW_FEATURE 模式下如何识别 5 种入口场景。

## 5 种场景概览

| 场景 | 入口信号 | 起点 stage | Discover 大阶段 |
|------|---------|------------|-----------------|
| A 零到一 | 用户只有一句话想法、无附件、无引用已有代码 | `ship-discover`（greenfield） | 激活 |
| B 产品提供 | 用户附了 PRD/Figma/原型/UIUX 文档，或选择先创建目录后补资料 | `ship-define`（interview mode） | 默认跳过；UIUX Gate 可插入 `ship-shape` |
| C 迭代增强 | 用户引用已有 feature 目录或具体代码路径并描述变更 | `ship-discover`（evolve） | 激活 |
| D PRD 直通 | 用户附了完整 PRD + 原型/设计稿，或选择先创建目录粘贴完整 PRD，且明确表示不需要需求录入 | `ship-define`（prd_direct mode） | 默认跳过；UIUX Gate 可插入 `ship-shape` |
| E 技术方案选区入口 | 用户提供已有技术方案文件或粘贴片段，并指定章节、接口、模块或标题；明确这是已有项目迭代；`scenario: technical_plan_provided` | `ship-tech-discovery`（technical plan entry） | 跳过 |

## 场景判定规则

### 场景 A（零到一）

**入口信号**：
- 用户只有一句话想法或简短描述
- 无 PRD、原型、设计稿等附件
- 未引用已有 feature 目录或代码路径
- 未提供技术方案

**meta.yml 设置**：
- `scenario: greenfield`
- `discovery_mode: greenfield`
- `current_stage: ship-discover`
- `stages.ship-discover.status: pending`
- `stages.ship-shape.status: pending`（若涉及 UI）

**初始化行为**：
- 不创建 raw `requirements.md` inbox
- 直接进入 `ship-discover`
- 激活 Discover 大阶段

### 场景 B（产品提供）

**入口信号**：
- 用户附了 PRD/Figma/原型/UIUX 文档
- 或用户选择"产品提供"模式，先创建目录后补资料
- 允许继续澄清需求缺口

**meta.yml 设置**：
- `scenario: product_provided`
- `current_stage: ship-define`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`（默认）
- `stages.ship-define.generation_mode: interview`
- `stages.ship-define.status: blocked`，`block_reason: awaiting_materials`（若先创建目录）

**初始化行为**：
- 创建 raw `requirements.md` inbox
- 创建 `resource/README.md`
- 若已有材料，直接进入 `ship-define`
- 若先创建目录，保持 blocked 态等待用户补材料

**UIUX Material Gate**：
- 若 `project_scope = fullstack | frontend_only` 且 feature 涉及 UI
- 必须检查 UIUX 材料覆盖度：
  - `sufficient`：材料可访问，覆盖主流程、关键页面/状态、核心异常路径 → 继续
  - `partial`：可访问但只覆盖部分页面 → 继续，但记录 UIUX risk
  - `screenshot_only`：只有截图 → 主流程完整时继续，否则按 `partial` 处理
  - `inaccessible`：链接打不开、权限不足 → 用户补材料或授权 `ship-shape`
- 用户授权生成线框时：
  - 覆写 `stages.ship-shape.status: pending`
  - 记录 `activation_mode: uiux_material_gate_insert`
  - 写入 `uiux_gate_user_sign_off`、`uiux_gate_signed_at`
  - 设置 `current_stage: ship-shape`
  - 完成后再回到 `ship-define`

### 场景 C（迭代增强）

**入口信号**：
- 用户引用已有 feature 目录、代码路径或明确现有功能
- 描述基于现状的变更需求

**meta.yml 设置**：
- `scenario: evolve`
- `discovery_mode: evolve`
- `current_stage: ship-discover`
- `evolve_source.feature_dirs` 或 `code_paths` 或 `existing_behavior_summary`（至少一种）
- `stages.ship-discover.status: pending`

**初始化行为**：
- 必须有现状基线
- 若用户未指定基线，先询问，不创建目录
- 记录 `evolve_source` 至少包含一种基线类型
- 激活 Discover 大阶段

**与场景 E 的区别**：
- C 从"变更意图 / 旧功能基线"出发，先做产品层影响扫描
- E 从"已有技术方案 selected scope"出发，直接进入技术发现

### 场景 D（PRD 直通）

**入口信号**：
- 用户附了完整 PRD + 原型/设计稿
- 或选择先创建目录粘贴完整 PRD
- 明确表示不需要需求录入（如"PRD 已完整"/"跳过需求录入"/"不需要生成需求文档"/"直接用 PRD"/"PRD 直通"）

**meta.yml 设置**：
- `scenario: prd_direct`
- `current_stage: ship-define`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`（默认）
- `stages.ship-define.generation_mode: prd_direct`
- `stages.ship-define.status: blocked`，`block_reason: awaiting_materials`（若先创建目录）

**初始化行为**：
- 创建 raw `requirements.md` inbox
- 创建 `resource/README.md`
- `ship-define` 走 prd_direct 模式（零提问纯提取）
- 若先创建目录，保持 blocked 态等待用户补材料

**UIUX Material Gate**：
- 同场景 B

**D + backend_only 材料类型确认**：
- 若 `project_scope = backend_only`
- PRD 应包含契约级材料：OpenAPI / endpoint list / 接口文档 / API spec / message protocol / 消息协议 / CLI spec / SDK / request-response 等
- 若只有产品文档无技术规约，`ship-define-review` Phase 1 P1-6 判定 Critical
- 默认建议降级为 B（interview 模式）补足契约信息

### 场景 E（技术方案选区入口）

**入口信号**：
- 用户提供已有技术方案文件或粘贴片段
- 指定章节、接口、模块或标题（selected scope）
- 明确这是已有项目迭代

**meta.yml 设置**：
- `scenario: technical_plan_provided`
- `project_context: existing_project`（强制）
- `current_stage: ship-tech-discovery`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`
- `stages.ship-define.status: skipped`
- `stages.ship-define-review.status: skipped`
- `stages.ship-define.generation_mode: technical_plan`（用于派生 requirements index 兼容标识）
- `technical_plan_source.selected_scope` 非空
- `technical_plan_source.selection_mode: referenced_sections | pasted_excerpt`
- `technical_plan_source.ignored_source_policy: out_of_scope`
- `technical_plan_source.repository_scan_required: true`

**初始化行为**：
- 只创建 `resource/README.md`
- 不创建 raw `requirements.md` inbox
- `requirements.md` 由 `ship-tech-discovery` 开头派生为最小 requirements index
- `selection_mode=pasted_excerpt` 时归档为 `resource/technical-plan-excerpt.md`

**约束条件**：
- 只允许 `project_context: existing_project`
- 若用户说是新项目，必须阻塞并建议改走场景 A/B/D
- 必须写入 `technical_plan_source`，包含技术方案来源、selected scope

**场景 E 不等于直接实现**：
- 场景 E 只跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate
- 仍必须按顺序执行：`ship-tech-discovery → ship-contract → ship-backend-design / ship-frontend-design（按 scope 裁剪） → ship-design-review → ship-delivery-plan → ship-plan-review → ship-build`
- `backend_only` 跳过 `ship-shape` 与 `ship-frontend-design`，但不跳过 `ship-contract`、`ship-backend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`
- selected scope 确认、接口列表确认、响应结构确认都不是 `ship-build` 授权

## 场景 B 与 D 的区分

| 维度 | 场景 B | 场景 D |
|------|--------|--------|
| PRD 完整度 | 部分或完整 | 完整 |
| 用户态度 | 允许继续澄清缺口 | 明确表示不需要需求录入 |
| `generation_mode` | `interview`（多轮采访） | `prd_direct`（零提问纯提取） |
| 明确信号 | 无明确跳过需求录入的信号 | "PRD 已完整"/"跳过需求录入"/"不需要生成需求文档"/"直接用 PRD"/"PRD 直通" |

**判定原则**：
- 若用户提供了材料但未明确表态，默认走场景 B
- 可在启动确认时询问用户偏好

## 信号歧义处理

### 优先级规则

信号歧义时**必须显式询问用户**场景，不允许猜测。

### 场景 A/C 的区分

- 场景 A/C 的 `ship-discover` 通过 `meta.yml.scenario` 和产物 frontmatter `discovery_mode` 区分
- A：`discovery_mode: greenfield`
- C：`discovery_mode: evolve`

### 场景 C 与 E 的区分

- C 从"变更意图 / 旧功能基线"出发，先做产品层影响扫描
- E 从"已有技术方案 selected scope"出发，直接进入技术发现，但仍需仓库取证

## 场景 × 范围组合矩阵

| 组合 | 是否允许 | 处理规则 |
|------|---------|---------|
| A + `backend_only` | 允许 | `ship-discover` 走 backend 子分支（聚焦消费者画像/SLA/契约形态），`ship-shape` 自动跳过 |
| A + `frontend_only` | 允许 | `ship-discover` 走 frontend 子分支，`ship-shape` 正常激活 |
| B + `backend_only` | 允许 | 标准路径，跳过 `ship-shape` 与 `ship-frontend-design`；UIUX Material Gate 不得插入 `ship-shape` |
| B + `frontend_only` | 允许 | 标准路径，跳过 `ship-backend-design` |
| C + `backend_only` | 允许 | `ship-discover` evolve 子分支聚焦 API surface 与消费者 |
| C + `frontend_only` | 允许 | `ship-discover` evolve 子分支聚焦组件/页面影响 |
| D + `backend_only` | 允许（材料类型确认） | D + backend_only 跳过 `ship-shape` 与 `ship-frontend-design`，UIUX Material Gate 不得插入 `ship-shape`；PRD 需要同时具备契约级材料（OpenAPI / endpoint list / 接口文档 / API spec / message protocol / 消息协议 / CLI spec / SDK / request-response 等）。该材料类型会在 `ship-define-review` hard gate 复核；若只有产品 PRD，无接口或技术规约，默认建议降级为 B/interview 补齐契约信息 |
| D + `frontend_only` | 允许 | 标准路径 |
| E + `backend_only` | 允许 | 标准路径，跳过 `ship-shape` 与 `ship-frontend-design` |
| E + `frontend_only` | 允许 | 标准路径，跳过 `ship-backend-design` |

## 启动确认模板

NEW_FEATURE 启动确认必须包含：
- 简述功能名称和目标
- 标明识别到的场景（A/B/C/D/E）及起点阶段
- 标明识别到的范围（fullstack / backend_only / frontend_only）及跳过的阶段
  - `backend_only` 时显式列出："将跳过 `ship-shape` 与 `ship-frontend-design`；不代表 contract / backend design / review / plan 可跳过"
  - `frontend_only` 时显式列出："将跳过 `ship-backend-design`"
- 列出将要经历的大阶段序列（含 Discover 是否激活）
- 预估涉及的技术领域
- 标明下一次需要用户确认的门禁时点
- 若组合为 `D + backend_only`，必须做材料类型确认
- 若场景为 E，必须额外按顺序展示：
  1. 技术方案来源与 selected scope
  2. 未选中内容按 `ignored_source_policy: out_of_scope` 忽略
  3. 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate
  4. 直接进入 `ship-tech-discovery`，并执行 repository scan
  5. `ship-tech-discovery` 开头派生最小 `requirements.md` index
  6. 进入 `ship-contract` 前必须完成 `selected_scope_ac_confirmation`
  7. 完成 contract 和按 scope 裁剪的 frontend/backend design
  8. 进入 `ship-delivery-plan` 前必须通过 `ship-design-review`
- 明确提示：**本次确认只表示启动 ShipKit workflow 并进入 `<current_stage>`，不会开始编码；编码只能在 `ship-plan-review` 通过后进入 `ship-build`**
- 场景 E 的启动确认中也要补充：**即使用户确认 selected scope，也只进入 `ship-tech-discovery`，不会直接实现接口**
- 等待用户一句话确认（"好的""开始""go"等均视为确认）
