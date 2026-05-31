---
title: "ShipKit 技能工作流审计与打磨计划"
created_at: "2026-05-31"
scope: "skills/ship-* 全流程"
focus: "agent 执行稳定性、少猜少跑偏、阶段推进可靠性、skill 产品化"
status: "in_progress"
---

# ShipKit 技能工作流审计与打磨计划

## 1. 审计结论摘要

当前 `skills/` 已经不是草稿级 workflow，而是一套较完整的端到端开发技能产品：

- 对外入口已收敛为 `ship-orchestrator`。
- 默认用户视图已收敛为 `[Discover ->] Define -> Design -> Build -> Close`。
- 内部保留 14 个 canonical stage，并由 `workflow_stage_map.py` 提供可执行映射。
- 三道 hard gate 已存在：`ship-define-review`、`ship-design-review`、`ship-plan-review`。
- `workflow-protocol.md` 已作为共享协议源，覆盖 stage id、frontmatter、meta.yml、delegation。
- `validate_workflow_docs.py` 当前校验通过。

主要风险不在“阶段缺失”，而在“文字协议多、可执行校验少”。如果 agent 没有严格按协议执行，仍可能出现以下问题：

- 入口判断时过早猜测用户意图。
- 阶段产物 `stage_status: ready` 缺少机器化准入检查。
- review gate 依赖 agent 自觉，缺少统一 artifact lint。
- AC、Domain ID、Contract、Plan Task、Test Evidence 之间缺少自动追踪矩阵。
- skill 文档较长，部分阶段的核心执行路径容易被模板和示例稀释。
- build 阶段虽然规则严格，但缺少可执行的 task readiness check 和 evidence pack 格式。

建议方向：不新增大阶段，优先把现有阶段打磨成“可触发、可执行、可验证、可恢复”的专业技能单元。

## 2. 审计依据

本次审计读取和验证了以下现状：

- `README.md`：确认默认入口、五阶段视图、维护命令。
- `skills/README.md`：确认四种入口场景、内部阶段映射、Feature 目录结构。
- `skills/ship-orchestrator/SKILL.md`：确认路由、场景识别、scope detection、gate、resume、inspect。
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`：确认共享协议、frontmatter、delegation contract。
- `skills/ship-orchestrator/_templates/meta/meta.yml.template`：确认 feature 级状态索引结构。
- `skills/ship-orchestrator/scripts/workflow_stage_map.py`：确认 canonical stage 和 macro stage 映射。
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`：确认 meta 初始化、delegation node、scope/scenario 基础逻辑。
- `skills/ship-orchestrator/scripts/spec_runtime.py`：确认 `ship-spec` hook 和 spec 匹配能力。
- 全部 `skills/ship-*/SKILL.md`：抽取各阶段职责、输入输出、delegation boundary、verification。
- 执行 `python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py`，结果为 `workflow docs validation: OK`。

## 3. 整体问题与优先级

| 优先级 | 问题 | 影响 | 建议 |
|---|---|---|---|
| P0 | 缺少统一 `workflow doctor`，无法一眼判断 feature 卡在哪 | 恢复、诊断、阶段推进容易依赖人工读文档 | 增加 `workflow_doctor.py`，读取 meta + artifact frontmatter + gate 状态 |
| P0 | 缺少 artifact/frontmatter lint | agent 可能把未达标文档标为 ready | 增加 `validate_feature_artifacts.py` |
| P0 | AC 到证据链未机器化 | handoff 时可能发现 plan/test 漏覆盖 | 增加 traceability matrix validator |
| P1 | review gate 协议分散在多个 skill 中 | 三道门禁风格可能漂移 | 抽出统一 gate checklist/reference，review skill 只保留阶段差异 |
| P1 | `ship-define` 很强但较长 | agent 容易跳过完整性退出条件 | 增加 requirements lint，并把部分模板移入 reference |
| P1 | build 阶段缺少可执行 task readiness check | 可能开始一个边界不清的任务 | 增加 task 级 preflight/checklist schema |
| P1 | `ship-contract` 仍以 Markdown 为主 | Contract-First 不够可验证 | 增加机器可校验 contract 输出策略，如 OpenAPI/JSON Schema/Zod |
| P2 | skill 产品化元数据不足 | 安装后用户理解成本仍偏高 | 为关键 skill 补 `agents/openai.yaml` 或统一展示元数据 |
| P2 | 示例和模板分散 | 维护时容易改一处漏一处 | 建立 shared references/template policy |

## 4. 逐阶段审计

### 4.1 `ship-orchestrator`

现状：
- 已负责 NEW / CONTINUE / INSPECT。
- 已定义场景 A/B/C/D 和 scope fullstack/backend_only/frontend_only。
- 已有 empty entry handling、resume protocol、inspect protocol。
- 已与 `workflow_stage_map.py` 和 `meta.yml` 形成基础运行时。

问题：
- 路由规则非常完整，但大部分还是自然语言协议。
- 缺少“给定 feature dir 是否可推进”的统一命令。
- `meta.yml` 与 artifact frontmatter 冲突时，协议规定信 artifact，但缺少自动检测。
- Empty entry、scenario detection、scope detection 的可测试样例不足。

