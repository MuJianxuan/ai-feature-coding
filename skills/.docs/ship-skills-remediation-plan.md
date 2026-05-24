# ship-* skills 修复批次计划

更新时间：2026-05-24

本文不是执行许可。它只描述在用户确认 `.docs/ship-skills-confirmation.md` 后，建议如何分批修复 `.docs/ship-skills-audit.md` 中 A-001 至 A-040 的问题。

实际用户决策以 `.docs/ship-skills-decision-log.md` 为准。

## 成功标准

修复完成后应满足：

- 5 个 macro stages 与 14 个 canonical stages 在 README、protocol、orchestrator、runtime、validator 中一致。
- scenario、scope、fast-track、lightweight flow、spec hook、handoff ownership、delegation、stage advancement 都有单一事实源和可验证落点。
- 单侧 scope 不引用不存在的侧向文档、测试轨或 plan。
- `ship-build` / `ship-verify` 的任务事实源统一。
- validator 和 unit tests 能覆盖本次发现的关键不变量，而不是只检查旧文案。

## 批次 0: 用户确认

依赖：无。

等待用户确认：

- C-001 至 C-011 是否按推荐方案执行。
- 若有分歧，按 C 编号记录替代决策。

不应在本批次修改：

- `SKILL.md`
- `workflow-protocol.md`
- runtime helper
- tests

## 批次 1: 共享协议与顶层口径

依赖：C-001, C-002, C-003, C-004, C-006, C-008, C-009。

目标文件：

- `../README.md`
- `README.md`
- `ship-orchestrator/SKILL.md`
- `ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `ship-orchestrator/_templates/README.md`
- `ship-orchestrator/_templates/meta/meta.yml.template`
- `ship-orchestrator/_templates/review/review.md.template`

覆盖问题：

- A-001, A-002, A-005, A-006, A-008
- A-009, A-020, A-023, A-024, A-025, A-027
- A-032, A-034, A-035

验收检查：

- 旧口径搜索不再命中语义文件：`4 大阶段|4 个大阶段|12 个 canonical|12 阶段`
- protocol 中明确定义：
  - 5 macro stages
  - 14 canonical stages
  - scenario 初始化规则
  - scope contract
  - fast-track/lightweight task source
  - `skip_log`
  - `lifecycle_status`
  - verify/handoff ownership 和 `complete` 语义

## 批次 2: runtime schema 与 helper 行为

依赖：C-001, C-002, C-003, C-006, C-007, C-010, C-011。

目标文件：

- `ship-orchestrator/scripts/workflow_stage_map.py`
- `ship-orchestrator/scripts/feature_meta_runtime.py`
- `ship-orchestrator/scripts/spec_runtime.py`
- `ship-orchestrator/scripts/test_spec_runtime.py`

覆盖问题：

- A-003, A-009, A-011, A-016, A-017, A-023, A-024, A-037, A-038

建议顺序：

1. `feature_meta_runtime.py init --scenario`：按 scenario 初始化 `current_stage`、skipped stages、`generation_mode`。
2. scope 初始化：`backend_only` 设置 `ship-delivery-plan.current_part = backend`。
3. delegation registry：补 `ship-discover` / `ship-shape`。
4. `skip_log` / `lifecycle_status` schema 与 helper。
5. `record-spec-proposal` 收紧到 `ship-handoff`。
6. `spec_runtime.py` path 输出稳定化。
7. stage advancement 最小 helper。
8. scope-aware macro summary 或 refresh 行为。

验收检查：

- unit tests 覆盖 4 种 scenario、3 种 scope、spec proposal 限制、自定义 spec root、delegation node、stage advancement。
- `/Users/rao/.pyenv/shims/python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'` 通过。

## 批次 3: scope-aware 阶段文档

依赖：C-003, C-005, C-008, C-009。

目标文件：

- `ship-contract/SKILL.md`
- `ship-contract/references/api-contract-template.md`
- `ship-frontend-design/SKILL.md`
- `ship-backend-design/SKILL.md`
- `ship-design-review/SKILL.md`
- `ship-delivery-plan/SKILL.md`
- `ship-plan-review/SKILL.md`
- `ship-build/SKILL.md`
- `ship-verify/SKILL.md`
- `ship-handoff/SKILL.md`

