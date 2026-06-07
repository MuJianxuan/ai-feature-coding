# skills/ 工作流全链路修复方案

> 基于：`.docs/skills-workflow-audit.md`  
> 交付类型：方案文档，不直接修改 `skills/` 源文件  
> 粒度：文件级修复步骤  
> 范围：覆盖审计 P0/P1，并扩展为 workflow 全链路加固（文档、runtime、transition、validator、测试、回归提示）

## 1. 修复目标

### 1.1 必须闭环的问题

1. B/D 场景经 `UIUX Material Gate` 插入 `ship-shape` 后，transition checker 必须把 `ship-shape` 当作真实前置阶段检查。
2. D + `backend_only` 的契约级材料要求必须进入 `ship-define-review` hard gate，不只停留在 orchestrator 启动提示。
3. E 场景启动摘要必须按实际执行顺序表达：先 `ship-tech-discovery`，contract 前确认 selected scope AC，design-review 后才能 delivery-plan。
4. UIUX Material Gate 必须定义“已有材料是否足够”的判断标准。
5. B/D 插入 `ship-shape` 后回流 `ship-define` 的 normalize 顺序必须明确。
6. C 场景 evolve impact scan 与 `ship-tech-discovery` Project Reality Scan 必须明确职责边界。
7. `project_scope` 在 `ship-design-review` approved 后必须有脚本级冻结保护。
8. E 场景 derived `requirements.md` index 的最低 AC 完整度必须明确并可校验。

### 1.2 全链路加固目标

- 将路由不变量集中到 transition/validator，而不是只写在 stage 文档。
- 将 scenario × scope × stage 的条件分支转化为可测试规则。
- 将 `meta.yml` 作为索引、artifact frontmatter 作为事实源的规则，在脚本中统一执行。
- 给新增规则补齐单元测试和人工 regression prompts。
- 避免引入新阶段或改变宏流程；保持 `[Discover →] Define → Design → Build → Close` 不变。

## 2. 当前证据摘要

- `skills/ship-orchestrator/SKILL.md:102` 已定义 B/D 的 UIUX Gate 插入规则，但 `skills/ship-orchestrator/scripts/stage_transition_check.py:93` 对 `product_provided`、`prd_direct` 无条件移除 `ship-shape`。
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py:857` 已有 `insert_shape_from_uiux_gate()`，会写入 `activation_mode: uiux_material_gate_insert` 与 gate sign-off。
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py:171` 已校验 B/D 非 skipped 的 `ship-shape` 必须来自 UIUX gate，但该校验不能替代 transition 的前置阶段检查。
- `skills/ship-orchestrator/SKILL.md:146` 已要求 D + `backend_only` 需要契约级材料，但 `skills/ship-define-review/SKILL.md:185` 的 PRD Direct Phase 1 未包含该检查项。
- `skills/ship-tech-discovery/SKILL.md:49` 已要求 E 场景派生最小 requirements index；`skills/ship-delivery-plan/SKILL.md:122` 要求 task 追溯到 AC ID、selected scope 和仓库证据，但最低 AC 完整度仍需脚本化。
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py` 已是合适的 workflow 回归测试承载点。

## 3. 修复原则

1. **先脚本不变量，后文档解释**：凡会导致错误推进的规则，必须进入 `stage_transition_check.py` 或 validator。
2. **保留事实源分层**：artifact frontmatter 优先，`meta.yml` 用于索引与恢复；冲突时 validator 报错或要求回写。
3. **不扩大流程阶段**：不新增 canonical stage，只补条件分支和校验。
4. **默认阻塞高风险不确定性**：涉及 hard gate、scope freeze、selected scope、UIUX gate 的缺口都应阻塞推进。
5. **测试覆盖每个 scenario × scope 关键边界**：尤其是 B/D/E/C 和单侧 scope。

## 4. 分阶段修复计划

### Phase 0：建立测试基线

#### 目标

在改逻辑前确认现有测试状态，避免后续无法区分新旧问题。

#### 涉及文件

- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/scripts/test_spec_runtime.py`
- `skills/ship-orchestrator/tests/README.md`