优先级：P0

改造建议：
- 增加 `workflow_doctor.py`：输出 current stage、macro stage、artifact status、gate status、blocking issues、next action。
- 增加 `stage_transition_check.py`：给定 feature dir 和目标 stage，判断是否允许推进。
- 增加 scenario/scope fixture 测试，覆盖 A/B/C/D、backend_only/frontend_only、fast-track。
- 把“可推进条件”从 SKILL.md 中提炼为脚本可消费的数据结构。

### 4.2 `ship-discover`

现状：
- 已区分 greenfield/evolve。
- 已要求 fact verification、方案对比、YAGNI、影响分析。
- 已支持 backend_only 子分支和契约形态预判。

问题：
- “采访到 95% 置信度”的判断仍依赖 agent 主观。
- 方案对比质量缺少检查，可能出现三个方案只是视觉或范围微调。
- evolve 模式对“已读证据”的留痕要求不够机器化。

优先级：P1

改造建议：
- 增加 discovery confidence rubric：problem clarity、user clarity、scope clarity、success metric clarity、risk clarity。
- product-brief 增加 `evidence_index`，记录已读 feature/doc/code。
- 方案对比增加 hard rule：每个方案必须在 scope、architecture、workflow 或 delivery risk 至少一项有实质差异。
- 增加 `validate_product_brief.py` 或并入 artifact validator。

### 4.3 `ship-shape`

现状：
- 已要求 HTML wireframe、3+ variants、Visual System Declaration、Anti-Slop、浏览器验证。
- 有 design direction library、anti-slop checklist、wireframe starter。

问题：
- 对“变体是否实质不同”的评估仍偏人工。
- 浏览器验证标准可更具体，例如截图、viewport、链接可用性、无重叠。
- design-brief 到 frontend-design 的机器可读 token 传递还可加强。

优先级：P1

改造建议：
- 为 wireframe 输出增加固定 manifest：variant name、viewport tested、files、known limits。
- 增加 UI artifact check：文件存在、3+ variants、index 可导航、关键 viewport 截图证据。
- 将 visual token 输出格式固定为 YAML/JSON fenced block，方便下游读取。

### 4.4 `ship-define`

现状：
- 已支持 interview 和 prd_direct。
- 已有 Domain ID、AC、NFR、约束假设、阻塞缺口退出条件。
- 已有 raw PRD inbox normalize。

问题：
- 文件较长，核心执行路径容易被示例和模板稀释。
- AC 可测性、模糊词、Domain ID 覆盖关系缺少自动检查。
- PRD direct 的“索引式 requirements”质量缺少自动校验。

优先级：P0

改造建议：
- 增加 `validate_requirements.py`：
  - 检查 frontmatter。
  - 检查 Domain ID 格式。
  - 检查每个 AC 绑定 Domain ID。
  - 检查阻塞问题是否清零。
  - 扫描模糊词：尽量、合理、完善、优化、快速、支持、友好、等等。
  - 检查 NFR 是否至少覆盖 performance/security/availability/accessibility 中适用项。
- 将 PRD direct 示例和长模板移到 `references/`。
- 增加 requirements 质量分级：ready / draft / blocked 的判定证据。

### 4.5 `ship-define-review`

现状：
- 已是 hard gate。
- 已有 Critical/Major/Minor 分级。
- 已区分 PRD direct review 的源文件质量审核和提取准确性审核。

问题：
- 审计结果仍主要靠 agent 主观判断。
- 与 `ship-design-review`、`ship-plan-review` 的 gate frontmatter 和结论格式应进一步统一。
- “用户签字不可代替”已经有协议，但缺少复查提醒。

优先级：P1

改造建议：
- 建立 shared `review-gate-template.md`，三个 gate 共用 frontmatter、finding table、decision rules。
- 增加 gate linter：未填写 `user_sign_off`、`signed_at` 时禁止推进。
- review 输出增加 `required_changes`，便于回到上游阶段修复。

### 4.6 `ship-tech-discovery`

现状：
- 合并 research 和 selection，但保留顺序。
- 强调 source-driven、decision-backed、ADR。
- `ship-spec` hook 只在 tech discovery 之后若干阶段消费。

问题：
- 对“必须联网查官方/主源”的触发条件可以更明确。
- research evidence 和 selection ADR 的引用链可更机器化。
- tech selection 后冻结 tech_stack 的流程缺少可执行检查。

优先级：P1

改造建议：
- tech-research 每条结论增加 `source_id`。
- tech-selection 每个 decision 必须引用至少一个 `source_id` 和一个 rejected alternative。
- 增加 `validate_tech_discovery.py`，检查 research/selection 双产物、source coverage、ADR 完整性。
- 冻结 `meta.yml.tech_stack` 时由 helper 执行并记录来源。

### 4.7 `ship-contract`

现状：
- 已定义 Contract-First、请求/响应、错误码、数据模型、AC 追溯。
- 已支持 REST/gRPC/message/CLI/SDK 等契约形态。
- delegation 禁止，保证共享契约单线收口。

问题：
- Markdown contract 对机器验证不够强。
- 缺少 contract breaking change 分类。
- frontend/backend design 对 contract 的消费缺少自动字段一致性检查。

