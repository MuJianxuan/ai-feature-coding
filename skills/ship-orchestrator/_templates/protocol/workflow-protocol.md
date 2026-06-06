# Workflow Protocol

> `skills` 的单一共享协议源。凡是涉及阶段标识、门禁字段、状态机、产物 ownership 的说明，以本文件为准；README、orchestrator、各阶段 SKILL 仅做引用和补充，不再各自发明协议。

## 1. Canonical Stage IDs

唯一合法的阶段标识如下：

| 顺序 | Stage ID | 主要产物 |
|------|----------|---------|
| 00a | `ship-discover` | `product-brief.md` |
| 00b | `ship-shape` | `design-brief.md` + `resource/wireframes/` |
| 01 | `ship-define` | `requirements.md` |
| 02 | `ship-define-review` | `review-define.md` |
| 03 | `ship-tech-discovery` | `tech-research.md` + `tech-selection.md` |
| 04 | `ship-contract` | `api-contract.md` |
| 05 | `ship-frontend-design` | `frontend-design.md` |
| 06 | `ship-backend-design` | `backend-design.md` |
| 07 | `ship-design-review` | `review-design.md` |
| 08 | `ship-delivery-plan` | `frontend-plan.md` + `backend-plan.md` |
| 09 | `ship-plan-review` | `review-plan.md` |
| 10 | `ship-build` | 代码 + 任务状态 |
| 11 | `ship-verify` | `verification.md`（测试章节） |
| 12 | `ship-handoff` | `verification.md`（验收结论）+ `handoff.md` |

禁止在 `current_stage`、`meta.yml.stages.*`、门禁协议、路由规则中混用 `requirement-intake`、`api-contract-design`、`implementation`、`acceptance` 等别名。`ship-intake` / `ship-intake-review` 已重命名为 `ship-define` / `ship-define-review`，旧名亦不可再使用。

说明：

- `ship-discover` 和 `ship-shape` 是条件性前置阶段（Discover 大阶段），仅在场景 A（零到一）或场景 C（迭代增强）时激活；场景 B（产品提供完整材料）、场景 D（PRD 直通）和场景 E（技术方案选区，`technical_plan_provided`）直接跳过，对应 `stages.*.status = skipped`。
- 前置阶段不设独立硬门禁；场景 A/B/C/D 的下游 `ship-define-review` 是统一的需求质量门。场景 E 直接进入 `ship-tech-discovery`，由 `ship-tech-discovery` 派生最小 `requirements.md` 索引，不单独执行 `ship-define-review`。

## 2. Macro Stage View

对外默认展示五个大阶段（Discover 可选）；它们是展示层和索引层概念，不替代 Canonical Stage IDs。

| Macro Stage | 展示标签 | 包含的 Canonical Stage IDs |
|-------------|----------|----------------------------|
| `discover` | `Discover` | `ship-discover`, `ship-shape` |
| `define` | `Define` | `ship-define`, `ship-define-review` |
| `design` | `Design` | `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `build` | `Build` | `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `close` | `Close` | `ship-handoff` |

`Discover` 是条件性大阶段，只在场景 A（零到一）或场景 C（迭代增强）时出现；场景 B（产品提供完整 PRD/原型/UIUX）、场景 D（PRD 直通）和场景 E（技术方案选区，`technical_plan_provided`）直接跳过，meta.yml 中相关阶段记为 `skipped`。

使用规则：

- `current_stage` 仍然只允许写 Canonical Stage IDs。
- `macro_stage` 是 `meta.yml` 中的展示/摘要字段，用于默认用户视图、状态列表和执行摘要。
- `macro_stage.current` 只允许使用 `discover / define / design / build / close`
- 对外默认显示 `macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`；只有在恢复断点、排查阻塞、直接调用具体阶段时，才展开到 `current_stage`。
- `ship-spec` 不是 canonical stage；它是由 orchestrator 感知、由各阶段实际消费的 workflow utility。

## 3. Source of Truth

- **阶段文档 frontmatter 是事实源**：阶段是否 `ready` / `draft`、评审是否 `approved`，以对应产物文档 frontmatter 为准。
- **`meta.yml` 是索引层**：服务于 orchestrator 的恢复、列表、汇总、快速路由；允许缓存摘要状态，但不得与文档 frontmatter 形成第二套真相。
- 当 `meta.yml` 与产物 frontmatter 冲突时，**优先信任产物文档**，然后回写修正 `meta.yml`。

## 4. Non-Review Artifact Contract

所有非评审阶段产物的 frontmatter 最小集合：

```yaml
---
stage: <canonical-stage-id>
artifact_role: ""  # 仅双产物阶段必填，如 research / selection / frontend-plan / backend-plan
stage_status: draft  # draft / ready / complete（按阶段适用）
updated_at: ""
evidence_complete: false
---
```

说明：

- `draft`：产物尚未完成，或证据/前置条件不足。
- `ready`：允许进入下一阶段，但不代表所有最终验收已结束。
- `complete`：仅用于最终态产物，如 `verification.md` 在 `ship-handoff` 完成后。
- `artifact_role`：仅在 `ship-tech-discovery` 和 `ship-delivery-plan` 中使用，用于区分双产物角色。

## 5. Review Gate Contract

所有硬门禁评审文档使用同一 frontmatter 协议：

