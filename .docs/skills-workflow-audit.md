# skills/ 技能工作流审计报告

> 审计对象：`skills/` ShipKit 技能工作流  
> 审计方式：按 A/B/C/D/E 五个入口场景分别委托只读子代理追踪，主代理复核 `README`、`ship-orchestrator`、关键阶段 Skill、runtime/validator/transition 脚本。  
> 结论状态：只读审计，未修改工作流源文件。

## 1. 总体结论

这套 `skills/` 工作流主体结构是完整的：默认对外呈现 `[Discover →] Define → Design → Build → Close` 五个宏阶段，内部通过 14 个 canonical stages 推进，并保留 `ship-define-review`、`ship-design-review`、`ship-plan-review` 三道硬门禁。

核心问题不在于主阶段顺序错误，而在于条件分支、状态回流、脚本校验与文档语义之间仍有若干未闭环点，尤其集中在：

- B/D 场景的 `UIUX Material Gate` 插入 `ship-shape` 后，transition checker 可能没有强制检查该插入阶段。
- D 场景 `backend_only` 的契约级材料验收要求只写在 orchestrator，未在 define-review 检查项中闭环。
- E 场景启动摘要中 `selected_scope_ac_confirmation`、`contract`、`design-review`、`delivery-plan` 的表述顺序容易误导。
- C 场景 evolve impact scan 与 `ship-tech-discovery` 的 Project Reality Scan 有职责重叠，需要明确边界。
- `project_scope` 冻结规则主要停留在文档层，缺少脚本级变更保护。

## 2. 阶段图复核

### 2.1 宏阶段

证据：

- `skills/README.md:9`
- `skills/README.md:146`
- `skills/ship-orchestrator/SKILL.md:203`
- `skills/ship-orchestrator/SKILL.md:248`

宏阶段为：

```text
[Discover →] Define → Design → Build → Close
```

### 2.2 Canonical stages

证据：

- `skills/ship-orchestrator/SKILL.md:209`
- `skills/ship-orchestrator/scripts/workflow_stage_map.py:30`

内部阶段顺序为：

```text
[ship-discover → ship-shape →]
ship-define → ship-define-review
→ ship-tech-discovery
→ ship-contract → ship-frontend-design → ship-backend-design
→ ship-design-review
→ ship-delivery-plan
→ ship-plan-review
→ ship-build → ship-verify → ship-handoff
```

其中：

- `ship-discover`：仅 A/C 默认激活。
- `ship-shape`：A/C 默认可激活；B/D 可由 `UIUX Material Gate` 插入；E、`backend_only`、无 UI 禁止。
- `ship-frontend-design` 与 `ship-backend-design` 是 sibling stages，可并行启动，最终由 `ship-design-review` 收口。

## 3. 五个入口场景追踪

### 3.1 场景 A：零到一 greenfield

入口依据：

- `skills/README.md:26`
- `skills/ship-orchestrator/SKILL.md:89`

路径：

```text
ship-discover → ship-shape(若涉及 UI 且无外部 UIUX) → ship-define → ship-define-review → ship-tech-discovery → ship-contract → frontend/backend design → ship-design-review → ship-delivery-plan → ship-plan-review → ship-build → ship-verify → ship-handoff
```

主要发现：

- `ship-shape` 激活条件在文档中存在，但“自动进入”还是“先询问用户”表述不够统一。`skills/ship-orchestrator/SKILL.md:98` 偏自动路由，`skills/ship-shape/SKILL.md:25` 又强调用户明确不要设计时不能静默跳过。
- `project_scope` 可在 `ship-tech-discovery` 后基于证据确认，但前置阶段如何输出足够 scope 证据不够明确。证据见 `skills/ship-orchestrator/SKILL.md:127`。

### 3.2 场景 B：产品提供 product_provided

入口依据：

- `skills/README.md:27`
- `skills/ship-orchestrator/SKILL.md:90`

路径：

```text
ship-define(interview)
  或 UIUX Gate 插入 ship-shape 后回到 ship-define
→ ship-define-review → Design → Build → Close
```

主要发现：

- `UIUX Material Gate` 判定标准模糊。文档列举 Figma / 原型 / 截图 / `design-brief.md`，但未说明“不可访问链接”“部分页面原型”“只有截图”是否足够。证据见 `skills/ship-orchestrator/SKILL.md:102`。
- 插入 `ship-shape` 后回流 `ship-define` 的 raw inbox normalize 顺序不够显式。`ship-define` 要求 raw `requirements.md` 必须先 normalize，见 `skills/ship-define/SKILL.md:74`；但 B 场景从 `ship-shape` 回来时，如何同时处理 raw PRD 与 `design-brief.md` 需要补充。
- `frontend_only` 下仍保留 `ship-contract` 是合理的，但需要在用户-facing 文案中解释 contract 可是 UI/API client/mock/SDK/CLI 等消费契约，不一定意味着后端实现。证据见 `skills/ship-orchestrator/SKILL.md:134`。

