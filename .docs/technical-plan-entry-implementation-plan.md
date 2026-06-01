# 技术方案选区入口实施计划

## 1. 背景与目标

当前 `ship-orchestrator` 支持四种 NEW_FEATURE 入口：`greenfield`、`product_provided`、`evolve`、`prd_direct`。这些入口分别面向从零需求、产品资料、已有功能增强和 PRD 直通，但还不支持“已有技术方案文件 + 用户指定章节/接口/片段，只围绕选中范围生成实施计划”的场景。

本次目标是新增一种受控入口，使已有项目迭代可以从技术方案选区进入 workflow，并最终进入 `ship-delivery-plan` 生成 plan。该入口不支持新项目，不直接进入 `ship-build`，也不把技术方案未选中内容纳入计划。

目标行为：

1. 用户提供技术方案文件，或直接粘贴方案片段。
2. 用户用章节、接口、模块、标题等描述本次关注范围。
3. orchestrator 只围绕选中范围做仓库探索和 Project Reality Scan。
4. 未选中内容默认视为 Out of Scope，不进入 plan。
5. 若未选中内容构成前置依赖或冲突，只记录为 risk / open question，不自动扩大范围。
6. 生成 `ship-delivery-plan` 所需的上游最小产物，并通过 `ship-design-review` 后进入 `ship-delivery-plan`。

## 2. 非目标

本次不做以下能力：

1. 不新增 canonical stage。
2. 不允许新项目使用该入口。
3. 不允许绕过 `ship-design-review` 直接进入 `ship-delivery-plan`。
4. 不允许绕过 `ship-plan-review` 直接进入 `ship-build`。
5. 不解析整份技术方案为完整 PRD。
6. 不把未选中章节自动纳入实施计划。
7. 不支持复杂文档分页定位；若用户只提供页码且无法可靠定位，要求用户补充章节名或直接粘贴片段。

## 3. 入口定义

新增 scenario：

```yaml
scenario: technical_plan_provided
```

中文名称：

```text
E 技术方案选区入口
```

入口信号：

- 用户说明“已有技术方案，按其中某章节生成计划”
- 用户提供技术方案文件路径，并指定章节、接口、模块或标题
- 用户直接粘贴技术方案局部内容，并要求基于这部分进入 plan 后续流程
- 用户明确这是已有项目迭代，不是新项目

典型 prompt：

```text
使用 ship-orchestrator，基于 resource/order-export-tech-design.md 的 3.2 订单导出异步任务章节生成 delivery plan。
```

```text
这是技术方案片段，只计划 POST /api/v1/orders/export 这一部分，先探索仓库再生成 plan：
<粘贴内容>
```

## 4. 输入模型

在 `meta.yml` 中新增技术方案选区摘要字段，作为 orchestrator 索引层；原始技术方案文件仍归档到 `resource/`。

推荐字段：

```yaml
technical_plan_source:
  source_files: []
  selection_mode: ""          # referenced_sections | pasted_excerpt
  selected_scope: []
  pasted_excerpt_file: ""     # 直接粘贴内容归档后的路径，如 resource/technical-plan-excerpt.md
  ignored_source_policy: out_of_scope
  repository_scan_required: true
  repository_scan_status: pending
```

约束：

- `technical_plan_source` 是索引层，不是技术方案正文事实源。
- 原始技术方案文件必须保留在 `resource/`，或由用户提供明确可读路径后复制/归档到 `resource/`。
- 直接粘贴内容必须归档为 `resource/technical-plan-excerpt.md`，不得只存在对话上下文中。
- `repository_scan_status` 只记录 selected scope 的仓库探索状态，不代表整份技术方案已探索。

`selected_scope` 推荐结构：

```yaml
selected_scope:
  - type: section             # section | api | module | component | freeform
    label: "3.2 订单导出异步任务"
    source_file: "resource/order-export-tech-design.md"
    locator: "heading"
```

字段语义：

| 字段 | 说明 |
|------|------|
| `source_files` | 技术方案来源文件，必须在 `resource/` 或用户明确提供的可读路径中 |
| `selection_mode` | `referenced_sections` 表示文件 + 章节/接口引用；`pasted_excerpt` 表示直接粘贴片段 |
| `selected_scope` | 本次唯一进入计划的选中范围 |
| `pasted_excerpt_file` | 粘贴内容归档文件路径 |
| `ignored_source_policy` | 固定为 `out_of_scope`，表示未选中内容不进入 plan |
| `repository_scan_required` | 固定为 `true` |
| `repository_scan_status` | `pending | in_progress | ready | blocked` |