#### 操作步骤

1. 运行现有单元测试：
   ```bash
   python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
   ```
2. 若已有失败，记录到 `.docs/skills-workflow-fix-baseline.md`，不在本修复中顺手改无关失败。
3. 在 `tests/README.md` 增加本次修复的测试矩阵入口说明，后续所有新增测试都归入 workflow hardening。

#### 验收标准

- 有清晰 baseline：通过或明确记录已知失败。
- 新增测试前后可对比。

## 5. P0 修复项

### P0-1：修复 B/D inserted `ship-shape` transition 绕过

#### 涉及文件

- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/SKILL.md`

#### 修改步骤

1. 在 `stage_transition_check.py` 增加 helper：
   - `_is_stage_skipped(meta, stage)`：只在 `stages.<stage>.status == skipped` 时允许从前置阶段列表中移除。
   - `_is_inserted_shape_required(meta)`：当 `scenario in product_provided/prd_direct` 且 `ship-shape.status != skipped` 时返回 true。
2. 修改 `_required_previous_stages()`：
   - 对 `product_provided` / `prd_direct`，仍移除 `ship-discover`。
   - 只有 `ship-shape.status == skipped` 时才移除 `ship-shape`。
   - 若 `ship-shape.status` 是 `pending/in_progress/ready/completed`，保留 `ship-shape` 为前置阶段。
3. 保持 `technical_plan_provided` 对 `ship-discover`、`ship-shape`、`ship-define`、`ship-define-review` 的跳过逻辑，但改成“按 meta skipped 状态 + scenario 禁止规则”双保险。
4. 在 `validate_feature_artifacts.py` 保留现有 `_validate_ship_shape_meta()`，补充错误信息：B/D inserted shape 必须由 transition 检查 `design-brief.md.stage_status`。
5. 在 `ship-orchestrator/SKILL.md` 的 UIUX Gate 规则后补一句：插入 `ship-shape` 后，`ship-shape` 不再视为 skipped，所有后续 transition 必须等待 `design-brief.md.stage_status=ready`。
6. 在 `test_workflow_hardening.py` 增加用例：
   - B 场景 `ship-shape.status=pending`、无 `design-brief.md`，进入 `ship-define` 或 `ship-define-review` 应被阻塞。
   - D 场景 `ship-shape.status=ready` 且 `design-brief.md.stage_status=ready`，允许继续检查后续 define 条件。
   - B/D `ship-shape.status=skipped` 时不要求 `design-brief.md`。

#### 验收标准

- `check_transition(..., "ship-define")` 或后续 stage 的 `checked_previous_stages` 在 inserted shape 情况下包含 `ship-shape`。
- 缺少 ready `design-brief.md` 时返回 `allowed=false` 和 `missing_stage_artifact` 或 `stage_not_ready`。
- skipped shape 不产生误报。

### P0-2：D + `backend_only` 契约级材料进入 hard gate

#### 涉及文件

- `skills/ship-define-review/SKILL.md`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/scripts/validate_requirements.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- 可选：`skills/ship-orchestrator/templates/` 中 requirements/review 模板（若存在对应模板）

#### 修改步骤

1. 在 `ship-define-review/SKILL.md` 的 PRD Direct Phase 1 表格新增检查项：
   - `P1-6 backend_only contract material`
   - 适用条件：`generation_mode=prd_direct` 且 `meta.yml.project_scope=backend_only`
   - 通过标准：源材料存在并可引用 OpenAPI / endpoint list / interface doc / design doc / message protocol / CLI spec / SDK contract 至少一种契约级材料。
   - 不通过标准：只有产品 PRD、无接口/消息/CLI/SDK 契约信息。
   - 失败级别：Critical，禁止 approved。
2. 在 `ship-orchestrator/SKILL.md:146` 附近补清楚：该材料类型确认会在 `ship-define-review` hard gate 复核，不是启动提示的一次性提醒。
3. 在 `validate_requirements.py` 增加轻量启发式检查：
   - 当 `generation_mode=prd_direct` 且 frontmatter 或 body 标记 `project_scope: backend_only` / meta 联动可读取时，ready requirements 必须出现契约材料索引信号。
   - 可接受关键词：`OpenAPI`、`endpoint`、`接口文档`、`API spec`、`message protocol`、`消息协议`、`CLI spec`、`SDK`、`request/response`。
   - 如果 `validate_requirements.py` 不方便读取 meta，则在 `validate_feature_artifacts.py` 中对 `meta.project_scope` + requirements frontmatter/body 做组合校验。
4. 在 `test_workflow_hardening.py` 增加用例：
   - D + backend_only + prd_direct + 无契约材料索引 → validator error。
   - D + backend_only + OpenAPI/source index → validator pass。
   - D + frontend_only 不触发 backend contract material 检查。

#### 验收标准

- `ship-define-review` 文档可指导人工 gate 检查。
- validator 对 D + backend_only 的明显缺失能报错。
- hard gate 不能在缺少契约级材料时 approved 并推进。

### P0-3：重写 E 场景启动确认摘要

#### 涉及文件

- `skills/ship-orchestrator/SKILL.md`
- `skills/README.md`
- `skills/ship-orchestrator/tests/regression-prompts.md`

#### 修改步骤

1. 将 `ship-orchestrator/SKILL.md:159` 的长句拆成有序 bullets：
   - 技术方案来源与 selected scope。
   - 未选中内容按 `ignored_source_policy: out_of_scope` 忽略。
   - 跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate。
   - 直接进入 `ship-tech-discovery`，并执行 repository scan。
   - `ship-tech-discovery` 开头派生最小 `requirements.md` index。
   - 进入 `ship-contract` 前必须完成 `selected_scope_ac_confirmation`。
   - 完成 contract 和按 scope 裁剪的 frontend/backend design。
   - 进入 `ship-delivery-plan` 前必须通过 `ship-design-review`。
2. 在 `skills/README.md` 的 E 场景入口摘要同步同样顺序，避免 README 和 orchestrator 不一致。
3. 在 `regression-prompts.md` 增加 E 场景人工检查 prompt，要求启动摘要必须按上述顺序出现。

#### 验收标准

- 用户看到的 E 场景启动确认不会误以为 `design-review` 在 `delivery-plan` 之后，或 `selected_scope_ac_confirmation` 在 contract 之后。
- README 与 orchestrator 表述一致。

## 6. P1 修复项

### P1-1：明确 UIUX Material Gate 材料有效性标准

#### 涉及文件

- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-shape/SKILL.md`
- `skills/ship-define/SKILL.md`
- `skills/ship-orchestrator/scripts/validate_ui_artifacts.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

#### 修改步骤

1. 在 `ship-orchestrator/SKILL.md` 新增 `UIUX Material Gate Coverage` 小节，定义四级判定：
   - `sufficient`：材料可访问，覆盖 Must Have 主流程、关键页面/状态、核心异常路径，可直接供 define 提取。
   - `partial`：可访问但只覆盖部分页面或缺少异常/状态；允许继续，但必须在 requirements/design 中记录 UIUX risk/open question。
   - `screenshot_only`：只有截图；允许继续的前提是截图覆盖主流程，否则视为 partial，并记录无法确认交互细节。
   - `inaccessible`：链接打不开、权限不足、文件损坏；视为缺材料，用户需补材料或授权 `ship-shape`。
2. 在 `ship-shape/SKILL.md` 的 When NOT to Use 中把“已提供材料”改为“已提供 sufficient UIUX materials”。
3. 在 `ship-define/SKILL.md` 的材料读取流程中增加：读取 `design-brief.md`、Figma/截图/原型时，必须记录材料覆盖级别与风险，不得把 partial 当成完整设计稿。
4. 在 `validate_ui_artifacts.py` 增加可选 frontmatter 字段检查：
   - `uiux_material_coverage: sufficient|partial|screenshot_only|inaccessible|generated`
   - ready `design-brief.md` 若 coverage 为 `partial/screenshot_only`，必须有 `uiux_risks` 或 `open_questions`。
5. 在 regression prompts 中增加“Figma 链接不可访问”“只有两张截图”“完整原型”三类入口提示。

#### 验收标准

- B/D 不会因“有一个链接”就误判为 UIUX 材料充分。
- partial/screenshot-only 可以继续，但风险必须显式进入后续文档。

### P1-2：明确 B/D inserted shape 回流 define 的 normalize 顺序

#### 涉及文件

- `skills/ship-define/SKILL.md`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

#### 修改步骤

1. 在 `ship-define/SKILL.md` 的 raw inbox normalize 章节新增 B/D inserted shape 回流流程：
   1. 先读取 `requirements.md` frontmatter，若是 raw inbox，必须 normalize。
   2. 再读取 `resource/README.md` 和所有 source documents。
   3. 再读取 `design-brief.md` 与 `resource/wireframes/`。
   4. 将 `design-brief.md` 作为 UIUX source，不覆盖 PRD source；两者冲突时记录 conflict/open question。
   5. 输出结构化 `requirements.md`，保持 `generation_mode`：B 为 `interview`，D 为 `prd_direct`，不得因为经过 `ship-shape` 切换成 technical_plan。
2. 在 `ship-orchestrator/SKILL.md` 的 UIUX Gate 插入规则后补“回流 define normalize 顺序”。
3. 在 `validate_feature_artifacts.py` 加强 raw inbox 检查：若 current stage 已超过 `ship-define`，raw inbox 一律 error；现有 `raw_inbox_past_define` 已具备基础，可补测试覆盖 inserted shape 回流。
4. 在 regression prompts 增加 B/D “先创建目录后补 PRD，再授权生成线框”的人工回归场景。

#### 验收标准

- 回流 define 后不会跳过 raw PRD normalize。
- `generation_mode` 保持场景语义。
- `design-brief.md` 与 PRD/source index 的关系清晰可追溯。

### P1-3：明确 C evolve impact scan 与 Project Reality Scan 边界

#### 涉及文件

- `skills/ship-discover/SKILL.md`
- `skills/ship-tech-discovery/SKILL.md`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

#### 修改步骤

1. 在 `ship-discover/SKILL.md` 的 evolve 分支中明确产出职责：
   - 产品层变更目标。
   - 旧功能/现有行为基线。
   - 用户影响范围假设。
   - 初步 out-of-scope。
   - 待技术验证项。
2. 在 `ship-tech-discovery/SKILL.md:153` 附近补强：Discover 的 impact scan 只是线索，Tech Discovery 必须用代码路径、文档路径、命令输出或用户确认重新取证。
3. 在 `ship-orchestrator/SKILL.md` 的 C 场景说明中加入一句：C 与 E 的区别是 C 从“变更意图/旧功能基线”出发，E 从“已有技术方案 selected scope”出发。
4. 在 `validate_feature_artifacts.py` 已有 `_validate_evolve_product_brief()` 基础上补充检查：
   - evolve 的 `product-brief.md` ready 时，必须能回指 `meta.yml.evolve_source`。
   - 如果 product-brief 中有“待技术验证项”章节，不能替代 `tech-research.md` 的 evidence。
5. 在 regression prompts 增加“用户只说优化现有功能但没指定基线”的阻塞场景。

#### 验收标准

- C 场景不会把 product discovery 的假设当技术事实。
- 未提供 evolve baseline 时仍阻塞，不创建 feature 目录或不推进。

### P1-4：增加 `project_scope` 冻结脚本级保护

#### 涉及文件

- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- 可选：`skills/ship-design-review/SKILL.md`

#### 修改步骤

1. 在 `meta.yml` 约定新增字段：
   ```yaml
   scope_freeze:
     status: unfrozen|frozen|reopened
     frozen_scope: ""
     frozen_at: ""
     frozen_by_gate: ship-design-review
     user_sign_off: ""
     reopen_reason: ""
   ```
2. 在 `feature_meta_runtime.py` 新增 helper：
   - `freeze_project_scope_after_design_review(data, user_sign_off, signed_at)`：当 `ship-design-review` approved 时写入 frozen scope。
   - `validate_scope_change_allowed(data, new_scope)`：design-review approved 后若 `new_scope != frozen_scope`，必须报错，除非显式 reopen。
3. 在 `validate_feature_artifacts.py` 增加校验：
   - `ship-design-review` approved 且 `scope_freeze.status` 为空时 warning 或 error（建议 error，避免冻结规则形同虚设）。
   - `scope_freeze.status=frozen` 时，`project_scope` 必须等于 `frozen_scope`。
   - frozen 后若存在 scope-forbidden artifact 冲突，保持现有 error。
4. 在 `stage_transition_check.py` 增加保护：
   - target stage 在 `ship-delivery-plan` 及之后时，必须满足 scope freeze。
   - 若 `project_scope` 与 frozen scope 不一致，阻塞。
5. 在 `ship-orchestrator/SKILL.md:131` 附近补充“冻结写入与 reopen 规则”：
   - scope 变更只允许在 design-review approved 前。
   - approved 后如确需变更，必须回退/reopen `ship-design-review`，重新跑受影响的 contract/design/plan。
6. 在 `test_workflow_hardening.py` 增加用例：
   - design-review approved 后无 `scope_freeze` → 阻塞进入 delivery-plan。
   - frozen fullstack 后改成 backend_only → validator error。
   - frozen scope 一致 → 不报错。

#### 验收标准

- `project_scope` 不会在设计评审后静默漂移。
- 下游 plan/build 不会基于与 design-review 不一致的 scope 执行。

### P1-5：明确 E derived requirements index 的 AC 最低完整度

#### 涉及文件

- `skills/ship-tech-discovery/SKILL.md`
- `skills/ship-delivery-plan/SKILL.md`
- `skills/ship-orchestrator/scripts/validate_requirements.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/scripts/validate_delivery_plan.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`

#### 修改步骤

1. 在 `ship-tech-discovery/SKILL.md` 的 technical_plan_provided 裁剪规则中定义最低完整度：
   - 每个 selected scope item 至少映射一个 Domain ID。
   - 每个可执行任务必须可回指至少一个 AC ID。
   - 每个 AC 必须包含：可验证结果、source locator、scope boundary、必要 NFR 或明确不适用。
   - Out-of-scope 必须列出未选中内容的处理政策。
2. 在 `validate_requirements.py` 对 `generation_mode=technical_plan` ready 状态增加检查：
   - selected_scope/source_documents 非空。
   - `selected_scope_ac_confirmed=true`。
   - body 中 AC 行必须包含 selected scope/source locator 信号，例如 `source:`、`来源:`、`selected scope:`、文件路径或章节锚点。
   - AC 行必须引用 Domain ID（已有 `ac_missing_domain_ref`）。
3. 在 `validate_feature_artifacts.py` 的 `_validate_technical_plan_meta()` 中加强：
   - `tech-discovery.status in ready/completed` 前，`repository_scan_status` 必须 ready。
   - confirmed AC IDs 必须覆盖 requirements body 中全部 AC IDs（已有基础逻辑），同时要求 body AC IDs 非空。
4. 在 `validate_delivery_plan.py` 增加 E 场景任务校验：
   - 每个 task 必须有 `ac_refs`、`scope`、`allowed_files`、`verification_command`。
   - 每个 task 必须出现 selected scope/source reference 或 technical source reference。
   - 不允许任务引用未确认 AC ID。
5. 在 `test_workflow_hardening.py` 增加用例：
   - E derived requirements ready 但 AC 无 source locator → error。
   - E selected_scope_ac_confirmation 缺少某个 AC → error。
   - E delivery task 无 selected scope/source ref → error。

#### 验收标准

- E 场景不会把一份空洞的 index 当成完整 requirements。
- delivery-plan 的每个 task 都能从 selected scope → AC → repository evidence 追溯。

## 7. 全链路加固项

### 7.1 集中化 workflow 不变量模块

#### 涉及文件

- 新增：`skills/ship-orchestrator/scripts/workflow_invariants.py`
- 修改：`stage_transition_check.py`
- 修改：`validate_feature_artifacts.py`
- 修改：`workflow_doctor.py`
- 修改：`test_workflow_hardening.py`

#### 修改步骤

1. 新建 `workflow_invariants.py`，集中定义：
   - scenario 是否允许某 stage active。
   - scope 是否允许某 artifact 存在。
   - B/D inserted shape 判定。
   - E technical plan required fields。
   - scope freeze required condition。
2. `stage_transition_check.py` 和 `validate_feature_artifacts.py` 复用同一组 helper，减少规则漂移。
3. `workflow_doctor.py` 使用同一 helper 输出 next_action，避免 doctor 建议与 transition 不一致。
4. 单元测试覆盖 helper 本身，以及 transition/validator 调用结果。

#### 验收标准

- 同一个规则不再散落在三处以不同条件实现。
- 新增 scenario/scope 规则时有单一修改入口。

### 7.2 加强 artifact frontmatter 与 meta 回写一致性

#### 涉及文件

- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/SKILL.md`

