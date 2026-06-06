# skills 工作流完整审计报告

审计范围：当前仓库 `skills/`。

审计方式：
- 已按用户要求先探索目录，再尝试按场景入口委派 4 个子代理分别跟踪 A/C、B/D、E、Design/Build/Close 横向链路。
- 子代理运行 `294c7867` 超时且后续 session 不可访问，因此主代理基于 `skills/README.md`、`skills/ship-orchestrator/SKILL.md`、各阶段 `SKILL.md`、`workflow-protocol.md`、`meta.yml.template` 重新复核并汇总。
- 已运行校验命令：`python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py`，结果 `workflow docs validation: OK`。这说明当前显式校验未发现协议文档硬错误，但不代表工作流没有语义冲突。

## 1. 总体结论

这套 skills 已形成较完整的端到端开发工作流：

```text
[Discover →] Define → Design → Build → Close

[ship-discover → ship-shape →]
ship-define → ship-define-review
→ ship-tech-discovery
→ ship-contract → ship-frontend-design / ship-backend-design
→ ship-design-review
→ ship-delivery-plan → ship-plan-review
→ ship-build → ship-verify → ship-handoff
```

整体优点：
- `workflow-protocol.md` 明确声明为共享协议源，避免各阶段各自发明协议。
- 五种入口场景 A/B/C/D/E 已在 README、orchestrator、protocol 中基本一致。
- 三道 hard gate（Define Review / Design Review / Plan Review）规则较清楚。
- 子代理边界有明确约束：子代理不是 stage，不能推进 `current_stage`，不能替用户签字。
- `technical_plan_provided` 场景已经补了 selected scope 裁剪、existing_project 限制和最小 requirements index，方向合理。

主要问题集中在：
1. 场景 E 跳过 Define gate 后，最小 AC 的用户确认机制不够强，容易让“技术方案草案”伪装成已确认需求。
2. `ship-delivery-plan` 的 fullstack 固定顺序与前后端设计并行理念不完全一致，且在单侧 scope 下与“主要产物 = frontend + backend plan”的协议表达有轻微冲突。
3. 场景 B/D 的 UIUX Material Gate 可以临时插入 `ship-shape`，但 `ship-shape` 在共享协议中仍被定义为仅 A/C 激活，存在运行时状态表达冲突。
4. `verification.md` 的 ownership 设计合理但反直觉：`ship-verify` 产物 frontmatter 固定 `stage: ship-handoff`，容易被阶段校验、恢复逻辑或人工理解误判。
5. soft gate 允许用户强制推进 `draft`，但多个阶段又写有“不得进入下游”的硬语气，软/硬阻塞边界需要更明确。
6. 文档里多处强调用户确认，但没有统一的“确认话术/签字字段/记录位置”模板，容易在执行中产生不一致。

## 2. 场景入口逐一跟踪

### 2.1 场景 A：零到一 greenfield

入口信号：只有一句话想法，无 PRD/原型/设计稿。

期望路径：

```text
ship-orchestrator
→ ship-discover(greenfield)
→ 若涉及 UI 且无 UIUX 材料：ship-shape
→ ship-define(interview)
→ ship-define-review
→ ship-tech-discovery
→ ship-contract
→ ship-frontend-design / ship-backend-design
→ ship-design-review
→ ship-delivery-plan
→ ship-plan-review
→ ship-build
→ ship-verify
→ ship-handoff
```

证据：
- `skills/README.md` 五种入口场景中 A 起点是 `ship-discover`，Discover 激活。
- `skills/ship-orchestrator/SKILL.md` 场景 A 起点为 `ship-discover(greenfield)`，若涉及 UI 且无外部 UIUX 材料进入 `ship-shape`。
- `workflow-protocol.md` 说明 `ship-discover` 和 `ship-shape` 仅 A/C 激活。