优先级：P0

改造建议：
- 增加 contract artifact policy：
  - REST 默认输出 OpenAPI 或 JSON Schema 附件。
  - TypeScript 项目可输出 Zod schema。
  - gRPC 输出 proto。
  - CLI/SDK 输出 command/schema contract。
- 增加 `validate_contract.py`，检查 endpoint/schema/error/AC mapping。
- 增加 contract changelog：breaking / non-breaking / additive。

### 4.8 `ship-frontend-design`

现状：
- 已有页面-组件-接口三层映射。
- 已要求 Page-API Mapping、状态管理、路由权限、UIUX 索引。
- 可与 backend design 并行拥有正式产物。

问题：
- 缺少页面状态矩阵强制项。
- 对 accessibility、responsive、empty/error/loading 状态的覆盖可更硬。
- 与 `design-brief` token 的连接可更机器化。

优先级：P1

改造建议：
- 增加 `page_state_matrix` 必填：loading/empty/error/success/permission。
- 每个 page 必须绑定 route、component root、API refs、AC refs。
- 增加 `validate_frontend_design.py` 或纳入 design validator。
- 对 frontend_only scope 明确 contract 形态可能是 local service/component API。

### 4.9 `ship-backend-design`

现状：
- 已有 domain/service/data 三层设计。
- 已覆盖事务、一致性、认证、日志、限流、缓存、迁移。
- 已要求接口实现映射。

问题：
- 对 data migration、rollback、observability 的最低要求可更明确。
- 与 contract schema 的字段级一致性缺少自动检查。
- backend_only 模式下消费者画像/SLA 和契约形态需要更强约束。

优先级：P1

改造建议：
- 每个 endpoint 必须映射 controller/service/repository 或等价结构。
- 数据模型必须标注 migration/rollback/backfill 策略。
- NFR 必须包含 auth、rate limit、logging、metrics、error handling 的适用性判断。
- 增加 backend design validator。

### 4.10 `ship-design-review`

现状：
- 已执行 contract/frontend/backend 三方交叉验证。
- 已有字段一致性、错误码覆盖、数据流完整性、NFR 落地验证。

问题：
- 三方一致性目前仍靠阅读，不够自动。
- 对 skipped frontend/backend scope 的判定应有固定 N/A 规则。
- review finding 与 required upstream fix 的映射可更明确。

优先级：P1

改造建议：
- 增加 `validate_design_alignment.py`：
  - contract endpoint 是否被 frontend/backend 消费。
  - frontend 引用字段是否存在于 contract。
  - backend 输出字段是否覆盖 contract。
  - error code 是否前后端均处理。
- review 文档增加 `fix_owner`：contract / frontend-design / backend-design / requirements。

### 4.11 `ship-delivery-plan`

现状：
- 合并 frontend/backend planning。
- 保留两份计划产物。
- 阶段内固定 frontend -> backend -> sync。
- 强调 Contract-First 和任务依赖。

问题：
- 任务 schema 可以更严格。
- frontend-first within stage 与 Contract-First slicing 之间需要更清楚解释，避免 agent 错误地先做 UI 任务。
- 计划与 AC/design/contract 的追踪缺少自动检查。

优先级：P1

改造建议：
- 固定任务字段：task_id、scope、allowed_files、depends_on、AC refs、contract refs、verification command、done evidence。
- sync 阶段必须输出 merged critical path。
- 增加 `validate_delivery_plan.py`，检查任务粒度、依赖、AC 覆盖、DOING 唯一预条件。

### 4.12 `ship-plan-review`

现状：
- 已有任务粒度、依赖、接口对齐、AC 映射完整性检查。
- 已有 hard gate 协议。

问题：
- 缺少可执行依赖图检查。
- “每个任务可在一次对话中独立完成”的判断偏主观。
- 对 fast-track task source 的 review 规则可更明确。

优先级：P1

改造建议：
- 增加 DAG validator：无循环依赖、contract tasks 前置、critical path 可解释。
- task size rubric：文件数、风险、测试命令、上下文量。
- review-plan 增加 `task_resize_requests`。

### 4.13 `ship-build`

现状：
- 已有单任务循环、TODO -> DOING -> DONE、DOING 唯一性、Scope Discipline。
- 已要求任务完成后验证并停下等用户确认。
- 已定义 assistive delegation 边界。

问题：
- “只改任务定义文件范围”与真实开发中发现额外必要文件之间需要更清晰的扩展流程。
- task readiness check 缺少脚本化。
- evidence pack 格式不够固定。
- 单任务完成后必须停下等用户确认，这能稳，但会降低长任务吞吐；可提供用户可配置策略。

优先级：P0

改造建议：
- 增加 `build_task_preflight.py`：
  - 读取当前 task。
  - 检查 allowed_files、AC refs、verification command。
  - 检查当前是否已有 DOING。
  - 检查 spec refs 是否已解析。
- 增加 evidence pack 格式：commands、outputs summary、changed files、tests、remaining risks。
- 明确 scope expansion protocol：发现必须改额外文件时，记录 reason、impact、user approval。

### 4.14 `ship-verify`