覆盖问题：

- A-004, A-012, A-013, A-014, A-018, A-019, A-020, A-021, A-022, A-028, A-029, A-030, A-033, A-036, A-040

建议顺序：

1. 先改 `ship-contract` 语义：API contract -> interaction boundary contract；Page -> consumer/entrypoint。
2. 再改设计阶段：frontend/backend/design-review 的 scope-aware checklist 与 reviewed documents。
3. 再改计划阶段：delivery-plan/plan-review 的单侧流程、checklist、frontmatter 示例。
4. 再改 build/verify：任务事实源从 `plan.md` 改为 scope-aware task source；正式编码全局单 `DOING`。
5. 最后改 handoff/verify：frontmatter、verification mode、测试命令证据落点。

验收检查：

- `rg -n "plan.md" ship-build/SKILL.md ship-verify/SKILL.md` 不再命中误导性事实源。
- `rg -n "frontend-plan.md \\+ backend-plan.md|reviewed_documents: \\[\"frontend-plan.md\", \"backend-plan.md\"\\]" ship-plan-review/SKILL.md` 只出现在 fullstack 示例或明确条件中。
- `rg -n "前端页面" ship-contract ship-frontend-design ship-design-review` 不再作为 backend_only 阻塞要求。

## 批次 4: fast-track / lightweight flow

依赖：C-004, C-005, C-006, C-009。

目标文件：

- `ship-orchestrator/SKILL.md`
- `ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `ship-define/SKILL.md`
- `ship-define-review/SKILL.md`
- `ship-build/SKILL.md`
- `ship-verify/SKILL.md`
- `ship-handoff/SKILL.md`

覆盖问题：

- A-010, A-031, A-034

建议顺序：

1. 定义 `pipeline_mode=fast-track` 的 lightweight task source 位置和字段。
2. 定义 `change_type` 与 lightweight flow 的最小产物。
3. 把“直接进入实现 / 无需本阶段”改成受控跳过：必须记录 `skip_log` 和替代事实源。
4. 文档/配置类变更进入 `ship-verify` 的 manual/docs mode，不直接绕过到 handoff。

验收检查：

- fast-track 最小路径可以合法进入 build。
- build/verify/handoff 都知道 fast-track 的任务、验证和验收证据来自哪里。

## 批次 5: 低风险一致性与维护体验

依赖：C-011。

目标文件：

- `README.md`
- `../README.md`
- `ship-spec/SKILL.md`
- `ship-shape/SKILL.md`
- `ship-shape/references/wireframe-starter/index.html`
- `ship-shape/references/wireframe-starter/variant-template.html`
- Python dependency manifest or README maintenance section

覆盖问题：

- A-007, A-015, A-026, A-039

验收检查：

- helper 命令在声明的工作目录下可运行。
- Python 依赖说明明确包含 PyYAML。
- wireframe starter 与 SRI 策略一致。
- AC / Domain ID 示例一致。

## 批次 6: validator 扩展与完成审计

依赖：批次 1 至 5 完成。

目标文件：

- `ship-orchestrator/scripts/validate_workflow_docs.py`
- `ship-orchestrator/scripts/test_spec_runtime.py`
- `.docs/ship-skills-traceability.md`

覆盖问题：

- A-005 及所有需要 runtime/validator 防回归的问题。

建议新增 validator：

- macro stage wording：要求 5-stage，禁止旧 4-stage 口径。
- canonical stage wording：禁止 12-stage 旧口径。
- delegation registry 双向一致。
- scope-aware stage 文档检查。
- no stale `plan.md` task source in build/verify。
- meta template 字段检查：`skip_log`、`lifecycle_status`、scenario generation mode。

完成审计：

- 全部验证命令通过。
- `.docs/ship-skills-audit.md` 中每个 A 项都标注已修复或已按用户决策保留。
- `.docs/ship-skills-confirmation.md` 中每个 C 项都有用户确认记录或最终采用方案。
- 不再存在需要用户确认但未确认的语义冲突。
