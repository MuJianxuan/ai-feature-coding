# `ship-grill-me` 辅助质询接入计划

> 交付类型：修改计划文档，不直接修改 `skills/` 源文件  
> 目标 skill：`skills/ship-grill-me/`  
> 目标定位：辅助质询 skill，用于阶段 ready / sign-off 前的高压澄清与压力测试  
> 范围边界：仅规划 `ship-delivery-plan` 之前的 6 个接入点，不新增 canonical stage

## 1. 背景与判断

`ship-grill-me` 当前语义是：

- 对 plan / design 进行 relentless interview
- 沿 decision tree 逐层追问
- 每个问题给出 recommended answer
- 若问题可从代码库回答，应先探索代码库
- 一次只问一个问题

这决定它不适合成为新的 workflow stage。它更适合作为阶段内的 `pre-ready` / `pre-signoff` hook：在产物即将标记 ready、或用户即将批准 gate 前，集中暴露模糊点、错误假设、未确认分支和风险承诺。

现有协议中 canonical stage 固定为：

```text
[ship-discover -> ship-shape ->]
ship-define -> ship-define-review
-> ship-tech-discovery
-> ship-contract -> ship-frontend-design -> ship-backend-design
-> ship-design-review
-> ship-delivery-plan
```

因此本计划不改变 stage map，不新增 `meta.yml.current_stage` 值，只新增一类辅助质询节点或 hook 说明。

## 2. 成功标准

完成实施后，应满足：

1. `ship-grill-me` 被明确定位为辅助质询 skill，而不是 canonical stage。
2. 6 个接入点都有清晰触发时机、输入材料、输出形式和禁止行为。
3. hard gate 的最终结论仍由主上下文和用户确认，`ship-grill-me` 不替代 `review-*.md`。
4. `ship-contract`、`ship-delivery-plan` 等 forbidden 节点不被误解为可以启动 grill 子代理。
5. `workflow-protocol.md`、`ship-orchestrator/SKILL.md`、相关阶段 `SKILL.md` 对辅助质询的描述一致。
6. validator / docs check 至少能防止以下错误：
   - 把 `ship-grill-me` 写入 canonical stage list。
   - 在 forbidden 节点登记 grill hook。
   - 在 hard gate 中由 grill 结果直接写 `approved`。
7. regression prompts 覆盖 6 个接入点的典型使用场景。

## 3. 设计原则

### 3.1 不新增 stage

`ship-grill-me` 不写入：

- `current_stage`
- `meta.yml.stages`
- canonical stage order
- stage transition chain
- macro stage mapping

它只作为阶段内策略被引用。

### 3.2 不拥有正式产物

`ship-grill-me` 不直接拥有以下正式文档：

- `product-brief.md`
- `design-brief.md`
- `requirements.md`
- `tech-research.md`
- `tech-selection.md`
- `api-contract.md`
- `frontend-design.md`
- `backend-design.md`
- `review-define.md`
- `review-design.md`

它的输出应是质询记录、待确认问题、recommended answers、risk acceptance 候选项，由当前阶段主上下文合并进正式产物。

### 3.3 一次只处理一个决策分支

`ship-grill-me` 的正文要求 “Ask the questions one at a time”。接入计划必须尊重这一点：

- 自动模式只能生成下一问和 recommended answer。
- 不一次性轰炸用户十几个问题。
- 可先列出质询主题树，但真正交互时逐题推进。

### 3.4 能从仓库确认的问题不问用户

每个接入点都必须保留规则：

- 项目事实、代码路径、已有 API、现有页面、DB 表、权限、测试命令等，先由 agent 探索仓库。
- 只有业务取舍、风险接受、scope 裁剪、未能从证据确认的事实才问用户。

## 4. 接入点总览