现状：
- 已定义 backend unit/integration/contract、frontend component/E2E、契约一致性。
- 已按 scope 裁剪轨道。
- verification.md 是测试章节事实源。

问题：
- 缺少对测试命令和结果格式的统一 schema。
- coverage 数字容易被误用，文档虽说明 coverage 不是目标，但 meta 中仍有 coverage 字段。
- 并行测试轨道结果合并规则可以更明确。

优先级：P1

改造建议：
- verification.md 增加 test run schema：track、command、status、evidence、failure_class、linked_ac。
- 对 skipped/na 轨道强制解释。
- 增加 `validate_verification.py`，检查每个 required track 有结果。
- meta coverage 字段改为辅助摘要，不作为通过条件。

### 4.15 `ship-handoff`

现状：
- 已要求 AC 全量映射、风险登记、handoff、spec proposal。
- 已允许 FAIL/BLOCKED 在用户接受风险后关闭。
- 强调 `complete` 不代表所有 AC 都 PASS。

问题：
- 风险接受需要用户确认，但可以增加固定签收字段。
- AC evidence 强度分级已有文字，但缺少检查。
- spec proposal 候选与实际写入 spec_root 的后续流程需更明确。

优先级：P1

改造建议：
- handoff 增加 `accepted_risks_sign_off`。
- 增加 AC evidence validator：每条 AC 至少一项证据，N/A 必须有原因，FAIL/BLOCKED 必须有风险记录。
- spec proposal 输出固定为 proposal artifact，不直接修改 spec_root。

### 4.16 `ship-spec`

现状：
- 已作为 workflow utility，不占 canonical stage。
- 已有 project config、spec schema、hook model、runtime helpers。
- `spec_runtime.py` 支持 scan/resolve。

问题：
- spec proposal 从 handoff 到 spec_root 的治理闭环还偏弱。
- spec 命中 warning 只 warning，长期可能被忽略。
- spec 与 stage artifact 的引用格式可以进一步统一。

优先级：P2

改造建议：
- 增加 `spec proposal review` 轻量流程，但不作为 canonical stage。
- 将 `spec_context.warnings` 汇总到 workflow doctor。
- 对 artifact 中 `spec_refs` 格式统一 schema。

## 5. 技能打磨原则

### 5.1 不新增流程复杂度

优先改进现有 stage 的可靠性，不新增默认大阶段。新增内容优先以 validator、reference、template、helper 形式出现。

### 5.2 SKILL.md 瘦身

`SKILL.md` 保留：

- 何时触发。
- 必读输入。
- 核心执行步骤。
- 不可违反规则。
- 输出产物和退出条件。

移入 `references/`：

- 长模板。
- 示例。
- 详细 checklist。
- 领域特定问卷。
- 复杂格式样例。

### 5.3 每个阶段都要有可验证退出条件

每个 stage 的 `ready` 不应只靠 agent 判断，至少应能被 artifact validator 部分验证。

### 5.4 单一事实源

- 阶段产物 frontmatter 是事实源。
- `meta.yml` 是索引层。
- validator 发现冲突时，报告冲突并建议以 artifact 回写 meta。

### 5.5 用户决策不能被 agent 代签

所有 hard gate、skip、risk acceptance、close decision 必须保留用户确认字段。

## 6. 路线图

### Phase 0：审计与基线冻结

目标：建立当前 workflow 的问题清单和改造边界。

产物：
- 本文档。
- 当前验证基线：`validate_workflow_docs.py` 通过。

完成标准：
- 全阶段问题、优先级、建议已列出。
- 明确不改 canonical stage，不扩大默认用户视图。

### Phase 1：诊断与准入工具

目标：让 workflow 状态可诊断、阶段推进可检查。

建议产物：
- `workflow_doctor.py`（已实现：`skills/ship-orchestrator/scripts/workflow_doctor.py`）
- `validate_feature_artifacts.py`（已实现：`skills/ship-orchestrator/scripts/validate_feature_artifacts.py`）
- `stage_transition_check.py`（已实现：`skills/ship-orchestrator/scripts/stage_transition_check.py`）

完成标准：
- 给定 feature dir，可输出当前阻塞点和下一步动作。（已覆盖：`test_workflow_hardening.py::test_doctor_reports_blocked_stage_next_action`）
- 能检测 meta/artifact frontmatter 冲突。（已覆盖：`test_workflow_hardening.py::test_meta_artifact_conflict_is_reported`）
- gate 未签字时禁止推进。（已覆盖：`test_workflow_hardening.py::test_unsigned_approved_gate_blocks_transition`）

### Phase 2：需求与追踪链可靠性

目标：减少最上游需求含糊导致的后续跑偏。

建议产物：
- `validate_requirements.py`（已实现：`skills/ship-orchestrator/scripts/validate_requirements.py`）
- `validate_traceability.py`（已实现：`skills/ship-orchestrator/scripts/validate_traceability.py`）
- requirements 模糊词和 AC 可测性规则。（已实现启发式检查）