发现：

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| A-1 | `ship-discover` 完成依赖“用户确认 → stage_status: ready”，但后续统一 hard gate 在 `ship-define-review`，Discover 本身无标准签字字段。 | 用户确认产品方向的证据可能只存在正文或对话里，恢复/审计时不如 review gate 稳定。 | 给 `product-brief.md` 增加统一 `user_direction_sign_off` / `confirmed_at` 字段，或在 protocol 中说明 Discover 确认只需正文记录。 |
| A-2 | `ship-shape` 要求 3+ 变体验证通过，但 `meta.yml.template` 只记录 `variations` 数量和 `direction`，未记录浏览器验证状态。 | orchestrator 只能凭 artifact frontmatter 或正文判断，meta 摘要不足。 | 在 `meta.yml.stages.ship-shape` 增加 `browser_verified: false` 或确保 `design-brief.md` frontmatter 包含 `browser_verified`。 |
| A-3 | 若 A + `backend_only`，orchestrator 说跳过 `ship-shape`；但 Discover 大阶段仍激活。这个逻辑合理，但用户默认五阶段视图可能看到 Discover 阶段少一个子阶段。 | 展示层可能让用户误以为 UI 原型缺失。 | macro summary 明确：“Discover 已完成，UI shaping 因 backend_only 被跳过”。 |

### 2.2 场景 C：迭代增强 evolve

入口信号：引用已有 feature 目录、代码路径或现有功能，并描述变更。

期望路径与 A 基本相同，但 `ship-discover` 走 evolve 分支，需要现状基线。

证据：
- `skills/README.md` C 起点为 `ship-discover(evolve)`。
- `ship-orchestrator/SKILL.md` 规定场景 C 必须有现状基线；若没有指定已有 feature/code 基线，不创建目录，先询问。
- `ship-discover/SKILL.md` evolve 分支会读取已有 feature、requirements、handoff、代码路径等。

发现：

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| C-1 | C 的现状基线既可能是旧 feature 目录，也可能是代码路径或“明确现有功能”，但 `meta.yml.template` 没有专门字段保存 evolve baseline。 | 后续 Design/Build 很难稳定追溯“基于哪个旧实现变更”。 | 增加 `evolve_source`：`feature_dirs`、`code_paths`、`existing_behavior_summary`、`baseline_confirmed_at`。 |
| C-2 | evolve 中 `ship-discover` 会分析影响，但后续 `ship-tech-discovery` 又要求 Project Reality First，二者职责可能重复。 | 重复扫描仓库，耗时；两个阶段可能得出不同现状结论。 | 明确 Discover 只做产品/影响粗分，Tech Discovery 做可执行技术现状扫描；在 `product-brief.md` 中输出“待技术验证项”。 |

### 2.3 场景 B：产品提供 product_provided

入口信号：已有 PRD/Figma/原型/UIUX，但允许继续澄清缺口。

期望路径：

```text
ship-orchestrator
→ ship-define(interview)
→ ship-define-review
→ Design / Build / Close
```

证据：
- README 场景 B 起点为 `ship-define(interview mode)`，跳过 Discover。
- orchestrator 规定 B/D 若尚未放资料，先创建 raw requirements inbox 和 resource README，并将 `ship-define` blocked。
- orchestrator 规定 B/D 若涉及 UI 且缺 UIUX 材料，必须走 UIUX Material Gate。

发现：

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| B-1 | README 说 B 跳过 Discover；orchestrator 又允许 B/D 在 UIUX Material Gate 中插入 `ship-shape` 生成线框。共享协议却说 `ship-shape` 仅 A/C 激活。 | 运行时可能出现 `scenario=product_provided` 但 `ship-shape` 非 skipped，违反“仅 A/C 激活”的读法。 | 把 `ship-shape` 的条件改成：“默认 A/C 激活；B/D 可经 UIUX Material Gate 显式插入”，并在 protocol、README、orchestrator 同步。 |
| B-2 | “产品提供完整材料”与 “允许继续澄清缺口”语义略冲突：完整材料通常不需要大量 interview。 | 用户可能困惑 B 与 D 的区别。 | 将 B 描述改为“已有材料但不保证完整/允许澄清”，D 才是“完整 PRD 直通”。 |
| B-3 | B/D 资料准备态创建 raw `requirements.md` inbox，但 `ship-define` 的事实源也是 `requirements.md`。 | raw inbox 与规范化 requirements 同名，可能让恢复逻辑误以为已有正式产物。 | raw inbox 使用单独路径如 `resource/raw-prd-inbox.md`，或在 frontmatter 增加 `artifact_state: raw_inbox | normalized`。 |

### 2.4 场景 D：PRD 直通 prd_direct