| 顺序 | 接入点 | 推荐强度 | 触发时机 | 输出形态 |
|---|---|---|---|---|
| 1 | `ship-discover` 后半段 | 中 | 方案选择后、`product-brief.md` ready 前 | 产品方向质询记录 / open questions |
| 2 | `ship-shape` 方向选择前 | 强 | 3+ wireframe / design variants 产出后、用户选定前 | UIUX 决策质询记录 |
| 3 | `ship-define` ready 前 | 最强 | `requirements.md.stage_status` 从 draft 变 ready 前 | requirements blocking gaps / confirmed assumptions |
| 4 | `ship-tech-discovery` 两个对齐点 | 强 | Selected Scope AC Confirmation / Research Alignment Check | scope / project reality 质询记录 |
| 5 | `ship-frontend-design` / `ship-backend-design` ready 前 | 强 | 对应 design 文档 ready 前 | 设计假设与风险质询记录 |
| 6 | `ship-design-review` 用户签字前 | 强 | `review-design.md` 起草后、用户 approved 前 | sign-off questions / risk acceptance candidates |

## 5. 具体修改计划

### Phase 0：补强 `ship-grill-me` 自身定义

#### 涉及文件

- `skills/ship-grill-me/SKILL.md`

#### 修改内容

1. 将 frontmatter name 统一为目录名或明确 alias。
   - 当前目录是 `ship-grill-me`
   - 当前 frontmatter 是 `name: grill-me`
   - 建议改为 `name: ship-grill-me`
   - 若希望保留触发词，在 description 里写 `grill me`、`grill-me`、`辅助质询`。
2. 扩展 description，让它更容易在 workflow 中触发：
   - “Use as an assistive questioning skill before a ShipKit stage is marked ready or before a hard gate sign-off.”
   - 明确不是 canonical stage。
3. 增加 `Workflow Boundaries` 章节：
   - 不修改 `meta.yml`
   - 不改 artifact frontmatter
   - 不替用户 sign off
   - 不绕过 validator / review gate
   - forbidden stage 中不可作为 subagent 启动
4. 增加 `Output Contract`：
   ```markdown
   ## Grill Output
   - Decision branch:
   - Question:
   - Recommended answer:
   - Evidence checked:
   - User answer:
   - Impact on current artifact:
   - Blocking status: blocking | non_blocking | resolved
   ```
5. 增加 `Question Discipline`：
   - 一次只问一个问题。
   - 先说明为什么这个问题阻塞或影响质量。
   - 给出 recommended answer。
   - 如果用户采纳 recommended answer，记录为明确决策。

#### 验收标准

- skill 名称与目录一致，触发语义清晰。
- 任意阶段引用它时，都不会误以为它能推进状态或写 gate 结论。

### Phase 1：在共享协议中增加辅助质询模型

#### 涉及文件

- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`

#### 修改内容

1. 在 `Delegation Contract` 后新增 `Assistive Questioning Hook` 小节。
2. 定义 `ship-grill-me` 是 hook，不是 stage：
   - 不进入 canonical stage table。
   - 不进入 macro stage table。
   - 不进入 transition order。
3. 定义 hook 类型：
   - `pre_ready_grill`：非 gate 阶段 ready 前质询。
   - `pre_signoff_grill`：hard gate 用户签字前质询。
4. 定义允许节点：
   - `ship-discover.pre-ready`
   - `ship-shape.pre-selection`
   - `ship-define.pre-ready`
   - `ship-tech-discovery.selected-scope-ac-confirmation`
   - `ship-tech-discovery.research-alignment`
   - `ship-frontend-design.pre-ready`
   - `ship-backend-design.pre-ready`
   - `ship-design-review.pre-signoff`
5. 定义禁止节点：
   - `ship-contract`
   - `ship-tech-discovery.selection`
   - `ship-delivery-plan`
   - 任何正式状态推进动作
6. 定义 hard gate 约束：
   - grill 输出只能作为 `review-*.md` 正文里的 open questions / risk acceptance 候选。
   - 不得写 `review_status: approved`。
   - `user_sign_off` 和 `signed_at` 必须由主上下文在用户明确批准后写入。

#### 验收标准

- 协议中能清楚解释 grill 与 delegation 的关系。
- 后续阶段 SKILL.md 引用该协议即可，不各自发明边界。

### Phase 2：更新 orchestrator 路由说明

#### 涉及文件

- `skills/ship-orchestrator/SKILL.md`
- 可选：`skills/README.md`

#### 修改内容

1. 在 `Delegation Model` 后增加 `Assistive Questioning` 说明：
   - orchestrator 在进入允许节点时，可根据用户请求或阶段风险提示使用 `ship-grill-me`。
   - 它不是 delegation mode 的新取值。
   - 不写入 `node_overrides`，除非后续决定显式配置。
2. 在 “阶段 skill 完成后回调调度器” 相关规则中补充：
   - 若当前阶段存在未解决的 blocking grill question，不得推进下一阶段。
   - 若只剩 non-blocking question，可作为 open question 传递，但必须写清影响范围。
3. 在节点级行为或摘要中列出 6 个推荐接入点。
4. 在 `skills/README.md` 的“子代理委派是执行策略，不是新阶段”附近补一句：
   - `ship-grill-me` 是辅助质询，不改变 5 阶段视图和 14 个 canonical stages。

#### 验收标准

- 默认用户仍只看到 5 个 macro stages。
- 高级用户能理解“grill 是阶段内质询，不是新流程节点”。

### Phase 3：接入点 1：`ship-discover` 后半段

#### 涉及文件

- `skills/ship-discover/SKILL.md`

#### 触发时机

在以下动作之后：

- greenfield：方案探索完成，用户倾向某一方案。
- evolve：现状摘要和影响分析完成。

在以下动作之前：

- 标记 `product-brief.md.stage_status: ready`。

说明：grill 应基于已经形成的产品方向或 `product-brief.md` 草稿发问，不应在尚无草稿材料时替代 `ship-discover` 的正常探索过程。

#### 质询重点

1. 目标用户是否具体到可设计路径。
2. 成功标准是否可观测。
3. MVP 是否有明确不做项。
4. 方案选择是否存在未比较的关键替代方案。
5. evolve 场景中，旧功能影响范围是否被低估。

#### 文档修改

1. 在 `Process` 的 `规格自检 (Self-Review)` 前插入可选步骤：
   ```text
   7.5 Optional Grill Check
   ```
2. 增加规则：
   - 仅当需求仍有明显业务分支、方案取舍或 evolve 影响不确定时触发。
   - 不问可从仓库或已有 feature 文档确认的问题。
3. 在 `product-brief.md` 模板或章节说明里增加：
   ```markdown
   ## Grill Decisions
   - GD-001: ...
   ```
   或复用 `Open Questions`，标注 `source: ship-grill-me`。

#### 验收标准

- `ship-discover` 不变成冗长采访。
- 只在方案选择和 ready 前补关键质询。

### Phase 4：接入点 2：`ship-shape` 方向选择前

#### 涉及文件

- `skills/ship-shape/SKILL.md`

#### 触发时机

在 3+ HTML wireframe / design variants 产出并浏览器验证后，用户选定方向前。

#### 质询重点

1. 选中的视觉方向是否匹配目标用户和业务语境。
2. 主流程、异常态、空态、loading、权限态是否在 wireframe 中可见。
3. 移动端和桌面端是否都成立。
4. UI token 是否能被后续 frontend design 消费。
5. 用户选择是否只是“看起来喜欢”，但没有解释业务原因。

#### 文档修改

1. 在 `Step 2: Design Direction Advisor` 后或 `用户选定方向` 前增加 `Design Direction Grill`。
2. 增加输出记录：
   ```markdown
   ## Direction Grill Notes
   - Selected variant:
   - Rejected variants:
   - Key tradeoff accepted:
   - UX states confirmed:
   - Remaining non-blocking concerns:
   ```
3. 在 ready 条件中增加：
   - 若存在 blocking UX state gap，不得 ready。
   - 若用户明确接受风险，可记录为 non-blocking，但不能掩盖缺失的 browser verification。

#### 验收标准

- design direction 的选择理由进入 `design-brief.md`。
- 后续 `ship-define` 可读取这些选择理由，而不是只看到最终视觉稿。

### Phase 5：接入点 3：`ship-define` ready 前

#### 涉及文件

- `skills/ship-define/SKILL.md`

#### 触发时机

在 `requirements.md` 已基本成稿，但 `stage_status` 仍为 draft；准备置为 ready 前。

#### 质询重点

1. In Scope / Out of Scope 是否真正排除了未来功能。
2. 每条 AC 是否可测试，而不是愿望描述。
3. NFR 是否量化。
4. 权限、角色、租户、数据可见性是否明确。
5. 异常流程是否覆盖。
6. Domain ID 是否能承接后续 contract / design。
7. 用户是否接受所有 assumptions。

#### 文档修改

1. 在 `Requirements Self-Review` 前增加 `Pre-Ready Grill`。
2. 在停止澄清条件中增加：
   - blocking grill questions 必须 resolved。
   - non-blocking grill questions 必须进入 `Open Questions` 并标注影响范围。
3. 在 `requirements.md` 结构中增加可选章节：
   ```markdown
   ## Grill Confirmation Log
   | ID | Question | Recommended Answer | User Decision | Impact | Status |
   |---|---|---|---|---|---|
   ```
4. 对 `prd_direct` 模式要谨慎：
   - 不把 grill 变成需求录入。
   - 只追问 PRD 源材料中无法判断、但影响 AC 或 scope 的点。

#### 验收标准

- `requirements.md.stage_status: ready` 前，核心业务不确定性已关闭或降级。
- `ship-define-review` 发现的 Critical/Major 问题应减少。

### Phase 6：接入点 4：`ship-tech-discovery` 两个对齐点

#### 涉及文件

- `skills/ship-tech-discovery/SKILL.md`

#### 触发点 A：Selected Scope AC Confirmation

适用于 `meta.yml.scenario: technical_plan_provided`。

##### 质询重点

1. selected scope 是否只覆盖用户指定章节 / 接口 / 模块。
2. 未选中内容是否明确 `out_of_scope`。
3. 派生 AC 是否足以支撑后续 contract / design / delivery plan。
4. NFR 是否来自 selected scope，还是 agent 自行扩张。
5. 用户是否明确确认 selected scope AC。

##### 修改内容

在 `Selected Scope AC Confirmation` 中增加：

- 可触发 `ship-grill-me` 逐题确认 selected scope。
- 用户确认后写回现有字段：
  - `requirements.md.selected_scope_ac_confirmed=true`
  - `meta.technical_plan_source.selected_scope_ac_confirmation.status=confirmed`

#### 触发点 B：Research Alignment Check

适用于所有场景，尤其 existing project。

##### 质询重点

1. reuse / extend / replace / new / avoid 判断是否与用户预期一致。
2. `unknown` 是否应阻塞，还是按假设继续。
3. 现有 API / DB / page / service 是否有遗漏。
4. 技术调研是否被项目现实约束推翻。
5. 进入 selection 前，关键事实是否都有证据。

##### 修改内容

在 `Research Alignment Check` 后增加 grill 使用规则：

- 若存在 `unknown` 且影响 contract 或 design，必须 grill。
- 若只有 low-risk unknown，可记录为 non-blocking assumption。
- grill 结果并入 `tech-research.md` 的 `Evidence and Uncertainty` 或 `Research Alignment Check`。

#### 验收标准

- 场景 E 不会把未选中技术方案内容带入下游。
- selection 的 ADR 能回指被 grill 确认过的事实或假设。

### Phase 7：接入点 5：`ship-frontend-design` / `ship-backend-design` ready 前

#### 涉及文件

- `skills/ship-frontend-design/SKILL.md`
- `skills/ship-backend-design/SKILL.md`

#### 重要边界

这两个阶段是 `parallel_owned_outputs`。协议中 `assistive_subagent` 在这两个阶段无效。因此接入方式不是启动额外辅助子代理，而是：

- 当前拥有该设计产物的上下文执行 grill。
- 若本阶段本身由 `parallel_subagent` 产出，该子代理可以在自己的设计产物 ready 前执行内部 grill。
- 不允许另一个 grill 子代理同时修改同一正式设计文档。

#### 前端质询重点

1. 每个页面动作是否映射到 contract。
2. UI state matrix 是否覆盖 loading / empty / error / permission / optimistic update。
3. 组件拆分是否服务真实复用，而非过度抽象。
4. API client / cache / store owner 是否明确。
5. 无设计稿或 generated wireframe 的风险是否被承认。

#### 后端质询重点

1. Service boundary 是否和 Domain ID 对齐。
2. 数据模型是否支撑 contract 字段。
3. 事务、一致性、幂等、重试、补偿是否明确。
4. 权限、审计、日志、metrics 是否落到具体实现点。
5. migration / rollback / deployment risk 是否明确。

#### 文档修改

1. 在各自 `Process` 的 self-check / ready 前增加 `Pre-Ready Design Grill`。
2. 增加输出章节：
   ```markdown
   ## Design Grill Notes
   | ID | Risk / Question | Evidence | Decision | Follow-up |
   |---|---|---|---|---|
   ```
3. ready 条件增加：
   - blocking design grill question 未解决时保持 draft。
   - non-blocking question 必须进入 Open Questions 或 Risk section。

#### 验收标准

- `ship-design-review` 可以读取 design grill 结果作为上下文。
- grill 不破坏 frontend/backend 并行 ownership。

### Phase 8：接入点 6：`ship-design-review` 用户签字前

#### 涉及文件

- `skills/ship-design-review/SKILL.md`

#### 触发时机

`review-design.md` 草案完成后，用户批准前。

#### 质询重点

1. Critical / Major 是否真的全部关闭。
2. 剩余 Minor 是否可接受。
3. 用户是否接受上线、性能、安全、兼容性风险。
4. 是否有条件批准，需要写入 `conditions`。
5. 是否应回退到 contract / frontend design / backend design 修复。

#### 文档修改

1. 在 `Process` 的 “提交用户审批” 前增加 `Pre-Signoff Grill`。
2. 明确：
   - grill 不替代 review checklist。
   - grill 不直接写 `review_status: approved`。
   - grill 结果只能形成 sign-off questions、risk acceptance candidates、conditions candidates。
3. 在 `review-design.md` 模板或章节说明中增加：
   ```markdown
   ## Pre-Signoff Grill
   - Question:
   - Recommended decision:
   - User decision:
   - Condition added:
   ```
4. 若用户回答暴露 Critical / Major 问题：
   - 不得 approved。
   - 应设置 `revision_needed` 或保持 `pending` 并回退修复。

#### 验收标准

- 用户签字前能看到具体风险和推荐决策。
- gate frontmatter 的最终字段仍由主上下文按用户明确批准写入。

## 6. validator 与测试计划

### Phase 9：文档一致性校验

#### 涉及文件

- `skills/ship-orchestrator/scripts/validate_workflow_docs.py`

#### 修改内容

1. 增加校验：canonical stage list 不包含 `ship-grill-me` / `grill-me`。
2. 增加校验：`workflow-protocol.md` 包含 `Assistive Questioning Hook` 章节。
3. 增加校验：允许接入点必须包含 6 类阶段说明。
4. 增加校验：`ship-contract`、`ship-delivery-plan` 不得被列为 grill allowed hook。
5. 增加校验：`ship-design-review` 文档中必须说明 grill 不得写 `review_status: approved`。

#### 验收标准

运行：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

应通过，并能在错误修改时给出明确失败信息。

### Phase 10：feature artifact 校验

#### 涉及文件

- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- 可选：新增 `validate_grill_hooks.py`

#### 修改内容

1. 暂不强制所有 feature 必须有 grill 记录。
2. 若检测到 `Grill Confirmation Log` / `Design Grill Notes`：
   - 不允许出现 `approved_by_grill` 等暗示替代用户签字的字段。
   - blocking 状态未 resolved 时，对应 artifact 不得 `stage_status: ready`。
3. 若 `review-design.md` 中出现 Pre-Signoff Grill：
   - 不允许用 Pre-Signoff Grill 替代 `user_sign_off` / `signed_at`。
   - 当 `review_status: approved` 时，仍必须存在 `user_sign_off` / `signed_at`；当 `review_status: pending` 时，这两个字段可以保持为空。

#### 验收标准

- grill 是增强质量的可选 hook，不会让旧 feature 全部失效。
- 一旦使用 grill，blocking 问题必须被正确处理。

### Phase 11：回归测试

#### 涉及文件

- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

#### 新增测试建议

1. `ship-grill-me` 不在 canonical stage order。
2. `ship-contract` 配置 grill hook 时 docs validator 报错。
3. `ship-design-review` 的 grill 输出不允许自动 approved。
4. `requirements.md` 有 unresolved blocking grill question 时，不允许 ready。
5. `frontend-design.md` / `backend-design.md` 有 unresolved blocking grill question 时，不允许 ready。
6. 场景 E selected scope grill 后，只能引用 selected scope 的 AC。

#### 新增 regression prompts

1. “启动 ship-orchestrator，我只有一句话想法，帮我在 product brief ready 前 grill 一下方案选择。”
2. “已有 3 个 UI 线框方案，使用 ship-grill-me 帮我选方向，但不要进入 define。”
3. “requirements.md 已成稿，ready 前用 ship-grill-me 逐题确认 scope 和 AC。”
4. “技术方案选区已提供，进入 contract 前用 ship-grill-me 确认 selected scope AC。”
5. “frontend-design.md / backend-design.md ready 前分别做设计质询，不能互改产物。”
6. “review-design.md 已起草，签字前 grill 风险，但不要自动 approved。”

## 7. 实施顺序

推荐顺序：

1. 修改 `skills/ship-grill-me/SKILL.md`，先把 skill 自身边界写清楚。
2. 修改 `workflow-protocol.md`，建立单一协议源。
3. 修改 `ship-orchestrator/SKILL.md` 和 `skills/README.md`，让默认入口能解释该 hook。
4. 逐个修改 6 个阶段文档：
   - `ship-discover`
   - `ship-shape`
   - `ship-define`
   - `ship-tech-discovery`
   - `ship-frontend-design` / `ship-backend-design`
   - `ship-design-review`
5. 补 `validate_workflow_docs.py`。
6. 补 artifact validator 的轻量规则。
7. 补单元测试和 regression prompts。
8. 运行全量维护命令。

## 8. 验证命令

实施完成后至少运行：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
```