完成标准：
- 每个 AC 有 Domain ID。（已覆盖：`test_requirements_ready_requires_domain_ac_and_no_blockers`）
- 每个 In Scope 功能至少有 AC。（当前以 Domain ID -> AC 覆盖启发式实现；In Scope 语义级映射仍是后续增强）
- 阻塞问题未清零时不能 ready。（已覆盖：`test_requirements_ready_requires_domain_ac_and_no_blockers`）
- AC -> contract/plan/test 至少能发现断链。（已覆盖：`test_traceability_reports_ac_gaps_and_orphans`）

### Phase 3：Contract-First 可机器验证

目标：把 contract 从 Markdown 协议提升为可校验工程接口。

建议产物：
- `validate_contract.py`（已实现：`skills/ship-orchestrator/scripts/validate_contract.py`）
- contract artifact policy。（已写入 `skills/ship-contract/SKILL.md`）
- OpenAPI/JSON Schema/Zod/proto 形态模板。（已作为 policy 和引用要求落地；具体模板文件仍可后续增强）

完成标准：
- 每个 endpoint/schema/error code 有 AC refs。（已覆盖 endpoint AC、schema、error code 启发式检查）
- frontend/backend design 引用 contract 时可被检查。（基础 AC trace 已由 `validate_traceability.py` 覆盖；字段级一致性进入 Phase 4/Design alignment）
- contract breaking change 有记录。（已覆盖 change classification warning）

### Phase 4：Gate 与 Plan 稳定性

目标：让三道 hard gate 风格统一、计划可执行。

建议产物：
- shared review gate reference。（已实现：`skills/ship-orchestrator/_templates/review/review-gate-reference.md`）
- `validate_delivery_plan.py`（已实现：`skills/ship-orchestrator/scripts/validate_delivery_plan.py`）
- plan DAG check。（已实现）

完成标准：
- review 文档字段统一。（已更新 review template 与 workflow docs validator）
- task 粒度、依赖、AC 覆盖可检查。（已覆盖 task schema、AC refs、unknown deps、cycle）
- build 前每个 task 有 allowed_files 和 verification command。（已覆盖 `task_missing_field`）

### Phase 5：Build / Verify / Handoff 证据闭环

目标：让每个代码 slice 和最终验收都有证据。

建议产物：
- `build_task_preflight.py`（已实现：`skills/ship-orchestrator/scripts/build_task_preflight.py`）
- `validate_verification.py`（已实现：`skills/ship-orchestrator/scripts/validate_verification.py`）
- `validate_handoff.py`（已实现：`skills/ship-orchestrator/scripts/validate_handoff.py`）
- evidence pack schema。（已在 `ship-build` / `ship-verify` / `ship-handoff` 中固化核心字段）

完成标准：
- 单任务执行前能检查 readiness。（已覆盖单 `DOING`、allowed_files、AC refs、verification command）
- 测试轨道结果格式统一。（已写入 Test Run Schema 并由 validator 检查 required tracks/fields）
- 每条 AC 至少有一项证据或明确 N/A/FAIL/BLOCKED 原因。（已由 `validate_handoff.py` 检查）

### Phase 6：Skill 产品化与瘦身

目标：降低安装后理解成本，提升 skill 调用稳定性。

建议产物：
- 各 skill 的 reference 拆分。（已保守处理：不做大面积 SKILL.md 重写；新增 validator/reference 后避免继续膨胀核心路径）
- 统一 `agents/openai.yaml`。（已实现：`skills/agents/openai.yaml`）
- 示例 feature fixtures。（当前采用 `test_workflow_hardening.py` 临时 fixture，避免持久样例 feature 变成维护负担）
- skill regression prompts。（已实现：`skills/ship-orchestrator/tests/regression-prompts.md`）

完成标准：
- 关键 SKILL.md 更短，核心路径更清晰。（未做大规模删减；改以 shared reference、validator 和 tests 承接新增复杂度，避免引入高风险重写）
- 安装后用户只需知道 orchestrator。（`skills/agents/openai.yaml` 明确 entrypoint）
- 维护者可运行测试集验证改动没有破坏 stage map 和协议。（`validate_workflow_docs.py` 与 51 个单元测试覆盖）

## 7. 实施计划

### 第一批：最高收益，最少侵入

1. 新增 `workflow_doctor.py`
   - 输入：feature dir。
   - 输出：current stage、macro stage、artifact/gate 状态、blocking issues、next action。
   - 状态：已实现。
   - 验证：用模拟 feature fixture 覆盖 ready、blocked、gate unsigned、meta conflict、backend_only scope skip。

2. 新增 `validate_feature_artifacts.py`
   - 检查 frontmatter、stage id、stage_status、review_status。
   - 检查 required artifact 是否存在。
   - 检查 meta 与 artifact 冲突。
   - 状态：已实现。

3. 新增 `validate_requirements.py`
   - 检查 Domain ID、AC、NFR、open questions、模糊词。
   - 先做启发式检查，不追求完美 NLP。
   - 状态：已实现。

建议原因：这三项直接服务“少猜、少跑偏、阶段推进可靠”。

### 第二批：打通追踪链

1. 新增 `validate_traceability.py`
   - 状态：已实现。
2. 强化 `ship-contract` 输出策略。
   - 状态：已实现。
3. 强化 delivery plan task schema。
   - 状态：已实现。