## 5. 路由策略

不新增 stage，复用现有 canonical stages。

推荐路径：

```text
technical_plan_provided
→ ship-define
→ ship-define-review
→ ship-tech-discovery
→ ship-contract
→ ship-frontend-design / ship-backend-design
→ ship-design-review
→ ship-delivery-plan
```

该路径的特殊规则：

1. `ship-define` 不做完整 PRD 录入，只提取选区对应的最小 `requirements.md`。
2. `requirements.md` 只覆盖 selected scope，不覆盖整份技术方案。
3. `ship-tech-discovery` 必须执行 Project Reality Scan，且扫描范围围绕 selected scope。
4. `ship-contract`、`ship-frontend-design`、`ship-backend-design` 按 project_scope 和 selected scope 裁剪。
5. `ship-design-review` 仍是硬门禁，确认 contract / frontend / backend design 与 selected scope 一致。
6. `ship-delivery-plan` 只为 selected scope 生成 `frontend-plan.md` / `backend-plan.md` 或单侧 plan。

门禁说明：

- 不能把 `technical_plan_provided` 设计为“直接跳到 `ship-delivery-plan`”的场景。
- `stage_transition_check.py` 必须仍然要求 `ship-define-review`、`ship-tech-discovery`、`ship-contract`、`ship-design-review` 满足现有退出条件。
- `repository_scan_status: ready` 只能作为补充索引；真正允许进入 `ship-contract` 的事实源仍是 `tech-research.md` 和 `tech-selection.md` 的 frontmatter 与内容校验。

## 6. 最小 AC 规则

技术方案通常描述“怎么实现”，但 workflow 需要 `Acceptance Criteria` 描述“做到什么算完成”。没有 AC 时，plan、build、verify 和 handoff 都会缺少验收锚点。

示例技术方案片段：

```text
新增订单导出接口，支持 CSV，后端使用异步任务生成文件。
```

这不是 AC，因为它没有说明用户可验收的结果、边界和异常。

应提取为最小 AC：

```text
AC-ORDER-001：当管理员选择订单时间范围并提交导出时，系统创建导出任务并返回任务 ID。
AC-ORDER-002：当导出任务完成后，管理员可以下载 CSV 文件，文件包含订单号、金额、状态、创建时间。
AC-ORDER-003：当导出时间范围超过允许上限时，系统拒绝请求并返回可理解的错误信息。
```

本入口的 AC 策略：

1. 只为 selected scope 提取 AC。
2. 如果技术方案中已有明确验收标准，直接引用并标准化 ID。
3. 如果没有明确 AC，由 agent 从选区提取“最小可验收结果”，并在 `ship-define-review` 中要求用户确认。
4. 不允许在 AC 缺失时把 `requirements.md.stage_status` 标记为 `ready`。
5. 每个 delivery plan task 必须引用至少一个 AC ID。

## 7. 仓库探索规则

该入口只支持已有项目，因此仓库探索是必需步骤。

探索目标：

1. 找到 selected scope 对应的现有代码、接口、页面、服务、表、任务、MQ、测试和旧 feature 文档。
2. 判断 selected scope 中每个关键点是 `reuse / extend / replace / new / avoid / unknown`。
3. 识别真实项目边界和 `project_scope`。
4. 为后续 plan 提供 `allowed_files`、依赖、验证命令和风险依据。

探索范围：

- 优先按用户提供的代码路径、接口名、模块名和章节关键词搜索。
- 不扫描技术方案未选中章节对应的功能。
- 若发现未选中内容是 selected scope 的前置依赖，记录为 `risk` 或 `open question`，并询问是否扩大 scope。

阻塞条件：

1. 无法确认这是已有项目。
2. 无法定位技术方案选区。
3. selected scope 依赖未选中内容且不扩 scope 就无法生成可执行 plan。
4. 无法确定 `project_scope`，且用户拒绝确认 fullstack/backend_only/frontend_only。

## 8. 文件级修改清单

### 8.1 文档与协议

修改 `skills/ship-orchestrator/SKILL.md`：