### 3.3 场景 C：迭代增强 evolve

入口依据：

- `skills/README.md:28`
- `skills/ship-orchestrator/SKILL.md:91`
- `skills/ship-orchestrator/SKILL.md:104`

路径：

```text
ship-discover(evolve) → ship-shape(若涉及 UI 且无 UIUX) → ship-define → ship-define-review → ship-tech-discovery → Design → Build → Close
```

主要发现：

- evolve 必须有 `evolve_source` 基线，runtime/validator 已有一定支持。证据见 `skills/ship-orchestrator/scripts/feature_meta_runtime.py:876`、`skills/ship-orchestrator/scripts/validate_feature_artifacts.py:189`。
- `ship-discover` 的 impact scan 与 `ship-tech-discovery` 的 Project Reality Scan 职责有重叠。建议明确：Discover 阶段产出“产品变更影响假设和范围”，Tech Discovery 阶段产出“代码/表/API/权限/测试等技术事实复核”。证据见 `skills/ship-tech-discovery/SKILL.md:16`、`skills/ship-tech-discovery/SKILL.md:151`。
- C 与 E 都是 existing_project 相关入口，区别应更突出：C 从变更意图/旧功能出发，E 从已有技术方案 selected scope 出发。

### 3.4 场景 D：PRD 直通 prd_direct

入口依据：

- `skills/README.md:29`
- `skills/ship-orchestrator/SKILL.md:92`
- `skills/ship-orchestrator/SKILL.md:110`

路径：

```text
ship-define(prd_direct, zero-question extraction)
  或 UIUX Gate 插入 ship-shape 后回到 ship-define(prd_direct)
→ ship-define-review → Design → Build → Close
```

主要发现：

- D 场景 `backend_only` 的材料类型确认写在 orchestrator：需要 OpenAPI / 接口文档 / 设计 doc / 消息协议 / CLI spec 等契约级材料。证据见 `skills/ship-orchestrator/SKILL.md:146`。
- `ship-define-review` 的 PRD Direct 评审清单未显式包含上述 D + `backend_only` 契约级材料检查，导致要求没有在 hard gate 中闭环。
- PRD Direct 修订回路中，如果 PRD 源文件质量不达标，需要补资料；但 `requirements.md` 何时从 ready 回到 draft、`generation_mode` 是否保持 `prd_direct`，需要更明确的状态转换规则。

### 3.5 场景 E：技术方案选区 technical_plan_provided

入口依据：

- `skills/README.md:30`
- `skills/ship-orchestrator/SKILL.md:93`
- `skills/ship-tech-discovery/SKILL.md:30`

路径：

```text
ship-tech-discovery(derive minimal requirements index + selected scope AC confirmation + Project Reality Scan)
→ ship-contract → frontend/backend design(按 scope 裁剪) → ship-design-review → ship-delivery-plan → ship-plan-review → ship-build → ship-verify → ship-handoff
```

关键规则：

- 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate，但必须派生最小 `requirements.md` index。证据见 `skills/ship-orchestrator/SKILL.md:105`、`skills/ship-tech-discovery/SKILL.md:49`。
- 只围绕 `technical_plan_source.selected_scope` 工作，未选中内容默认 `out_of_scope`。证据见 `skills/ship-orchestrator/SKILL.md:107`、`skills/ship-tech-discovery/SKILL.md:63`。
- 仅允许 `project_context: existing_project`。证据见 `skills/ship-orchestrator/SKILL.md:106`。

主要发现：

- 启动确认文案中把“进入 delivery-plan 前仍需 design-review”和“contract 前完成 selected_scope_ac_confirmation”放在同一句末尾，顺序表达容易误导。证据见 `skills/ship-orchestrator/SKILL.md:159`。
- `repository_scan_status` 的同步责任不够具体。文档说明它只是 meta 索引，不是事实源，但没有明确何时由谁同步为 ready/blocked。证据见 `skills/ship-tech-discovery/SKILL.md:68`。
- derived `requirements.md` 是索引式，但 `ship-delivery-plan` 要求每个 task 追溯到 AC ID、selected scope、仓库探索证据。需要明确索引式 AC 的最低完整度。证据见 `skills/ship-tech-discovery/SKILL.md:108`、`skills/ship-delivery-plan/SKILL.md:122`。

## 4. 横切协议复核

### 4.1 事实源规则

证据：