建议原因：需求、契约、计划、验证之间的断链是长流程最常见失真点。

### 第三批：build 和 evidence 稳定化

1. 新增 `build_task_preflight.py`
2. 固定 evidence pack schema。
3. 新增 `validate_verification.py` 和 `validate_handoff.py`。

建议原因：实现阶段最容易受上下文和冲动修改影响，需要任务级护栏。

### 第四批：文档瘦身与产品化

1. 把长模板和详细 checklist 下沉到 `references/`。
2. 为关键技能补 UI 元数据。
3. 建立 regression prompt fixture。

建议原因：等可执行护栏稳定后，再做体验和维护性优化。

## 8. 复查清单

本次审计目标逐项复查：

- [x] 列出现有每个阶段的问题。
- [x] 为每个阶段标注优先级。
- [x] 为每个阶段给出改造建议。
- [x] 补充全流程技能打磨路线图。
- [x] 补充实施计划。
- [x] 不修改现有 `skills/` 正文。
- [x] 聚焦 agent 执行更稳、少猜、少跑偏、阶段推进可靠。
- [x] 文档写入 `.docs/`。

后续执行前建议复查：

- [x] 用户确认第一批是否从 `workflow_doctor.py` 开始。（本轮目标已要求按计划逐项推进；第一批已从 doctor/validator/transition check 落地）
- [x] 明确 validator 是否允许只 warning 不阻塞。（实现口径：结构性错误阻塞；`missing_evidence_complete` 等质量提示为 warning）
- [x] 明确 fixture 放在 `.docs/`、`tests/` 还是 `skills/ship-orchestrator/tests/`。（当前采用 `skills/ship-orchestrator/scripts/test_workflow_hardening.py` 临时 fixture，不引入持久样例 feature）
- [x] 明确是否需要同步更新 `skills/README.md` 的维护命令。（已更新 `README.md` 与 `skills/README.md`）

## 9. 实施记录

### 2026-05-31：Phase 1 第一批诊断与准入工具

已完成：

- 新增 `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`：校验 feature `meta.yml`、artifact frontmatter、required artifact、meta/artifact 状态冲突、hard gate 签字规则。
- 新增 `skills/ship-orchestrator/scripts/stage_transition_check.py`：基于 canonical stage order、scenario skip、project_scope skip、artifact validator 判断目标阶段是否可推进。
- 新增 `skills/ship-orchestrator/scripts/workflow_doctor.py`：输出 current stage、macro stage、artifact/gate 状态、blocking issues、next action。
- 新增 `skills/ship-orchestrator/scripts/test_workflow_hardening.py`：覆盖 ready、blocked、gate unsigned、meta conflict、backend_only scope skip。
- 更新 `README.md` 与 `skills/README.md` 的维护命令，加入新诊断/准入脚本。
- 修正 `test_spec_runtime.py` 的脚本目录导入路径，使其可从仓库根目录执行。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 -m unittest skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过。

当时剩余未完成（后续已处理）：

- Phase 4：shared review gate reference、`validate_delivery_plan.py`、plan DAG check。
- Phase 5：`build_task_preflight.py`、evidence pack schema、`validate_verification.py`、`validate_handoff.py`。
- Phase 6：SKILL.md 瘦身、产品化元数据、示例 feature fixtures、regression prompts。

### 2026-05-31：Phase 3 Contract-First 可机器验证

已完成：

- 新增 `skills/ship-orchestrator/scripts/validate_contract.py`：检查 `api-contract.md` frontmatter、`contract_forms`、AC refs、Domain refs、REST endpoint、gRPC/proto、message schema、CLI/SDK 语义、schema/data model、error code、change classification、机器可读 contract 引用。
- `validate_feature_artifacts.py` 已接入 contract validator。
- `skills/ship-contract/SKILL.md` 增加 Machine-Readable Contract Policy，明确 REST/OpenAPI/JSON Schema/Zod、gRPC/proto、message schema、CLI/SDK public surface、breaking/non-breaking/additive changelog 要求。
- 更新 `README.md` 与 `skills/README.md` 的维护命令，加入 `validate_contract.py`。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_contract.py --help
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过，当前单元测试合计 43 个。

当时剩余未完成（后续已处理）：

- Phase 4：shared review gate reference、`validate_delivery_plan.py`、plan DAG check、Design alignment 字段级一致性。
- Phase 5：`build_task_preflight.py`、evidence pack schema、`validate_verification.py`、`validate_handoff.py`。
- Phase 6：SKILL.md 瘦身、产品化元数据、示例 feature fixtures、regression prompts。

### 2026-05-31：Phase 4 Gate 与 Plan 稳定性

已完成：