```yaml
---
stage: <ship-define-review | ship-design-review | ship-plan-review>
gate_type: hard
review_status: pending  # pending / approved / rejected / revision_needed
reviewer: ""
reviewed_at: ""
reviewed_documents: []
revision_count: 0
user_sign_off: ""
signed_at: ""
conditions: []
---
```

推进规则：

- 只有 `review_status: approved` 且 `user_sign_off`、`signed_at` 非空时，才允许推进。
- `rejected`：必须回退到上一个产出阶段。
- `revision_needed`：必须修复列出的 Critical / Major 问题后重审。
- `approved` 是 `meta.yml` 可选缓存字段，不是评审文档事实源。

## 6. meta.yml Summary Contract

`meta.yml` 记录 orchestrator 摘要状态时遵循：

- 普通阶段摘要状态：`pending / in_progress / ready / blocked / completed`
- 评审阶段摘要状态：`pending / in_progress / approved / rejected / revision_needed`
- `current_stage` 只允许使用 Canonical Stage IDs
- `macro_stage.current` 只允许使用 `discover / define / design / build / close`
- `macro_stage.label` 只允许使用 `Discover / Define / Design / Build / Close`
- `macro_stage.summary` 面向默认用户视图，描述当前目标而不是暴露细阶段名
- `macro_stage.next_user_decision` 记录下一次需要用户确认的动作或门禁

推荐策略：