- `skills/ship-orchestrator/SKILL.md:18`
- `skills/ship-orchestrator/SKILL.md:281`
- `skills/ship-orchestrator/SKILL.md:511`

规则：

- 阶段文档 frontmatter 是一级事实源。
- `meta.yml` 是 orchestrator 的恢复、汇总、展示索引。
- 冲突时优先信任产物 frontmatter，并回写 `meta.yml`。

该规则在文档层较清晰，但部分脚本只做局部校验，尚未覆盖所有条件分支。

### 4.2 硬门禁规则

证据：

- `skills/ship-orchestrator/SKILL.md:383`
- `skills/ship-orchestrator/scripts/stage_transition_check.py:69`

规则：

- `review_status=approved` 且 `user_sign_off`、`signed_at` 非空才允许推进。
- hard gate 不允许 skip 或强制通过。

该规则整体一致。

### 4.3 委派边界

证据：

- `skills/ship-orchestrator/SKILL.md:291`
- `skills/ship-orchestrator/SKILL.md:351`
- `skills/ship-delivery-plan/SKILL.md:90`

结论：

- 子代理是执行策略，不是新阶段。
- `ship-frontend-design` 与 `ship-backend-design` 可并行拥有正式输出。
- `ship-delivery-plan` 是 forbidden delegation，必须由主上下文顺序完成 frontend → backend → sync。

注意点：orchestrator 的 node 摘要把 `ship-delivery-plan` 列为 stage 级 node，见 `skills/ship-orchestrator/SKILL.md:322`；协议中又定义为 forbidden，并不构成硬冲突，但建议文案标注“stage 级 node 不代表可委派”。

## 5. 已确认的问题清单

### P0：应优先修复

#### P0-1：B/D 插入 `ship-shape` 后 transition checker 可能绕过检查

证据：

- 插入规则：`skills/ship-orchestrator/SKILL.md:103`
- runtime 插入函数：`skills/ship-orchestrator/scripts/feature_meta_runtime.py:857`
- transition 裁剪：`skills/ship-orchestrator/scripts/stage_transition_check.py:93`

问题：

`stage_transition_check.py` 对 `product_provided`、`prd_direct` 统一移除 `ship-discover` 和 `ship-shape` 作为前置阶段。若 B/D 已通过 UIUX Gate 把 `ship-shape.status` 覆写为 `pending/in_progress/ready`，推进到后续阶段时仍可能不强制检查 `design-brief.md` 是否 ready。

建议：

- 仅在 `stages.ship-shape.status == skipped` 时移除 `ship-shape`。
- 若 `activation_mode == uiux_material_gate_insert` 且 status 非 skipped，应要求 `design-brief.md.stage_status` 为 `ready`。

#### P0-2：D + `backend_only` 契约级材料要求未进入 hard gate

证据：

- 材料要求：`skills/ship-orchestrator/SKILL.md:146`
- 启动确认：`skills/ship-orchestrator/SKILL.md:158`

问题：

orchestrator 要求 D + `backend_only` 的 PRD 必须包含契约级材料，但 `ship-define-review` 的 PRD Direct 评审清单没有明确检查该条件。

建议：

- 在 `ship-define-review` 的 PRD Direct Phase 1 或 Phase 2 增加检查项：当 `scenario=prd_direct` 且 `project_scope=backend_only` 时，必须验证 OpenAPI / 接口文档 / 设计 doc / 消息协议 / CLI spec 等契约级材料存在且可引用。

#### P0-3：场景 E 启动确认摘要顺序表述不清

证据：

- `skills/ship-orchestrator/SKILL.md:159`

问题：

当前一句话同时描述 selected scope AC confirmation、contract、design-review、delivery-plan，顺序读起来不够清晰。

建议：

改为分步表达：

1. 先进入 `ship-tech-discovery`。
2. 在进入 `ship-contract` 前完成 `selected_scope_ac_confirmation`。
3. 之后完成 contract 和按 scope 裁剪的 frontend/backend design。
4. 进入 `ship-delivery-plan` 前必须通过 `ship-design-review`。

### P1：建议修复

#### P1-1：UIUX Material Gate 材料覆盖标准模糊

证据：

- `skills/ship-orchestrator/SKILL.md:102`
- `skills/ship-shape/SKILL.md:18`

建议补充判定标准：

- 链接是否可访问。
- 是否覆盖 Must Have 主流程。
- 是否覆盖关键页面、状态、异常路径。
- 仅有截图时是否允许继续，还是必须标注 UIUX 风险。

#### P1-2：B/D 插入 `ship-shape` 后回流 `ship-define` 的 normalize 顺序不清

证据：

- `skills/ship-orchestrator/SKILL.md:103`
- `skills/ship-define/SKILL.md:74`