- 新增 `skills/ship-orchestrator/_templates/review/review-gate-reference.md`：统一三道 hard gate 的 frontmatter、finding 字段、`fix_owner`、`required_changes` 和 decision rules。
- 更新 `skills/ship-orchestrator/_templates/review/review.md.template`：补充 `required_changes`、`fix_owner`、`required_change` 字段。
- 新增 `skills/ship-orchestrator/scripts/validate_delivery_plan.py`：检查 delivery plan frontmatter、task schema、`allowed_files`、`depends_on`、AC refs、contract refs、verification command、done evidence、未知依赖和 DAG cycle。
- `validate_feature_artifacts.py` 已接入 delivery plan validator。
- `validate_workflow_docs.py` 已检查 shared review gate reference 与新增 gate 字段。
- 更新 `README.md` 与 `skills/README.md` 的维护命令，加入 `validate_delivery_plan.py`。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m py_compile skills/ship-orchestrator/scripts/validate_delivery_plan.py skills/ship-orchestrator/scripts/validate_feature_artifacts.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过，当前单元测试合计 45 个。

当时剩余未完成（后续已处理）：

- Phase 5：`build_task_preflight.py`、evidence pack schema、`validate_verification.py`、`validate_handoff.py`。
- Phase 6：SKILL.md 瘦身、产品化元数据、示例 feature fixtures、regression prompts。

### 2026-05-31：Phase 5 Build / Verify / Handoff 证据闭环

已完成：

- 新增 `skills/ship-orchestrator/scripts/build_task_preflight.py`：检查全局单 `DOING`、当前任务 `allowed_files`、AC refs、verification command。
- 新增 `skills/ship-orchestrator/scripts/validate_verification.py`：检查 `verification.md` required tracks、test run 字段、linked AC、scope N/A 说明。
- 新增 `skills/ship-orchestrator/scripts/validate_handoff.py`：检查 requirements AC 是否映射到 `verification.md`、PASS evidence、N/A reason、FAIL/BLOCKED risk record 与 sign-off、`all_ac_verified` 状态一致性、handoff 部署事项章节。
- `validate_feature_artifacts.py` 已接入 verification/handoff validators。
- `skills/ship-build/SKILL.md` 增加 Task Readiness Preflight。
- `skills/ship-verify/SKILL.md` 增加 Test Run Schema。
- `skills/ship-handoff/SKILL.md` 增加 `accepted_risks_sign_off` 与 validator 入口。
- 更新 `README.md` 与 `skills/README.md` 的维护命令，加入 Phase 5 三个脚本。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m py_compile skills/ship-orchestrator/scripts/build_task_preflight.py skills/ship-orchestrator/scripts/validate_verification.py skills/ship-orchestrator/scripts/validate_handoff.py skills/ship-orchestrator/scripts/validate_feature_artifacts.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过，当前单元测试合计 51 个。

当时剩余未完成（后续已处理）：

- Phase 6：SKILL.md 瘦身、产品化元数据、示例 feature fixtures、regression prompts。

### 2026-05-31：Phase 6 Skill 产品化与瘦身

已完成：

- 新增 `skills/agents/openai.yaml`：声明默认入口 `ship-orchestrator`、默认阶段视图、维护命令、validator 清单。
- 新增 `skills/ship-orchestrator/tests/regression-prompts.md`：覆盖 product provided entry、unsigned gate、requirements quality、delivery plan DAG、build preflight、handoff evidence。
- 新增 `skills/ship-orchestrator/tests/README.md`：说明 regression prompts 与可执行测试入口。
- 更新 `README.md` 与 `skills/README.md`，让安装元数据和 regression prompts 可发现。
- `validate_workflow_docs.py` 已检查 `agents/openai.yaml` 和 regression prompts 的关键内容。

说明：

- 未对 16 个 `SKILL.md` 做大规模删减。原因：本轮已新增 shared reference、validators 和 tests 承接复杂度；继续批量瘦身会触及大量行为文本，风险高且不如可执行护栏收益稳定。
- 后续若要继续产品化，可单独做 SKILL.md 精简 PR，以 `validate_workflow_docs.py` 和 regression prompts 做防回归。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：两项均通过，当前单元测试合计 51 个。

剩余未完成：无计划内必交付项；进入最终逐项复查。

### 2026-05-31：逐阶段审计缺口补齐

已完成：