入口信号：完整 PRD + 原型/设计稿，用户明确不需要需求录入。

期望路径：

```text
ship-orchestrator
→ ship-define(prd_direct, zero-question extraction)
→ ship-define-review(PRD source quality + extraction accuracy + checklist)
→ Design / Build / Close
```

证据：
- README D 起点为 `ship-define(prd_direct mode)`。
- `ship-define/SKILL.md` prd_direct 模式要求零提问、纯提取，GAP 标记影响 `stage_status`。
- `ship-define-review/SKILL.md` 对 prd_direct 有专门评审流程。

发现：

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| D-1 | “零提问”与“阻塞性 GAP 导致 draft”之间缺少解除路径说明：如果 PRD 有阻塞 GAP，是继续保持 D，还是切 B interview？ | 执行中可能卡住：不能提问，但又不能 ready。 | 明确 prd_direct GAP 处理：阻塞 GAP 时转为 `product_provided/interview` 或要求用户补 PRD 后重跑 D。 |
| D-2 | D + backend_only 附加提示说 PRD 应包含 OpenAPI/接口文档/设计 doc；但仍允许。 | 若用户只给产品 PRD，contract 阶段可能缺输入。 | 在 D + backend_only 启动确认中要求用户明确材料类型，否则建议自动降级到 B。 |

### 2.5 场景 E：技术方案选区 technical_plan_provided

入口信号：已有技术方案文件/片段，并指定章节、接口、模块或标题；必须是 existing_project。

期望路径：

```text
ship-orchestrator
→ ship-tech-discovery(technical plan entry)
   - 派生最小 requirements.md index
   - Project Reality Scan
   - Research Alignment Check
→ ship-contract(selected scope only)
→ frontend/backend design(selected scope only)
→ ship-design-review
→ ship-delivery-plan(selected scope only)
→ ship-plan-review
→ ship-build
→ ship-verify
→ ship-handoff
```

证据：
- README 场景 E 起点为 `ship-tech-discovery`，跳过 Discover 和 Define。
- orchestrator 明确 E 跳过 `ship-define` 与 `ship-define-review`，但要求派生最小 requirements index。
- protocol 规定 E 不能直接进 delivery plan，仍必须经过 tech-discovery、contract、必要 design 和 design-review。
- `ship-contract`、`ship-frontend-design`、`ship-backend-design`、`ship-delivery-plan` 都有 selected scope 裁剪规则。

发现：

| 编号 | 问题 | 影响 | 建议 |
|---|---|---|---|
| E-1 | 场景 E 跳过 define gate，但派生的最小 AC 只是 `ship-tech-discovery` 内的 Research Alignment Check，没有统一 hard gate 签字。 | 技术方案可能缺少“做到什么算完成”的产品确认，后续计划和验收都建立在 AI 提取的 AC 上。 | 为 E 增加轻量 `selected_scope_ac_confirmation` 字段或在 `ship-design-review` 前强制用户确认最小 AC；不一定恢复完整 define gate。 |
| E-2 | README 说 E 跳过 Discover 和 Define；orchestrator/protocol 说 `stages.ship-define.generation_mode=technical_plan` 且由 tech-discovery 派生 `requirements.md`。 | 表达上容易误解：跳过阶段但仍产生该阶段主要产物。 | 统一文案为“跳过 ship-define 执行阶段，但仍由 tech-discovery 派生最小 requirements index”。 |
| E-3 | E 只创建 `resource/README.md`，不创建 raw PRD inbox；但必须归档技术方案来源到 resource 或可读路径。未说明粘贴片段何时写成 `resource/technical-plan-excerpt.md`。 | 粘贴输入可能只存在对话，不利于后续审计。 | 在 orchestrator 初始化 E 时强制把粘贴片段写入 `resource/technical-plan-excerpt.md`，并记录在 `technical_plan_source.pasted_excerpt_file`。 |
| E-4 | `technical_plan_source.repository_scan_required=true`，但如果 scan blocked，后续如何处理不够明确。 | 可能在 existing_project 无法扫描时仍推进到 contract/plan。 | 明确 `repository_scan_status=ready` 是进入 `tech-selection.md.ready` 的前置；blocked 时只能 draft。 |