- 阶段开始时：`in_progress`
- 阶段产物达到可推进条件时：`ready` 或评审结果状态
- orchestrator 成功完成阶段切换后：上一阶段记为 `completed`，下一阶段写入 `current_stage`
- 每次 `current_stage` 变化时，同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`
- 对双产物阶段记录 `current_part`，用于阶段内恢复：
  - `ship-tech-discovery.current_part`: `research | selection`
  - `ship-delivery-plan.current_part`: `frontend | backend | sync`
- `stages.ship-define.block_reason` 记录需求定义阶段的阻塞原因；`awaiting_materials` 表示 feature 目录已创建，但仍等待用户把 PRD/原型/设计稿等资料写入 raw `requirements.md` inbox 或 `resource/`
- `spec_context` 记录最近一次规范解析结果与本 feature 已引用规范摘要：
  - `workspace_mode`: `single_project | project_group`
  - `workspace_name`: 工作区名称，来自 `.docs/ship/project.yml`
  - `spec_root`: workspace 下的规范目录
  - `feature_root`: workspace 下的 feature 运行时产物目录
  - `resolution_source`: `workspace_config | meta_spec_context | explicit_paths`
  - `index_status`: `missing | ready | invalid`
  - `last_checked_stage`: 最近一次消费规范的 hook 点
  - `referenced_spec_ids`: 本 feature 已留痕的规范集合
  - `warnings`: 最近一次 helper 解析的告警
  - `pending_proposals`: `ship-handoff` 生成、待用户确认的规范沉淀提案
- `skip_log` 记录用户显式强制跳过门禁或默认前置阶段的事实留痕：
  - 每条记录至少包含 `at / from_stage / to_stage / gate_type / reason / user_sign_off`
  - 仅用于审计和回放，不改变 stage status 的语义
  - 若跳过行为影响后续决策，下游阶段必须显式引用该记录作为风险或假设来源
- `lifecycle_status` 是 feature 级状态，不是 stage status：
  - `active`: 正常推进
  - `blocked`: 当前 feature 无法继续推进
  - `completed`: feature 已完成
  - `abandoned`: feature 被明确终止或废弃
- `delegation` 记录本 feature 的子代理偏好：
  - `default_mode`: `current_context | assistive_subagent`
  - `ask_on_parallel_stage`: 显式并行阶段前是否征询用户
  - `ask_on_assistive_node`: 辅助委派节点前是否征询用户
  - `node_overrides`: 节点级覆盖；key 使用 `stage` 或 `stage.substage`
  - `node_overrides` 合法值：`current_context | assistive_subagent | parallel_subagent | gate_check_subagent`
  - `warnings`: 最近一次 delegation 解析产生的告警；不得与 `spec_context.warnings` 混用

## 7. Delegation Contract

子代理不是额外 stage，而是 orchestrator 在阶段内部采用的执行策略。默认原则：**单一事实源不分叉，正式状态推进单线程，辅助工作可并行**。

说明：

- `Delegation Modes` 是节点能力分类，不是 `node_overrides` 的直接取值
- `node_overrides` 记录的是运行时执行选择值
- 节点是否合法解释某个 override 值，由该节点自己的运行时规则决定

### 7.1 Delegation Modes

| Mode | 含义 | 允许行为 | 禁止行为 |
|------|------|---------|---------|
| `forbidden` | 不允许委派 | 无 | 不可启动子代理 |
| `gate_check_switchable` | gate 检查执行者可切换 | 当前上下文或子代理都可执行质量门禁检查 | 子代理不可确认最终 gate 结果 |
| `parallel_owned_outputs` | 允许并行拥有正式产物 | 子代理可直接产出自己拥有的正式文档 | 不可改别人的正式产物、不可推进 gate |
| `assistive_only` | 只允许辅助委派 | 资料搜集、审计、测试分轨、证据整理 | 不可改 canonical artifact frontmatter、不可改 `meta.yml` |
| `user_gate_only` | 用户独占决策点 | 用户确认通过/拒绝/继续/关闭 | 子代理不可替用户签字或拍板 |

### 7.2 Stage Matrix

| Stage / Node | Delegation Mode | 说明 |
|-------------|-----------------|------|
| `ship-discover` | `assistive_only` | 仅现有代码扫描、过往 feature 索引、外部产品事实核查、规格自检可委派；`product-brief.md` 定稿仍由主上下文完成 |
| `ship-shape` | `assistive_only` | 仅素材收集、参考图分析、token 提取、单变体 HTML 草稿可委派；`design-brief.md` 定稿与变体筛选仍由主上下文完成 |
| `ship-define` | `assistive_only` | 仅资料索引、资源可访问性检查可委派；`requirements.md` 定稿仍由主上下文完成 |
| `ship-define-review` | `gate_check_switchable` + `user_gate_only` | 质量检查可由当前上下文或子代理执行；最终 gate 结论和签字不可委派 |
| `ship-tech-discovery.research` | `assistive_only` | 可委派项目现状扫描、资料搜集与证据初筛；正式 `tech-research.md` 仍由主上下文合并 |
| `ship-tech-discovery.selection` | `forbidden` | 选型必须回指 research 证据，保持单一决策链 |
| `ship-contract` | `forbidden` | 共享契约是前后端并行的单一基线，不分叉 |
| `ship-frontend-design` | `parallel_owned_outputs` | 可与后端设计并行，拥有 `frontend-design.md` |
| `ship-backend-design` | `parallel_owned_outputs` | 可与前端设计并行，拥有 `backend-design.md` |
| `ship-design-review` | `gate_check_switchable` + `user_gate_only` | 质量检查可由当前上下文或子代理执行；最终 gate 结论和签字不可委派 |
| `ship-delivery-plan` | `forbidden` | 阶段内固定 `frontend -> backend -> sync` |
| `ship-plan-review` | `gate_check_switchable` + `user_gate_only` | 质量检查可由当前上下文或子代理执行；最终评审结论和签字不可委派 |
| `ship-build` | `assistive_only` + `user_gate_only` | 正式编码任务保持单 `DOING`；只读准备/验证支线可委派 |
| `ship-verify` | `assistive_only` | 后端单测/集成/契约、前端组件/E2E 可分轨并行；`verification.md` 统一归档 |
| `ship-handoff` | `assistive_only` + `user_gate_only` | 证据收集可委派；close/follow-up/proposal 取舍必须用户决定 |

### 7.3 Ownership Rules

- 只有 `parallel_owned_outputs` 允许子代理直接拥有正式产物文件：
  - `ship-frontend-design` -> `frontend-design.md`
  - `ship-backend-design` -> `backend-design.md`
- `gate_check_switchable` 允许子代理直接写正式 gate 文档草案：
  - `ship-define-review` -> `review-define.md`
  - `ship-design-review` -> `review-design.md`
  - `ship-plan-review` -> `review-plan.md`
- 上述 gate 文档在子代理起草时必须保持：
  - `review_status: pending`
  - `user_sign_off: ""`
  - `signed_at: ""`
- `assistive_only` 子代理只能返回证据包、审计结果、测试结果或候选提案，正式文档合并由主上下文完成。
- 任意模式下，只有 orchestrator 或当前主上下文可以：
  - 修改 `meta.yml`
  - 改写正式产物 frontmatter 的 `stage_status / review_status / all_ac_verified`
  - 写入 `user_sign_off`、`signed_at`
  - 推进 `current_stage`

### 7.4 Canonical Delegation Node IDs

所有 `node_overrides` key 都必须来自预定义的 canonical `node_id` 集合；未知 key 一律视为无效 override。

| Node ID | Delegation Mode | 说明 |
|--------|-----------------|------|
| `ship-discover` | `assistive_only` | 需求探索：代码扫描、事实核查、规格自检 |
| `ship-shape` | `assistive_only` | UIUX 原型：素材收集、参考分析、单变体草稿 |
| `ship-define` | `assistive_only` | 需求资料索引与可访问性检查 |
| `ship-define-review` | `gate_check_switchable` | 需求评审 gate |
| `ship-tech-discovery.research` | `assistive_only` | Project Reality Scan、技术资料搜集与证据初筛 |
| `ship-tech-discovery.selection` | `forbidden` | 技术选型与 ADR 收口 |
| `ship-contract` | `forbidden` | 共享 API 契约定稿 |
| `ship-frontend-design` | `parallel_owned_outputs` | 前端设计正式产物 |
| `ship-backend-design` | `parallel_owned_outputs` | 后端设计正式产物 |
| `ship-design-review` | `gate_check_switchable` | 设计评审 gate |
| `ship-delivery-plan` | `forbidden` | 前后端计划同步收口 |
| `ship-plan-review` | `gate_check_switchable` | 计划评审 gate |
| `ship-build.read-next-task` | `assistive_only` | 下一个任务的现状阅读与文件清单整理 |
| `ship-build.spec-scan` | `assistive_only` | spec 匹配与引用建议 |
| `ship-build.env-precheck` | `assistive_only` | 测试/构建/环境预检查 |
| `ship-build.evidence-pack` | `assistive_only` | 已完成 slice 的证据整理 |
| `ship-verify.backend-unit` | `assistive_only` | backend unit 测试轨 |
| `ship-verify.backend-integration` | `assistive_only` | backend integration 测试轨 |
| `ship-verify.backend-contract` | `assistive_only` | backend contract 测试轨 |
| `ship-verify.frontend-component` | `assistive_only` | frontend component 测试轨 |
| `ship-verify.frontend-e2e` | `assistive_only` | frontend E2E 测试轨 |
| `ship-handoff.ac-evidence` | `assistive_only` | AC 证据收集 |
| `ship-handoff.deploy-materials` | `assistive_only` | 部署事项原材料整理 |
| `ship-handoff.spec-proposals` | `assistive_only` | spec proposal 候选梳理 |

### 7.5 Delegation Warning Log

delegation 解析产生的 warning 必须写入 `meta.yml.delegation.warnings`，对象结构固定为：

```yaml
delegation:
  warnings:
    - at: ""
      node_id: ""
      requested_mode: ""
      resolved_mode: ""
      reason: ""