若补了 feature artifact 规则，再用 fixture 或示例 feature 运行：

```bash
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-delivery-plan --json
```

## 9. 风险与取舍

### 风险 1：流程变重

`ship-grill-me` 如果每阶段都默认触发，会让工作流变成过度采访。

缓解：

- 只作为 `pre-ready` / `pre-signoff` hook。
- 默认在高风险或用户主动要求时触发。
- 每次只问一个问题。

### 风险 2：与 hard gate 重复

`ship-define-review` 和 `ship-design-review` 已有 checklist，grill 可能重复评审。

缓解：

- 在 hard gate 中只做签字前风险质询。
- 不重复 checklist。
- 不写最终 review status。

### 风险 3：破坏 forbidden 节点

`ship-contract` 与 `ship-delivery-plan` 是 forbidden 节点，错误接入会破坏单一事实源。

缓解：

- 协议明确禁止。
- docs validator 检查 forbidden 节点不得列入 allowed grill hooks。

### 风险 4：并行设计产物 ownership 混乱

前后端设计可以并行拥有正式产物，如果另开 grill 子代理，可能出现多方编辑同一文档。

缓解：

- grill 在当前产物 owner 内部执行。
- 不作为额外 assistive subagent。
- 不直接修改对方产物。

## 10. 最终推荐

建议把 `ship-grill-me` 做成一套显式但轻量的质量增强 hook：

```text
stage draft -> grill unresolved branch -> artifact ready
review draft -> grill risk acceptance -> user sign-off
```

优先落地顺序：

1. `ship-define.pre-ready`
2. `ship-tech-discovery.selected-scope-ac-confirmation`
3. `ship-tech-discovery.research-alignment`
4. `ship-shape.pre-selection`
5. `ship-frontend-design.pre-ready` / `ship-backend-design.pre-ready`
6. `ship-design-review.pre-signoff`
7. `ship-discover.pre-ready`

这样能最大化减少下游返工，同时不改变现有 workflow 的阶段结构和门禁事实源。