- 在 Empty Entry Handling 的新建模式中加入“技术方案选区入口”。
- 在 Scenario Detection 中新增场景 E。
- 明确该场景 `Discover` 跳过，但 `Project Reality Scan` 必须在 Design 大阶段执行。
- 新增启动确认模板，要求展示：
  - 技术方案来源
  - selected scope
  - 忽略未选中内容的策略
  - 仓库探索要求
  - 将进入 `ship-delivery-plan` 前仍需通过 `ship-design-review`

修改 `skills/README.md` 和根 `README.md`：

- 增加入口示例。
- 说明该入口只适用于已有项目迭代。
- 说明不会把整份技术方案纳入计划。

修改 `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`：

- 增加 `technical_plan_provided` 的 scenario 语义。
- 说明不新增 canonical stage。
- 增加 selected scope、未选中内容、仓库探索、最小 AC 的协议约束。

修改 `skills/ship-orchestrator/_templates/meta/meta.yml.template`：

- `scenario` 注释增加 `technical_plan_provided`。
- 新增 `technical_plan_source` 字段。

### 8.2 阶段 skill

修改 `skills/ship-define/SKILL.md`：

- 增加 `technical_plan_provided` generation mode 或子模式。
- 说明该模式只提取 selected scope 的最小 requirements 和 AC。
- 说明技术方案原文不直接作为 `requirements.md` 合同。
- 更新 `requirements.md` frontmatter 示例，允许 `generation_mode: technical_plan`。
- 明确 `technical_plan` 模式必须写入 `source_documents` 或等价来源索引，引用 selected scope 来源位置。

修改 `skills/ship-define-review/SKILL.md`：

- 增加技术方案选区评审检查：
  - selected scope 是否明确
  - AC 是否覆盖 selected scope
  - 未选中内容是否未被错误纳入 scope
  - 是否确认已有项目前提
- 更新 `generation_mode` 判定规则，识别 `technical_plan` 并执行技术方案选区评审流程。
- 更新 `review-define.md` frontmatter 注释，使 `generation_mode` 可继承 `interview | prd_direct | technical_plan`。

修改 `skills/ship-tech-discovery/SKILL.md`：

- 增加技术方案选区入口下的 Project Reality Scan 裁剪规则。
- 要求 `Requirement-to-Reality Mapping` 只覆盖 selected scope。

修改 `skills/ship-contract/SKILL.md`：

- 增加 selected scope contract 裁剪规则。
- 未选中接口不得进入本期 contract，除非作为依赖风险记录。

修改 `skills/ship-frontend-design/SKILL.md` 和 `skills/ship-backend-design/SKILL.md`：

- 增加 selected scope design 裁剪规则。
- 计划只覆盖 selected scope 相关页面/组件/服务/数据模型。

修改 `skills/ship-delivery-plan/SKILL.md`：

- 明确在 `technical_plan_provided` 下只为 selected scope 生成任务。
- 每个 task 必须可追溯到 selected scope、AC ID 和仓库探索证据。
- 未选中内容不得生成任务。

### 8.3 Runtime helper 与校验

修改 `skills/ship-orchestrator/scripts/feature_meta_runtime.py`：

- `VALID_SCENARIOS` 增加 `technical_plan_provided`。
- 增加 `TECHNICAL_PLAN_SCENARIOS` 或等价集合，避免把该场景错误归入 `DEFINE_SCENARIOS` 的 raw PRD inbox 逻辑。
- 初始化该 scenario：
  - `current_stage: ship-define`
  - `stages.ship-discover.status: skipped`
  - `stages.ship-shape.status: skipped`
  - `stages.ship-define.generation_mode: technical_plan`
  - `project_context: existing_project`
  - `technical_plan_source.repository_scan_required: true`
- 若用户尝试用新项目创建该 scenario，直接报错。
- 为 `init` 命令增加技术方案选区参数，至少支持：
  - `--technical-source-file`
  - `--technical-selected-scope`
  - `--technical-selection-mode referenced_sections | pasted_excerpt`
  - `--technical-pasted-excerpt-file`
- `create_material_intake_files()` 对 `technical_plan_provided` 只创建 `resource/README.md`，不复制 raw PRD inbox 模板；`requirements.md` 应由 `ship-define` 生成结构化合同。

修改 `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`：