```

约束：

- `delegation.warnings` 只记录委派解析告警，不复用 `spec_context.warnings`
- 当 override 非法、节点不接受某个 mode、或自动解析被强制回退时，必须追加一条 warning
- warning 是审计信息，不改变阶段事实状态

### 7.6 Runtime Delegation Resolution

orchestrator 在进入可委派节点前，必须按如下顺序解析执行方式：

1. 先确定当前 `node_id`
2. 读取 `node_overrides[node_id]`
3. 若 override 缺失，再根据节点类别决定是否询问用户
4. 若跳过询问，再按该节点可接受的默认规则解析
5. 若仍无法解析，回退 `current_context`

节点类别的运行时规则：

- `forbidden`
  - 不可启动任何子代理，包括辅助委派与只读支线
  - 若存在任何 override，记录 warning 并强制回退 `current_context`
- `parallel_owned_outputs`
  - 只接受 `current_context | parallel_subagent`
  - `assistive_subagent` 与 `gate_check_subagent` 一律视为无效
  - 若 `ask_on_parallel_stage = true`，默认先询问用户
  - 若 `ask_on_parallel_stage = false`，只有 `node_overrides[node_id] = parallel_subagent` 时才自动启动子代理；否则回退 `current_context`
  - 禁止从 `default_mode = assistive_subagent` 推断出 `parallel_subagent`
  - 前后端设计按各自 `node_id` 独立决策；允许只启动其中一侧
- `assistive_only`
  - 只接受 `current_context | assistive_subagent`
  - `parallel_subagent` 与 `gate_check_subagent` 一律视为无效
  - 若 `ask_on_assistive_node = true`，默认先询问用户
  - 若 `ask_on_assistive_node = false`，可在 override 缺失时回落到 `default_mode`
- `gate_check_switchable`
  - 只接受 `current_context | gate_check_subagent`
  - `assistive_subagent` 映射为 `gate_check_subagent`
  - `parallel_subagent` 一律视为无效
  - 三个 hard gate 不单独受 `ask_on_assistive_node` 或 `ask_on_parallel_stage` 控制；它们只复用 `node_overrides` 与 `default_mode`

用户在委派决策节点的回答持久化规则：

- 节点级回答写入 `node_overrides[node_id]`
- 不得隐式改写 `default_mode`
- 只有用户明确表达“以后默认都这样”时，orchestrator 才能更新 `default_mode`

### 7.7 Hard Gate Runtime Execution Modes

以下三阶段进入时，orchestrator 必须按 delegation 配置自动解析本次质量门禁检查的执行者：

- `ship-define-review`
- `ship-design-review`
- `ship-plan-review`

可选执行方式：

- `current_context`
  - 主代理直接执行 gate 检查并写正式 `review-*.md`
- `gate_check_subagent`
  - 子代理执行 gate 检查并直接写正式 `review-*.md` 草案
  - 草案写入时 `review_status` 固定为 `pending`
  - 主代理随后必须重新读取该文档、复核内容、确认质量检查结果

解析顺序固定为：

1. 先读取 `node_overrides[stage]`
2. 若 override 缺失或不适用，再读取 `delegation.default_mode`
3. 若仍无法解析，回退 `current_context`

值映射规则：

- `current_context` -> `current_context`
- `gate_check_subagent` -> `gate_check_subagent`
- `assistive_subagent` -> `gate_check_subagent`
- `parallel_subagent` -> 对 hard gate 无效

无效值处理：

- 若 hard gate 上的 `node_overrides` 值无效（如 `parallel_subagent`），记录 warning 后回退到 `default_mode`
- 若 `default_mode` 在 hard gate 上无法解析，也记录 warning，并最终回退 `current_context`

固定收口流程：

1. 基于 delegation 配置解析本次 gate 的执行方式
2. 产出正式 `review-*.md` 草案
3. 主代理复核该草案并按需要修订
4. 主代理设置最终 `review_status`
5. 若主代理判断可通过，再向用户请求明确批准
6. 只有用户明确批准后，主代理才能写入 `user_sign_off` 与 `signed_at`

### 7.8 User Decision Nodes

以下节点允许 orchestrator 询问“当前上下文执行，还是启用子代理策略”：

1. `ship-contract` 完成后、进入 `ship-frontend-design / ship-backend-design` 前
2. `ship-plan-review` 通过后、进入 `ship-build` 前
3. `ship-build` 每个 verified slice 完成后
4. `ship-verify` 入口
5. `ship-handoff` 收尾前（此处只问关闭/跟进决策，不问并行编码）

默认策略：

- 若 `delegation.default_mode = current_context`，则默认不启动子代理
- 若 `delegation.default_mode = assistive_subagent`，则按节点规则解释：
  - 在 `assistive_only` 节点，表示默认启用辅助委派
  - 在三个 hard gate 节点，映射为 `gate_check_subagent`
- `parallel_owned_outputs` 阶段默认仍应询问用户，除非 `ask_on_parallel_stage = false`
- 当 `ask_on_parallel_stage = false` 时，只有显式 `node_overrides[node_id] = parallel_subagent` 才能自动委派；否则回退 `current_context`
- 当 `ask_on_assistive_node = false` 时，`assistive_only` 节点可在 override 缺失时回落到 `default_mode`
- 三个 hard gate 的执行方式复用 `node_overrides` 与 `default_mode`，不再每次进入都单独询问
- `node_overrides` 的值语义固定为：
  - `current_context`: 当前上下文执行
  - `assistive_subagent`: 辅助委派执行
  - `parallel_subagent`: 并行拥有正式产物的子代理执行
  - `gate_check_subagent`: hard gate 检查子代理执行
- 节点级覆盖只影响当前节点，不自动改写全局默认

## 8. Spec Hook Contract

`ship-spec` 是 workflow utility，不参与 stage map，也不拥有 `current_stage`。它通过 hook 的方式接入以下阶段：

### Workspace Resolution Contract

- `ship-spec` 的运行边界是 workspace，默认 spec root 是 workspace `.docs/spec`。
- `.docs/ship/project.yml` 是 workspace boundary 的唯一显式配置源。
- `spec_runtime.py` / `feature_meta_runtime.py sync-spec` 优先读取 `--project-config`；CONTINUE_FEATURE 则优先读取已有 `meta.yml.spec_context`。
- 不允许根据 `package.json`、`go.mod`、`pyproject.toml` 或父目录结构做 silent guess。
- `spec_context` 必须持久化以下字段：
  - `workspace_mode`
  - `workspace_name`
  - `spec_root`
  - `feature_root`
  - `resolution_source`
- feature `projects` 是默认执行范围，不是硬安全边界；用户明确要求探索其他一级项目时允许临时扩展，并在阶段文档中留痕。
- 只有无法确定 `workspace` 时才阻塞；workspace 已确定但缺少 `spec_root` / `INDEX.md` / 匹配 spec 时，统一走 Warn Then Continue。

| Hook 点 | 触发时机 | 默认动作 | 缺失/不匹配策略 |
|---------|---------|---------|----------------|
| `ship-tech-discovery` | `selection` 子段完成前 | 检查规范与选定技术栈/约束是否冲突 | Warn Then Continue |
| `ship-frontend-design` | 编写设计约束前 | 加载前端相关规范作为设计约束 | Warn Then Continue |
| `ship-backend-design` | 编写设计约束前 | 加载后端相关规范作为设计约束 | Warn Then Continue |
| `ship-build` | 每个任务开始前 | 按文件清单匹配规范并写入任务证据 | Warn Then Continue |
| `ship-handoff` | 验收总结前 | 汇总已引用规范并生成待沉淀 proposal | Warn Then Continue |

运行时约束：

- orchestrator 在进入以上阶段前，应通过 `spec_runtime.py` 或等价 helper 解析规范，并回写 `meta.yml.spec_context`
- `ship-tech-discovery / ship-frontend-design / ship-backend-design / ship-handoff` 的相关产物 frontmatter 应包含：

```yaml
spec_checked_at: ""
referenced_spec_ids: []
spec_warnings: []
```

- `ship-build` 没有阶段产物 frontmatter；它应在任务条目或任务证据中记录 `spec_refs`

- workspace 下的 `.docs/spec/INDEX.md` 是唯一人工路由入口；agent 在当前需求和阶段下必须先读 `INDEX.md`，再决定读取哪些 spec 文件
- `INDEX.md` 表格只使用 `frontend / backend / shared` 三类；不新增 `spec_type` / `discipline` 等 schema 层级字段
- 运行时 helper 仍可读取 workspace `spec_root` 下各个规范文件的 frontmatter 做 scan / resolve / 校验；`INDEX.md` 与 frontmatter 不一致时记录 warning
- 缺少 `INDEX.md`、找不到匹配规范、frontmatter 不合法时，默认只告警并留痕；除非用户显式要求严格模式，否则不阻塞阶段推进
- `fast-track` 不新增 hook stage；跳过设计阶段时，规范检查压缩到 `ship-build` 入口和 `ship-handoff` 汇总

规范 frontmatter 统一字段：

```yaml
spec_id: ""
scope: project  # project | module | file
stage_hooks: []  # ship-tech-discovery | ship-frontend-design | ship-backend-design | ship-build | ship-handoff
stack_tags: []
domains: []
applies_to: []
last_updated: ""
```

匹配规则：

- `ship-tech-discovery`：先读 `.docs/spec/INDEX.md`，再按 `stage_hooks + stack_tags` 匹配，`domains` 为空表示全局规范
- `ship-frontend-design`：先读 `INDEX.md` 中 `frontend/shared` 候选，再按 `stage_hooks + stack_tags + domains` 匹配
- `ship-backend-design`：先读 `INDEX.md` 中 `backend/shared` 候选，再按 `stage_hooks + stack_tags + domains` 匹配
- `ship-build`：按 `stage_hooks=ship-build` 且 `applies_to` 对任务文件清单做 glob 匹配；任务文件清单必须先归一化到 workspace root 相对路径；`stack_tags / domains` 为附加过滤
- `ship-handoff`：以 `meta.yml.spec_context.referenced_spec_ids` 为基础生成 proposal，可附加全局规范扫描结果

## 8.1 Tech Discovery Research Contract

`ship-tech-discovery` 是 Design 大阶段的第一个事实收口点。已有项目上的需求必须 Project Reality First，不能只做外部技术调研或技术选型。

`tech-research.md.stage_status: ready` 必须包含：

- `Project Reality Scan / 项目现状发现`
- `Requirement-to-Reality Mapping / 需求与已有系统映射`
- `Existing Surface Inventory / 现有表面清单`
- `Evidence and Uncertainty / 证据与不确定项`
- `Research Alignment Check / 产出前对齐记录`
- `Technical Research / 技术调研`
- `Selection Inputs / 给 tech-selection.md 的输入`

Research Alignment Check 是 research 子段内部的过程动作，不是 hard gate：

- 不新增 `review-tech-research.md`
- 不新增 `review_status / user_sign_off / signed_at`
- 用户纠正项目理解时，必须回到相关代码路径重新探索并更新证据
- 用户允许按假设继续时，必须在 `tech-research.md` 记录 assumptions、风险和影响范围

对 `existing_project`，Project Reality Scan 必须至少给出与需求相关的代码路径、文档路径、API、DB、frontend、service、worker、MQ、权限、observability、test 或既有 feature 证据。对 `new_project`，可以写“不适用：new_project，无既有代码基线”，但章节不能消失。

## 9. Testing / Handoff Ownership

`verification.md` 是跨 13/14 两阶段共享的验收证据文件，ownership 分工如下：

- `ship-verify`：
  - 创建或更新 `verification.md`
  - 负责自动化测试结果、覆盖率、失败分类、环境说明
  - 自动化验证通过后将 `verification.md.stage_status` 置为 `ready`
- `ship-handoff`：
  - 读取 `verification.md`
  - 补齐 AC 映射、手工验证、残余风险、最终验收结论
  - 完成后将 `verification.md.stage_status` 置为 `complete` 或保留 `draft`
  - 产出 `handoff.md`

`ship-build` 只负责任务级验证与 plan 状态，不拥有 `verification.md`。

并行约束补充：

- `ship-verify` 可把 backend unit / backend integration / backend contract / frontend component / frontend E2E 作为独立测试轨道并行执行
- 并行执行不改变 `verification.md` ownership；测试结果必须由主上下文统一写回
- `ship-handoff` 可并行收集 AC 证据、截图、命令输出和 proposal 候选，但残余风险分级与 `stage_status` 判定必须单线程完成

## 10. Fast-Track Rules

fast-track 是受控子流程，不是"跳过流程直接编码"。

- 场景 A/B/C/D 的最小路径固定为：`ship-define → ship-define-review → ship-build → ship-verify → ship-handoff`（场景 A/C 仍保留必要的 `ship-discover` 前置）
- 场景 A/B/C/D 不允许绕过 `ship-define-review`；场景 E 默认不进入 fast-track，直接从 `ship-tech-discovery` 开始并保留后续设计评审
- 若未生成设计/计划文档，必须在启动确认或需求评审中明确记录 fast-track 原因和风险
- 若未生成 `frontend-plan.md` / `backend-plan.md`，`ship-build` 的任务事实源固定为 feature 根目录下的 `fast-track-tasks.md`
- 一旦发现需求复杂度上升、接口新增、跨端耦合升高，可随时升级回 standard

`fast-track-tasks.md` 是 build 阶段轻量任务事实源，不新增 canonical stage。文件由 `ship-define-review` 通过后或进入 `ship-build` 前创建，主上下文维护。

frontmatter:

```yaml
---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---
```

任务条目沿用 `ship-build` 的单任务格式：

```markdown
### Task FT-001: 修复登录按钮状态
- status: DOING
- allowed_files:
  - src/pages/Login.tsx