#### 修改步骤

1. 梳理每个 stage 的事实字段：
   - status 类字段以 artifact frontmatter 为准。
   - `meta.yml.stages.*` 是索引。
   - gate approved 以 review artifact 的 `review_status/user_sign_off/signed_at` 为准。
2. 在 validator 中对以下冲突给 error：
   - `meta.status=ready` 但 artifact `stage_status=draft`。
   - `meta.review.approved=true` 但 review artifact 未签名。
   - `meta.current_stage` 已超过某 stage，但该 stage artifact 缺失且未 skipped。
3. 在 runtime 中提供 `sync_meta_from_artifacts(feature_dir)`，作为修复建议或 doctor action，不强制自动改。
4. Orchestrator 文档补充：冲突时先读取 artifact，确认后回写 meta。

#### 验收标准

- 恢复/继续工作流时不会只凭 stale meta 推进。
- doctor 能提示“同步 meta”而不是误导进入下一阶段。

### 7.3 完整 scenario × scope × stage 测试矩阵

#### 涉及文件

- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`
- `skills/ship-orchestrator/tests/README.md`

#### 建议矩阵

| 场景 | scope | 关键断言 |
|---|---|---|
| A | fullstack | discover + shape 默认路径，shape ready 后 define |
| A | backend_only | shape skipped，frontend-design skipped |
| B | fullstack | shape skipped 时可走 define；inserted shape 时必须 ready |
| B | frontend_only | contract 保留，backend-design skipped |
| B | backend_only | shape/frontend-design skipped |
| C | fullstack | evolve_source 必须存在，tech-discovery 不信任 discover 假设 |
| D | fullstack | prd_direct 必须经过 define-review |
| D | backend_only | 契约级材料必需 |
| E | fullstack | skip define/review，但 requirements index + AC confirmation + repo scan 必需 |
| E | frontend_only/backend_only | design/plan 按 scope 裁剪，未选中内容不得生成任务 |

#### 验收标准

- 每个矩阵行至少一个自动测试或 regression prompt。
- P0/P1 每个问题至少一个失败前可复现、修复后通过的测试。

### 7.4 增加 preflight 命令组合

#### 涉及文件

- `skills/ship-orchestrator/tests/README.md`
- 可选：新增 `skills/ship-orchestrator/scripts/run_workflow_checks.py`

#### 修改步骤

1. 在 README 增加推荐命令：
   ```bash
   python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
   ```
2. 若常用 feature fixtures 已存在，补充：
   ```bash
   python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
   python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-contract --json
   ```
3. 可选新增 `run_workflow_checks.py`，统一运行 validators、transition 和 tests。

#### 验收标准

- 修改 workflow 后有一条清晰命令能跑核心回归。
- 人工 regression prompt 与自动测试入口都能被发现。

## 8. 建议实施顺序

1. **测试基线**：先运行现有 unittest，记录初始状态。
2. **P0-1 transition**：修复 inserted shape 绕过，因为它直接影响错误推进。
3. **P0-2 hard gate**：补 D + backend_only 契约级材料 gate 与 validator。
4. **P0-3 文案顺序**：修 E 启动摘要，低风险但影响用户理解。
5. **P1-4 scope freeze**：先做冻结字段与 validator，再接入 transition。
6. **P1-5 E derived AC**：补 requirements / delivery-plan 校验。
7. **P1-1/P1-2/P1-3 文档边界**：补 UIUX gate、normalize、C/E 边界，并加 regression prompts。
8. **全链路 invariant 抽取**：在规则稳定后再抽公共 helper，避免过早抽象。

## 9. 风险与回滚策略

### 风险 1：validator 过严导致旧 feature 大量报错

- 缓解：新增规则先区分 `error` 与 `warning`。
- 建议：对安全推进相关规则使用 error；对历史缺字段使用 warning，并在进入下游 transition 时提升为 error。

### 风险 2：scope freeze 字段引入后旧 meta 缺字段

- 缓解：仅当 `ship-design-review` 已 approved 且 target stage 在 `ship-delivery-plan` 之后时强制要求。
- 回滚：可暂时降级为 warning，但不建议长期保持。

### 风险 3：E derived AC source locator 启发式误判

- 缓解：先采用明确格式要求，例如 AC 行或邻近 bullet 必须出现 `source:` / `来源:` / `selected_scope:`。
- 回滚：保留人工 review 提示，但 transition 到 contract 前仍检查 AC confirmation。

### 风险 4：workflow_invariants 抽取造成导入循环

- 缓解：新模块只放纯函数和常量，不导入 validators。
- 回滚：先在单文件内 helper 实现，测试稳定后再抽取。

## 10. 验证清单

### 自动验证

- `python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py`
- 针对 fixture 手动运行：
  - `python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json`
  - `python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-contract --json`
  - `python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-delivery-plan --json`

### 人工回归

- B 场景：有 PRD、无 UIUX，用户授权生成线框，确认 transition 不跳过 `ship-shape`。
- D + backend_only：完整产品 PRD 但无 API spec，确认 define-review 阻塞。
- E 场景：用户提供技术方案 selected section，确认启动摘要顺序正确，且 contract 前要求 selected scope AC confirmation。
- C 场景：用户说“优化旧功能”但不提供 feature/code baseline，确认阻塞询问基线。
- frozen scope：design-review approved 后尝试从 fullstack 改 backend_only，确认 validator/transition 阻塞。

## 11. Definition of Done

本轮修复完成必须同时满足：

- P0/P1 八个问题均有文档规则、脚本校验或 regression prompt 覆盖。
- `stage_transition_check.py` 不再无条件跳过 B/D inserted `ship-shape`。
- `ship-define-review` 明确检查 D + `backend_only` 契约级材料。
- E 场景启动摘要与实际 stage 顺序一致。
- `project_scope` 在 design-review approved 后有 frozen scope 保护。
- E derived requirements index 与 delivery tasks 可追溯到 selected scope、AC ID 和仓库证据。
- 核心 unittest 通过，或仅存在已记录且与本修复无关的历史失败。

## 12. 后续可选优化

- 为 `meta.yml` 定义 JSON Schema 或 YAML schema，减少字段漂移。
- 将 scenario/scope 初始化 fixtures 固化到 `tests/fixtures/`，让新增测试更少依赖手写 YAML。
- 给 `workflow_doctor.py` 增加 `--fix-suggestions` 输出，提示应调用哪个 runtime helper 修复 stale meta。
- 为 regression prompts 建立人工结果记录模板，便于后续审计比对。