- 校验 `technical_plan_provided` 必须有 `technical_plan_source`。
- 校验 `source_files` 或 `pasted_excerpt_file` 至少存在一种。
- 校验 `selected_scope` 非空。
- 校验 `project_context` 必须为 `existing_project`。
- 校验 `repository_scan_status` 在 `ship-tech-discovery` 产物 ready 后必须为 `ready`，并且不得替代 `tech-research.md` / `tech-selection.md` 的既有校验。

修改 `skills/ship-orchestrator/scripts/validate_requirements.py`：

- 识别 `generation_mode: technical_plan`。
- 校验 technical plan 模式下 `requirements.md` 必须包含 selected scope 来源索引。
- 校验 ready 状态下仍必须有 Domain ID、AC ID、In Scope / Out of Scope、待确认问题和资料索引。
- 避免把 `technical_plan` 当作 raw PRD inbox 或普通 interview 模式静默处理。

修改 `skills/ship-orchestrator/scripts/stage_transition_check.py`：

- 对 `technical_plan_provided` 跳过 `ship-discover` / `ship-shape`。
- 不跳过 `ship-define-review`、`ship-tech-discovery`、`ship-contract`、`ship-design-review`。
- 阻止直接跳到 `ship-delivery-plan`，除非上游产物和硬门禁完整。
- 保持 standard 路径下 `ship-delivery-plan` 的前置要求为 `review-design.md approved + user_sign_off + signed_at`。

修改 `skills/ship-orchestrator/scripts/validate_delivery_plan.py`：

- 如果 meta 是 `technical_plan_provided`，增加检查：
  - task 中应引用 selected scope 或 technical source。
  - task 不应引用未选中章节作为实现范围。
  - 每个 task 仍需 `allowed_files`、AC refs、verification command。

修改 `skills/ship-orchestrator/scripts/validate_workflow_docs.py`：

- 将 README / protocol / meta template / orchestrator 对 `technical_plan_provided` 的描述纳入一致性校验。
- 更新 “场景（A/B/C/D）” 等固定文案检查，避免新增场景后校验脚本仍要求旧表述。
- 增加对 `technical_plan_source`、`technical_plan` generation mode 的文档同步检查。

### 8.4 回归测试

修改 `skills/ship-orchestrator/tests/regression-prompts.md`，新增场景：

1. 技术方案文件 + 章节入口。
2. 直接粘贴技术方案片段入口。
3. 技术方案入口但 project_context 为 new_project，应阻塞。
4. selected_scope 为空，应阻塞。
5. 试图直接进入 `ship-delivery-plan` 但缺少 `review-design.md approved`，应阻塞。
6. plan 包含未选中章节任务，应报告问题。
7. `technical_plan_provided` 初始化不应创建 raw PRD inbox。
8. `generation_mode: technical_plan` 的 requirements ready 但缺少 selected scope 来源索引，应报告问题。

修改 `skills/ship-orchestrator/scripts/test_workflow_hardening.py`：

- 增加 feature 初始化测试。
- 增加 artifact validation 测试。
- 增加 stage transition 测试。
- 增加 delivery plan selected scope 校验测试。
- 增加 `validate_requirements.py` 对 `technical_plan` generation mode 的测试。

修改 `skills/ship-orchestrator/scripts/test_spec_runtime.py`：

- 增加 `feature_meta_runtime.py init --scenario technical_plan_provided` 的初始化测试。
- 验证 `project_context != existing_project` 时拒绝创建。
- 验证 `technical_plan_source` 初始化字段、`current_stage`、`generation_mode` 和 skipped stages。

## 9. 推荐实施顺序

### Step 1：协议与文档

修改：

- `workflow-protocol.md`
- `ship-orchestrator/SKILL.md`
- `skills/README.md`
- 根 `README.md`
- `meta.yml.template`
- `validate_workflow_docs.py`

验证：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

### Step 2：runtime 初始化

修改：

- `feature_meta_runtime.py`
- `test_spec_runtime.py`