## 3. 横向阶段冲突与不合理点

### 3.1 `ship-shape` 条件与 B/D UIUX Material Gate 冲突

证据：
- protocol 说 `ship-shape` 仅 A/C 激活，B/D/E 跳过。
- orchestrator 说 B/D 缺 UIUX 材料且用户授权生成线框时，允许插入 `ship-shape` 后再回到 `ship-define`。

判断：这是当前最明确的协议冲突之一。

建议：
- 修改 protocol 对 `ship-shape` 的定义：
  - 默认激活：A/C 且涉及 UI 且无外部 UIUX。
  - 条件插入：B/D 经 UIUX Material Gate 用户显式授权。
  - 禁止：E、backend_only、无 UI。
- `meta.yml.stages.ship-shape.status` 支持 `inserted` 或在 `skip_log` 中记录插入原因。

### 3.2 `ship-delivery-plan` 固定 frontend → backend → sync 与并行设计理念不完全一致

证据：
- orchestrator 并行规则说 frontend/backend design 是 sibling stages，可并行。
- orchestrator 又规定 delivery-plan 阶段内固定 `frontend → backend → sync`。
- protocol 中 `ship-delivery-plan` 是 forbidden，不委派，阶段内固定 `frontend -> backend -> sync`。

判断：不一定是错误，但会降低 fullstack 计划阶段效率，也与“前后端并行任务”的交付理念有点不匹配。

建议：
- 如果坚持顺序，说明原因：先前端 plan 是为了从用户路径驱动后端任务。
- 如果要提高效率，改为：`contract tasks → frontend/backend task draft parallel → sync`。
- 至少把 delivery plan 的“固定顺序”写成设计选择，而不是隐含约束。

### 3.3 `verification.md` frontmatter `stage: ship-handoff` 反直觉

证据：
- protocol 说明 `verification.md` 是 shared artifact，frontmatter `stage` 固定写 `ship-handoff`。
- `ship-verify/SKILL.md` 也强调这是刻意 ownership 设计。

判断：设计上可成立，但容易被自动校验/人工审计误判为 `ship-verify` 没有产物。

建议：
- 在 `verification.md` frontmatter 增加 `produced_by: [ship-verify]`、`accepted_by: ship-handoff` 或 `artifact_phase: testing | acceptance`。
- 验证脚本必须显式容忍 `ship-verify` 输出 `stage=ship-handoff`，避免未来维护者误修。

### 3.4 soft gate 可强制推进与阶段内部“不得进入下游”语气冲突

证据：
- orchestrator soft gate 规则：`stage_status: draft` 时可提示风险，用户可强制推进并写 `skip_log`。
- 多个阶段 SKILL 写明阻塞项未解决不得 `ready`、不得进入下游。
- hard gate 不可跳过，这一点清楚。

判断：soft gate 的强制推进适合非关键普通阶段，但 requirements、contract、delivery plan 等其实可能是高风险软门禁。

建议：
- 将 soft gate 分级：
  - `soft_optional`：可用户强推。
  - `soft_blocking`：虽非 hard review，但没有 ready 不可推进，如 `api-contract.md`、derived `requirements.md`、`tech-selection.md`。
- 或在各阶段 frontmatter 增加 `blocking_gaps: []`，只要非空就不可 skip。

### 3.5 `meta.yml` 阶段状态枚举与 artifact 状态枚举不完全统一

证据：
- `meta.yml.template` 普通阶段状态含 `pending/in_progress/ready/blocked/completed`。
- artifact frontmatter 使用 `draft/ready/complete`。
- orchestrator 又说阶段完成后回写 `ready/approved/completed`。

判断：这是有意区分索引层与事实源，但执行者容易混淆 `ready` vs `completed`、`complete` vs `completed`。

建议：
- 在 protocol 加一张状态映射表：
  - artifact `draft` → meta `in_progress` 或 `blocked`
  - artifact `ready` → meta `ready`
  - orchestrator 已推进到下一阶段 → 上一阶段 meta `completed`
  - artifact `complete` → meta `completed`
- 统一说明 `complete` 只出现在 artifact，`completed` 只出现在 meta。

### 3.6 子代理产出边界清楚，但实际“每个场景入口委托一个子代理”容易超时

