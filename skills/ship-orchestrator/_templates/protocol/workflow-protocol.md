# Workflow Protocol

> `skills` 的单一共享协议源。凡是涉及阶段标识、门禁字段、状态机、产物 ownership 的说明，以本文件为准；README、orchestrator、各阶段 SKILL 仅做引用和补充，不再各自发明协议。

## 1. Canonical Stage IDs

唯一合法的阶段标识如下：

| 顺序 | Stage ID | 主要产物 |
|------|----------|---------|
| 01 | `ship-intake` | `requirements.md` |
| 02 | `ship-intake-review` | `review-requirement.md` |
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

禁止在 `current_stage`、`meta.yml.stages.*`、门禁协议、路由规则中混用 `requirement-intake`、`api-contract-design`、`implementation`、`acceptance` 等别名。

## 2. Macro Stage View

对外默认展示四个大阶段；它们是展示层和索引层概念，不替代 Canonical Stage IDs。

| Macro Stage | 展示标签 | 包含的 Canonical Stage IDs |
|-------------|----------|----------------------------|
| `define` | `Define` | `ship-intake`, `ship-intake-review` |
| `design` | `Design` | `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `build` | `Build` | `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `close` | `Close` | `ship-handoff` |

使用规则：

- `current_stage` 仍然只允许写 Canonical Stage IDs。
- `macro_stage` 是 `meta.yml` 中的展示/摘要字段，用于默认用户视图、状态列表和执行摘要。
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
stage: <ship-intake-review | ship-design-review | ship-plan-review>
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
- `macro_stage.current` 只允许使用 `define / design / build / close`
- `macro_stage.label` 只允许使用 `Define / Design / Build / Close`
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
- `spec_context` 记录最近一次规范解析结果与本 feature 已引用规范摘要：
  - `index_status`: `missing | ready | invalid`
  - `last_checked_stage`: 最近一次消费规范的 hook 点
  - `referenced_spec_ids`: 本 feature 已留痕的规范集合
  - `warnings`: 最近一次 helper 解析的告警
  - `pending_proposals`: `ship-handoff` 生成、待用户确认的规范沉淀提案
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
| `ship-intake` | `assistive_only` | 仅资料索引、资源可访问性检查可委派；`requirements.md` 定稿仍由主上下文完成 |
| `ship-intake-review` | `gate_check_switchable` + `user_gate_only` | 质量检查可由当前上下文或子代理执行；最终 gate 结论和签字不可委派 |
| `ship-tech-discovery.research` | `assistive_only` | 可委派资料搜集与证据初筛 |
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
  - `ship-intake-review` -> `review-requirement.md`
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
| `ship-intake` | `assistive_only` | 需求资料索引与可访问性检查 |
| `ship-intake-review` | `gate_check_switchable` | 需求评审 gate |
| `ship-tech-discovery.research` | `assistive_only` | 技术资料搜集与证据初筛 |
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

- `ship-intake-review`
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

- `.docs/spec/INDEX.md` 是 registry，服务于人工浏览；运行时匹配事实源是各个 `.docs/spec/*.md` 的 frontmatter
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

- `ship-tech-discovery`：按 `stage_hooks + stack_tags` 匹配，`domains` 为空表示全局规范
- `ship-frontend-design / ship-backend-design`：按 `stage_hooks + stack_tags + domains` 匹配
- `ship-build`：按 `stage_hooks=ship-build` 且 `applies_to` 对任务文件清单做 glob 匹配；`stack_tags / domains` 为附加过滤
- `ship-handoff`：以 `meta.yml.spec_context.referenced_spec_ids` 为基础生成 proposal，可附加全局规范扫描结果

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

fast-track 是受控子流程，不是“跳过流程直接编码”。

- 最小路径固定为：`ship-intake → ship-intake-review → ship-build → ship-verify → ship-handoff`
- 不允许绕过 `ship-intake-review`
- 若未生成设计/计划文档，必须在启动确认或需求评审中明确记录 fast-track 原因和风险
- 一旦发现需求复杂度上升、接口新增、跨端耦合升高，可随时升级回 standard