验证：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_spec_runtime.py
```

重点验证：

- `technical_plan_provided` 可创建 feature。
- 新项目上下文被拒绝。
- `technical_plan_source` 初始字段存在。
- `ship-discover` / `ship-shape` 被 skipped。
- `current_stage` 为 `ship-define`。
- 不创建 raw PRD inbox 模板。

### Step 3：artifact 与 transition 校验

修改：

- `validate_feature_artifacts.py`
- `validate_requirements.py`
- `stage_transition_check.py`
- `test_workflow_hardening.py`

验证：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

重点验证：

- selected scope 缺失时报错。
- requirements ready 但缺少 selected scope 来源索引时报错。
- 未完成 `ship-design-review` 时不能进入 `ship-delivery-plan`。
- 已完成上游产物和硬门禁后允许进入 `ship-delivery-plan`。

### Step 4：阶段 skill 适配

修改：

- `ship-define/SKILL.md`
- `ship-define-review/SKILL.md`
- `ship-tech-discovery/SKILL.md`
- `ship-contract/SKILL.md`
- `ship-frontend-design/SKILL.md`
- `ship-backend-design/SKILL.md`
- `ship-delivery-plan/SKILL.md`

验证：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

人工复查：

- 每个阶段都明确 selected scope 裁剪规则。
- 没有任何阶段暗示可以把整份技术方案纳入 plan。
- 没有任何阶段允许绕过硬门禁。

### Step 5：delivery plan 校验增强

修改：

- `validate_delivery_plan.py`
- `test_workflow_hardening.py`

验证：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

重点验证：

- task 必须引用 AC。
- task 必须有 `allowed_files`。
- task 必须有 verification command。
- 技术方案入口下 task 不能脱离 selected scope。

## 10. 风险与取舍

### 风险 1：技术方案与真实代码不一致

处理：

- 强制 Project Reality Scan。
- 冲突写入 `tech-research.md` 的 `Conflicting Evidence`。
- 不允许在冲突未解释时继续生成 ready 设计。

### 风险 2：用户选区描述无法定位

处理：

- 章节/接口定位失败时阻塞。
- 要求用户补充更精确章节名、接口名或直接粘贴片段。

### 风险 3：选区依赖未选中内容

处理：

- 不自动扩大 scope。
- 写入 risk / open question。
- 询问用户是否把依赖纳入 selected scope。

### 风险 4：AC 过度推断

处理：

- agent 只能提取最小 AC 草案。
- `ship-define-review` 必须要求用户确认。
- 未确认时不得进入 ready。

### 风险 5：改动范围过大

处理：

- 不新增 canonical stage。
- 不改 14 阶段顺序。
- 新入口只作为 scenario 和阶段内裁剪规则存在。

## 11. 成功标准

实施完成后，应满足：

1. 用户可以用“技术方案文件 + 章节/接口描述”创建 feature。
2. 用户可以直接粘贴技术方案片段创建 feature。
3. 新入口必须要求已有项目上下文。
4. 新入口会跳过 Discover，但不会跳过 Define / Design / hard gates。
5. 仓库探索只围绕 selected scope。
6. `requirements.md` 只包含 selected scope 的最小 Domain / AC。
7. `ship-delivery-plan` 只生成 selected scope 对应任务。
8. 未选中技术方案内容不会进入 plan。
9. 缺少 selected scope、AC、仓库探索证据或硬门禁时，校验脚本会阻塞推进。

## 12. 复查清单

修改完成后逐项复查：

- [ ] `VALID_SCENARIOS` 已包含 `technical_plan_provided`
- [ ] `feature_meta_runtime.py` 已拒绝 `technical_plan_provided + new_project`
- [ ] `feature_meta_runtime.py` 未为 `technical_plan_provided` 创建 raw PRD inbox
- [ ] `meta.yml.template` 已包含 `technical_plan_source`
- [ ] 新入口不能用于 new_project
- [ ] 新入口初始化时 `ship-discover` / `ship-shape` 为 skipped
- [ ] 新入口不会直接进入 `ship-delivery-plan`
- [ ] `stage_transition_check.py` 仍要求 `ship-design-review` 通过
- [ ] `validate_feature_artifacts.py` 能发现 selected scope 缺失
- [ ] `validate_requirements.py` 能识别 `generation_mode: technical_plan`
- [ ] `validate_delivery_plan.py` 能发现脱离 selected scope 的 task
- [ ] `ship-define` 明确最小 AC 提取与用户确认规则
- [ ] `ship-tech-discovery` 明确仓库探索裁剪规则
- [ ] `ship-delivery-plan` 明确只计划 selected scope
- [ ] README、skills README、workflow protocol 三处说法一致
- [ ] `validate_workflow_docs.py` 已同步新增场景文案检查
- [ ] 回归 prompt 覆盖文件引用、粘贴片段、新项目拒绝、直接跳转拒绝