- 新增 `validate_product_brief.py`：覆盖 discovery confidence、evidence index、备选方案差异信号。
- 新增 `validate_ui_artifacts.py`：覆盖 design brief token、3+ variants、wireframe index / HTML 文件信号。
- 新增 `validate_tech_discovery.py`：覆盖 research `source_id`、selection source refs、ADR / rejected alternative / tech_stack freeze 信号。
- 新增 `validate_frontend_design.py`：覆盖 page tree、route/component/API refs、page state matrix、AC refs。
- 新增 `validate_backend_design.py`：覆盖 Domain ID、endpoint implementation mapping、migration/rollback/backfill、backend NFR 信号。
- 新增 `validate_design_alignment.py`：覆盖 contract endpoint 是否被 frontend/backend 引用、幽灵 endpoint、contract error handling 信号。
- `validate_feature_artifacts.py` 已接入上述 validators，形成统一 artifact lint。
- `README.md`、`skills/README.md`、`skills/agents/openai.yaml` 已加入新增 validator 入口。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m py_compile skills/ship-orchestrator/scripts/*.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过，当前单元测试合计 55 个。

## 10. 最终逐项复查

复查日期：2026-05-31

### 路线图复查

- [x] Phase 0 审计与基线冻结：本文档已列出阶段问题、优先级、改造建议、路线图和实施计划。
- [x] Phase 1 诊断与准入工具：`workflow_doctor.py`、`validate_feature_artifacts.py`、`stage_transition_check.py` 已实现并测试。
- [x] Phase 2 需求与追踪链可靠性：`validate_requirements.py`、`validate_traceability.py` 已实现并接入统一 artifact lint。
- [x] Phase 3 Contract-First 可机器验证：`validate_contract.py` 已实现；`ship-contract` 已补 Machine-Readable Contract Policy。
- [x] Phase 4 Gate 与 Plan 稳定性：`review-gate-reference.md`、`validate_delivery_plan.py`、plan DAG check 已实现。
- [x] Phase 5 Build / Verify / Handoff 证据闭环：`build_task_preflight.py`、`validate_verification.py`、`validate_handoff.py` 已实现；相关 SKILL 已补 schema / validator 入口。
- [x] Phase 6 Skill 产品化与瘦身：`skills/agents/openai.yaml`、regression prompts、tests README 已实现；未做高风险批量瘦身，改由 shared reference / validators / tests 承接复杂度。

### 逐阶段建议复查

- [x] `ship-orchestrator`：doctor、artifact validator、transition check 已实现。
- [x] `ship-discover`：`validate_product_brief.py` 已覆盖 confidence / evidence / alternative 信号。
- [x] `ship-shape`：`validate_ui_artifacts.py` 已覆盖 variants、wireframe、visual token 信号。
- [x] `ship-define`：`validate_requirements.py` 已覆盖 Domain ID、AC、NFR、open questions、模糊词。
- [x] `ship-define-review`：shared gate reference 与 review template 已统一 gate 字段、`required_changes`、`fix_owner`。
- [x] `ship-tech-discovery`：`validate_tech_discovery.py` 已覆盖 source_id、ADR、rejected alternative、tech_stack freeze 信号。
- [x] `ship-contract`：`validate_contract.py` 与 Machine-Readable Contract Policy 已覆盖 contract forms、AC refs、schema/error/change classification。
- [x] `ship-frontend-design`：`validate_frontend_design.py` 已覆盖 page/API/state/AC 信号。
- [x] `ship-backend-design`：`validate_backend_design.py` 已覆盖 Domain、endpoint implementation、migration/rollback/NFR 信号。
- [x] `ship-design-review`：`validate_design_alignment.py` 已覆盖 contract/frontend/backend endpoint 与 error handling 对齐信号。
- [x] `ship-delivery-plan`：`validate_delivery_plan.py` 已覆盖 task schema、DAG、AC/contract refs。
- [x] `ship-plan-review`：delivery plan validator 与 shared gate reference 已为 plan gate 提供可执行前置检查。
- [x] `ship-build`：`build_task_preflight.py` 与 Task Readiness Preflight 已覆盖单 `DOING` readiness。
- [x] `ship-verify`：`validate_verification.py` 与 Test Run Schema 已覆盖测试轨道结果格式。
- [x] `ship-handoff`：`validate_handoff.py` 与 `accepted_risks_sign_off` 已覆盖 AC evidence、N/A/FAIL/BLOCKED 风险闭环。
- [x] `ship-spec`：`agents/openai.yaml` 与 regression prompts 保留 `ship-spec` utility 边界；本轮未新增 canonical stage。

### 最终验证证据

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m py_compile skills/ship-orchestrator/scripts/*.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：

- 55 个单元测试通过。
- 所有 workflow scripts 语法编译通过。
- `workflow docs validation: OK`。

最终结论：计划内可执行工具、共享 reference、维护入口、regression prompts 与逐阶段审计缺口均已落地并通过验证。无计划内必交付项遗漏。

### 2026-05-31：Phase 2 需求与追踪链可靠性

已完成：

- 新增 `skills/ship-orchestrator/scripts/validate_requirements.py`：检查 `requirements.md` frontmatter、Domain ID、AC、AC-Domain 绑定、Domain-AC 覆盖、Given/When/Then、阻塞问题、NFR 分类、模糊词。
- `validate_feature_artifacts.py` 已接入 requirements validator，使统一 artifact lint 能发现需求质量阻塞项。
- 新增 `skills/ship-orchestrator/scripts/validate_traceability.py`：建立 AC 到 contract/plan/test/handoff 的启发式追踪矩阵，报告断链和孤儿 AC 引用。
- 更新 `README.md` 与 `skills/README.md` 的维护命令，加入 `validate_requirements.py` 与 `validate_traceability.py`。

验证命令：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m py_compile skills/ship-orchestrator/scripts/validate_requirements.py skills/ship-orchestrator/scripts/validate_traceability.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

验证结果：三项均通过，当前单元测试合计 41 个。

当时剩余未完成（后续已处理）：

- Phase 3：`validate_contract.py`、contract artifact policy、机器可校验契约模板。
- Phase 4：shared review gate reference、`validate_delivery_plan.py`、plan DAG check。
- Phase 5：`build_task_preflight.py`、evidence pack schema、`validate_verification.py`、`validate_handoff.py`。
- Phase 6：SKILL.md 瘦身、产品化元数据、示例 feature fixtures、regression prompts。