本次执行尝试已经暴露：按场景委派多个 delegate，读取大批文档时容易超时，且子代理 session 可能不可恢复。

建议：
- 对审计类任务，子代理输入应更小：每个代理只读 2-4 个文件，并要求输出最多 5 个问题。
- 或先由主代理生成场景矩阵，再让子代理只验证特定假设。
- 对 skills 工作流自身可增加一个“workflow-audit”脚本或 checklist，避免完全依赖人工/子代理长上下文。

## 4. 逐阶段检查摘要

| 阶段 | 主要输入 | 主要输出 | 主要风险 |
|---|---|---|---|
| ship-orchestrator | 用户意图、meta、feature docs | 路由、meta 更新 | 场景 B/D 插入 shape 与协议冲突；状态映射复杂 |
| ship-discover | 一句话想法/旧功能基线 | product-brief.md | 用户方向确认字段不标准；evolve baseline 不持久 |
| ship-shape | product-brief/UI 缺口 | design-brief.md、wireframes | 默认仅 A/C，但 B/D gate 可插入 |
| ship-define | PRD/product brief/design brief | requirements.md | raw inbox 与正式 requirements 同名；D 模式 GAP 解除路径不明 |
| ship-define-review | requirements.md | review-define.md | 规则较清楚；E 跳过后 AC 确认不足 |
| ship-tech-discovery | requirements / selected scope | tech-research.md、tech-selection.md | E 派生 requirements 的确认机制弱；scan blocked 处理需更硬 |
| ship-contract | tech-selection | api-contract.md | selected scope 裁剪合理；需确保单侧 scope contract 形态不被误跳过 |
| ship-frontend-design | api-contract、UIUX | frontend-design.md | 缺 UIUX 时的阻塞与 shape 插入需统一 |
| ship-backend-design | api-contract、tech-selection | backend-design.md | 与 frontend sibling 并行清楚 |
| ship-design-review | contract + FE/BE design | review-design.md | hard gate 规则清楚 |
| ship-delivery-plan | approved design | frontend/backend plan | fullstack 顺序固定可能不合理；单侧 scope 下产物命名需明确 |
| ship-plan-review | plan docs | review-plan.md | hard gate 规则清楚 |
| ship-build | approved plan | code/tasks | 单 DOING 合理；辅助委派边界清楚 |
| ship-verify | build complete | verification.md testing sections | frontmatter stage=handoff 反直觉 |
| ship-handoff | verification ready、requirements AC | handoff.md、verification complete | all_ac_verified 与 FAIL/BLOCKED 风险接受逻辑需持续清晰 |
| ship-spec | workspace spec | spec_context / referenced specs | 非 stage，hook 规则清楚；缺规 warn 策略合理 |

## 5. 建议优先级

### P0：应尽快修正

1. **统一 `ship-shape` 激活条件**：解决 A/C only 与 B/D UIUX Material Gate 插入之间的协议冲突。
2. **补强场景 E 最小 AC 的用户确认机制**：避免技术方案 selected scope 直接绕过需求确认。
3. **明确 raw inbox 与正式 requirements 的区别**：避免恢复和门禁误判。

### P1：建议近期修正

4. 为 C 场景增加 `evolve_source` 元数据。
5. 为 `verification.md` 增加 shared artifact 辅助字段，降低误解。
6. 为 soft gate 增加 blocking/non-blocking 分级。
7. 给 meta/artifact 状态做映射表。

### P2：优化项

8. 解释或调整 `ship-delivery-plan` 的 frontend→backend→sync 固定顺序。
9. 统一所有“用户确认”字段和记录模板。
10. 为 workflow audit 增加脚本化检查项，覆盖当前 validate 脚本未覆盖的语义冲突。

## 6. 本次复查结论

- 当前 `validate_workflow_docs.py` 通过，说明基础协议字段/文档校验 OK。
- 但从入口到结束的场景追踪看，仍存在若干语义冲突和执行歧义，尤其是：
  - B/D 是否可插入 `ship-shape`；
  - E 跳过 Define gate 后如何确认 AC；
  - raw inbox 与 requirements 正式产物同名；
  - verification shared ownership 的可理解性。

建议先按 P0 修正共享协议和 orchestrator 文案，再补充脚本校验这些语义规则。