- ac_refs:
  - AC-AUTH-001
- verification_command: pnpm test -- Login
- evidence:
  - pending

任务目标：
修复登录按钮状态。

上下文：
前端是 React；登录页在 src/pages/Login.tsx；AC-AUTH-001 覆盖按钮状态行为。

约束：
不要重写登录页；不要改后端接口；只修改 allowed_files 中列出的文件。

验收：
pnpm test -- Login 通过；AC-AUTH-001 对应行为可观察。

输出：
直接修改 allowed_files 中列出的代码，更新 evidence，并说明改了哪些文件。
```

最低要求：全局恰好一个 `DOING` task；当前 `DOING` task 必须包含 `allowed_files`、AC refs、verification command，以及 `任务目标 / 上下文 / 约束 / 验收 / 输出` 执行简报。fast-track 若升级回 standard，保留 `fast-track-tasks.md` 作为历史证据，后续任务源切回 plan 文档。

Discover 前置阶段在 fast-track 下的规则：

- 场景 A（零到一）/ 场景 C（迭代增强）即便选择 fast-track，也应至少经过 `ship-discover`，因为"模糊想法"或"变更请求"未结构化时无法直接进 `ship-define`
- fast-track 下默认跳过 `ship-shape`：UIUX 留给 `ship-build` 阶段在简单页面上现场处理；若 fast-track 中发现 UI 复杂度高，应升级回 standard 并补做 `ship-shape`
- 场景 B（产品提供完整材料）和场景 D（PRD 直通）的 fast-track 与现有规则一致，`ship-discover` 与 `ship-shape` 都标记为 `skipped`

## 11. Scenario Routing Rules

`ship-orchestrator` 在 NEW_FEATURE 流程的入口必须先识别场景，再决定起点 stage。

| 场景 | 入口信号 | 起点 stage | Discover 大阶段 |
|------|---------|------------|-----------------|
| A 零到一 | 用户只有一句话想法、无附件 | `ship-discover`（greenfield 分支） | 激活 |
| B 产品提供 | 用户附了 PRD/Figma/原型/UIUX 文档，或选择先创建目录后补资料 | `ship-define`（interview mode） | 跳过（`stages.ship-discover.status / ship-shape.status = skipped`） |
| C 迭代增强 | 用户引用已有 feature 目录或具体代码路径并描述变更 | `ship-discover`（evolve 分支） | 激活 |
| D PRD 直通 | 用户附了完整 PRD + 原型/设计稿，或选择先创建目录粘贴完整 PRD，且明确表示不需要需求录入 | `ship-define`（prd_direct mode） | 跳过（`stages.ship-discover.status / ship-shape.status = skipped`） |
| E 技术方案选区 | 用户提供已有技术方案文件或粘贴片段，并指定章节、接口、模块、标题等 selected scope；必须是 `existing_project` | `ship-tech-discovery`（technical plan entry） | 跳过（`stages.ship-discover.status / ship-shape.status / ship-define.status / ship-define-review.status = skipped`） |

判定规则：

- 信号歧义时必须显式询问用户场景，不允许猜测
- 场景 A/C 的 `ship-discover` 通过 frontmatter `discovery_mode: greenfield | evolve` 区分分支
- 场景 A/C 在 `ship-discover` 完成后，若 feature 涉及 UI 且无外部 UIUX 材料，进入 `ship-shape`；否则跳过 `ship-shape` 直接进 `ship-define`
- 场景 B 不进 Discover 大阶段；若资料已存在，orchestrator 路由到 `ship-define`（interview mode）；若用户选择先创建目录后补资料，则 `stages.ship-define.status: blocked` 且 `block_reason: awaiting_materials`
- 场景 D 不进 Discover 大阶段；若资料已存在，orchestrator 路由到 `ship-define`（prd_direct mode）；若用户选择先创建目录后补资料，则 `stages.ship-define.status: blocked` 且 `block_reason: awaiting_materials`；`stages.ship-define.generation_mode` 设为 `prd_direct`
- 场景 B/D 的 raw `requirements.md` inbox 只是原始资料入口，不是下游 contract；必须经 `ship-define` normalize 后才能进入 `ship-define-review`
- 场景 E 不新增 canonical stage；`meta.yml.scenario = technical_plan_provided`，`current_stage = ship-tech-discovery`，`stages.ship-define.status = skipped`，`stages.ship-define.generation_mode = technical_plan`（即 derived `requirements.md` 使用 `generation_mode: technical_plan`），`stages.ship-define-review.status = skipped`，`technical_plan_source.repository_scan_required = true`
- 场景 E 只允许 `project_context: existing_project`；若用户试图用于 `new_project`，必须阻塞并改走场景 A/B/D
- 场景 E 只创建 `resource/README.md` 作为资料归档提示，不创建 raw PRD inbox；`requirements.md` 由 `ship-tech-discovery` 开头派生为最小 requirements index，用于后续 AC traceability
- 场景 E 不能直接进入 `ship-delivery-plan`；仍必须通过 `ship-tech-discovery`、`ship-contract`、必要的 frontend/backend design 和 `ship-design-review`

场景 B 与 D 的区分：

- 场景 B：用户提供了 PRD/原型等材料，但未明确表示跳过需求录入 → `ship-define` 走 interview 模式（多轮采访，完整生成 requirements.md）
- 场景 D：用户提供了完整 PRD + 原型，且有明确信号表示不需要需求录入（如"PRD 已完整"/"跳过需求录入"/"不需要生成需求文档"/"直接用 PRD"/"PRD 直通"） → `ship-define` 走 prd_direct 模式（零提问，产出索引式 requirements.md，引用 PRD 来源位置而非复制原文）
- 若用户提供了材料但未明确表态，默认走场景 B；可在启动确认时询问用户偏好

场景 E 技术方案选区协议：

- `technical_plan_source` 是索引层，不是正文事实源。原始技术方案文件或粘贴片段必须归档到 `resource/` 或记录为用户明确提供的可读路径。
- `technical_plan_source.selected_scope` 是本期唯一进入计划的范围；未选中内容按 `ignored_source_policy: out_of_scope` 处理，不得自动纳入 `requirements.md`、contract、design 或 delivery plan。
- `selection_mode` 只能是 `referenced_sections` 或 `pasted_excerpt`；粘贴片段必须归档为 `pasted_excerpt_file`。
- `ship-tech-discovery` 开头必须从 selected scope 派生最小 `requirements.md` index：只包含本期 In Scope / Out of Scope、Domain ID、最小 AC、NFR、待确认问题和 source index。若技术方案没有明确 AC，agent 只能提取最小可验收结果草案，并在 Research Alignment Check 中要求用户确认；AC 缺失时不得把 `requirements.md.stage_status` 标记为 `ready`，也不得把 `tech-research.md` 和 `tech-selection.md` 同时标记为 ready。
- `ship-tech-discovery` 必须执行 Project Reality Scan，但扫描范围只围绕 selected scope；`Requirement-to-Reality Mapping` 只覆盖 derived `requirements.md` index 对应的 Domain ID / AC ID。若未选中内容构成前置依赖或冲突，记录为 risk / open question，不自动扩大 scope。
- `repository_scan_status: ready` 只是补充索引，不能替代 `tech-research.md` / `tech-selection.md` 的 frontmatter 与内容校验。
- `ship-contract`、`ship-frontend-design`、`ship-backend-design`、`ship-delivery-plan` 都必须按 selected scope 裁剪；每个 delivery plan task 必须引用 AC ID、selected scope 或 technical source、仓库探索证据、`allowed_files`、verification command，以及 `任务目标 / 上下文 / 约束 / 验收 / 输出` 执行简报。

Discover 阶段产物补充契约：

- `product-brief.md` 在通用 frontmatter 之外增加：`discovery_mode`（必填）、`approach_selected`（greenfield 必填）、`base_feature`（evolve 必填）、`discovery_rounds`、`fact_check_done`
- `design-brief.md` 在通用 frontmatter 之外增加：`design_direction`、`variations_count`、`wireframe_index_path`、`asset_protocol_invoked`、`brand_spec_path`
- `resource/wireframes/` 至少包含 `index.html`（变体导航）+ 至少 3 个变体 HTML 入口；HTML 必须在浏览器中可访问、控制台无报错

## 12. Project Scope Contract

`project_scope` 是 feature 级维度，决定哪些阶段被跳过、哪些阶段需要适配行为。与 `scenario` 平行：scenario 决定入口完整度路由，scope 决定架构层覆盖范围。

### 12.1 Valid Values

| Value | 含义 | 跳过阶段 |
|-------|------|---------|
| `fullstack` | 前后端均涉及（默认） | 无 |
| `backend_only` | 仅后端 | `ship-shape`, `ship-frontend-design` |
| `frontend_only` | 仅前端 | `ship-backend-design` |

`ship-contract` 在所有 scope 下默认保留（后端 API 需要契约给消费者，前端需要契约描述所消费的外部 API）。

### 12.2 Detection Timing

- **首选**：NEW_FEATURE 启动确认时由用户声明（"纯后端项目"/"只做 API"/"不涉及前端"）
- **次选**：`ship-tech-discovery` 完成后由 orchestrator 基于明确证据确认，不允许仅凭 `tech_stack.frontend` 或 `tech_stack.backend` 为空就得出单侧结论
- **证据要求**：必须同时能说明 `tech_stack`、现有 surface、consumer/entrypoint 和项目边界四类证据都指向单侧，才允许写回 `meta.yml.project_scope` 与 `project_scope_evidence`
- **冻结点**：`ship-design-review` 通过后 scope 不可变更
- **歧义处理**：信号不明确时默认 `fullstack`。此时必须显式询问用户是否要落成单侧 scope；在用户确认之前不得写回单侧 `project_scope`，不得静默落盘为单侧 scope

### 12.3 Skip Mechanism

与 Discover 跳过机制一致：

- 被跳过的阶段在 `meta.yml.stages.<stage>.status` 设为 `skipped`
- orchestrator 路由时遇到 `skipped` 状态直接跳到下一个非 skipped 阶段
- 被跳过阶段的产物不生成，下游阶段不得引用不存在的产物
- 向后兼容：缺失 `project_scope` 字段的已有 feature 默认为 `fullstack`

### 12.4 Conditional Stages

| 阶段 | fullstack | backend_only | frontend_only |
|------|-----------|--------------|---------------|
| `ship-contract` | active | active | active |
| `ship-frontend-design` | active | **skipped** | active |
| `ship-backend-design` | active | active | **skipped** |
| `ship-design-review` | 3-doc 交叉验证 | 2-doc（Contract↔Backend） | 2-doc（Contract↔Frontend） |
| `ship-delivery-plan` | frontend→backend→sync | backend only | frontend only |
| `ship-plan-review` | 2-plan 评审 | 1-plan 评审 | 1-plan 评审 |
| `ship-verify` | 全轨道 | 跳过 frontend-* 轨道 | 跳过 backend-* 轨道 |

### 12.5 Downstream Adaptation

受 scope 影响的阶段必须包含 `## Scope Adaptation` 节，定义：

- 入口条件如何变化
- 产物集合如何变化
- 检查项哪些标记为 `na`（不适用）

### 12.6 Verify Track Adaptation

`ship-verify` 测试轨道根据 scope 自动裁剪：

- `backend_only`：跳过 `ship-verify.frontend-component` 和 `ship-verify.frontend-e2e`
- `frontend_only`：跳过 `ship-verify.backend-unit`、`ship-verify.backend-integration`、`ship-verify.backend-contract`
- `fullstack`：所有轨道可用