建议：

明确回流 `ship-define` 后执行顺序：

1. 先检查 raw `requirements.md` inbox。
2. 如为 raw PRD，先 normalize。
3. 再合并读取 `design-brief.md` 与 `resource/wireframes/` 作为 UIUX 材料。
4. 最后产出结构化 `requirements.md`。

#### P1-3：C 场景 Discover impact scan 与 Tech Discovery scan 边界不清

证据：

- `skills/ship-tech-discovery/SKILL.md:16`
- `skills/ship-tech-discovery/SKILL.md:151`

建议：

- `ship-discover(evolve)`：负责产品层变更范围、影响假设、用户确认。
- `ship-tech-discovery`：负责代码/数据/API/权限/测试证据复核，不直接信任 Discover 结论。

#### P1-4：`project_scope` 冻结规则缺少脚本级保护

证据：

- `skills/ship-orchestrator/SKILL.md:131`
- `skills/ship-orchestrator/scripts/stage_transition_check.py:97`

建议：

- 在 `ship-design-review` approved 后记录 frozen scope。
- 后续 validator 若发现 `project_scope` 与 frozen scope 不一致，应报错或要求显式 migration/reopen gate。

#### P1-5：场景 E derived AC 最低完整度不明确

证据：

- `skills/ship-tech-discovery/SKILL.md:49`
- `skills/ship-tech-discovery/SKILL.md:108`
- `skills/ship-delivery-plan/SKILL.md:122`

建议：

补充 derived `requirements.md` index 的最低要求：

- 每个 selected scope 至少有 Domain ID。
- 每个可执行任务必须可回指至少一个 AC ID。
- AC 可以是索引式，但必须具备可验证结果、来源位置和 out-of-scope 边界。

## 6. 子代理结果中的误报修正

以下是主代理复核后确认的误报或需修正表述：

### 6.1 `activation_mode` 并非完全无验证

子代理曾报告 `activation_mode` 无验证脚本。复核发现该说法不准确。

证据：

- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py:171`
- `skills/ship-orchestrator/scripts/validate_ui_artifacts.py:37`

现状：

- B/D 若 `ship-shape.status` 非 skipped，validator 会要求 `activation_mode=uiux_material_gate_insert`。
- `design-brief.md` 若 `activation_mode=uiux_material_gate_insert`，validator 会要求 UIUX gate sign-off。

仍需修的是 transition checker 对“已插入 shape”的前置阶段检查。

### 6.2 `generation_mode` 并非完全缺失

子代理曾报告 `generation_mode` 模板缺失。复核发现该说法不准确。

证据：

- `skills/ship-orchestrator/scripts/validate_workflow_docs.py:76`
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py:951`

现状：

runtime 会根据场景设置 `generation_mode`，文档一致性脚本也检查模板中存在相关字段。

仍需修的是：PRD Direct 修订、B/D 插入 `ship-shape` 后回流时，`generation_mode` 是否保持或切换的规则需更明确。

## 7. 建议修复顺序

建议按以下顺序推进：

1. 修复 `stage_transition_check.py` 对 B/D inserted `ship-shape` 的前置检查。
2. 补充 `ship-define-review` 中 D + `backend_only` 的契约级材料检查项。
3. 重写 `ship-orchestrator` 场景 E 启动确认摘要，明确执行顺序。
4. 补充 UIUX Material Gate 的材料有效性标准。
5. 补充 B/D 插入 `ship-shape` 后回流 `ship-define` 的 normalize 顺序。
6. 明确 C 场景 impact scan 与 Project Reality Scan 的职责边界。
7. 为 `project_scope` 冻结增加脚本级保护或至少文档化 frozen scope 字段。
8. 明确 E 场景 derived `requirements.md` index 的 AC 最低完整度。

## 8. 复查清单

本次审计已覆盖：

- [x] `skills/README.md` 的入口与阶段总览。
- [x] `ship-orchestrator/SKILL.md` 的场景识别、scope、route、gate、delegation、resume 协议。
- [x] A/B/C/D/E 五个入口场景的子代理逐项追踪。
- [x] `workflow_stage_map.py` canonical stage 与 macro stage 映射。
- [x] `stage_transition_check.py` 阶段推进检查。
- [x] `feature_meta_runtime.py` 场景初始化、UIUX gate 插入、technical plan source、evolve source 支持。
- [x] `validate_feature_artifacts.py`、`validate_ui_artifacts.py`、`validate_tech_discovery.py` 的关键校验逻辑。
- [x] 子代理报告中的误报复核。

未执行：

- [ ] 修改工作流文档或脚本。
- [ ] 运行完整测试套件。

原因：本轮任务目标是生成审计文档，不做源文件修复。
