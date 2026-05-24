# ship-* skills 审计追踪矩阵

更新时间：2026-05-24

本文用于追踪 `.docs/ship-skills-audit.md` 与 `.docs/ship-skills-confirmation.md` 的覆盖关系，避免后续修复时遗漏 skill、reference、runtime helper 或验证命令。

修复批次与依赖顺序见 `.docs/ship-skills-remediation-plan.md`。

当前目标完成度审计见 `.docs/ship-skills-completion-audit.md`。

## 文件覆盖矩阵

| 文件 | 覆盖状态 | 主要关联问题 |
|------|----------|--------------|
| `../README.md` | 已审计 | A-001, A-002, A-005, A-039 |
| `README.md` | 已审计 | A-001, A-002, A-005, A-039 |
| `ship-orchestrator/SKILL.md` | 已审计 | A-001, A-002, A-009, A-012, A-023, A-024, A-025, A-038 |
| `ship-orchestrator/_templates/protocol/workflow-protocol.md` | 已审计 | A-001, A-003, A-004, A-010, A-013, A-014, A-016, A-023, A-032, A-034, A-038 |
| `ship-orchestrator/_templates/meta/meta.yml.template` | 已审计 | A-011, A-015, A-023, A-024, A-027 |
| `ship-orchestrator/_templates/review/review.md.template` | 已审计 | A-006 |
| `ship-orchestrator/_templates/README.md` | 已审计 | A-001, A-006 |
| `ship-orchestrator/scripts/workflow_stage_map.py` | 已审计 | A-001, A-002, A-037 |
| `ship-orchestrator/scripts/feature_meta_runtime.py` | 已审计 | A-003, A-009, A-011, A-016, A-023, A-024, A-038 |
| `ship-orchestrator/scripts/spec_runtime.py` | 已审计 | A-017 |
| `ship-orchestrator/scripts/validate_workflow_docs.py` | 已审计 | A-003, A-005, A-007, A-014 |
| `ship-orchestrator/scripts/test_spec_runtime.py` | 已审计 | A-007, A-009, A-011, A-016, A-017, A-038 |
| `ship-discover/SKILL.md` | 已审计 | A-003, A-009, A-025 |
| `ship-shape/SKILL.md` | 已审计 | A-003, A-025, A-026 |
| `ship-define/SKILL.md` | 已审计 | A-008, A-009, A-015, A-027 |
| `ship-define-review/SKILL.md` | 已审计 | A-008, A-027 |
| `ship-tech-discovery/SKILL.md` | 已审计 | A-031, A-032 |
| `ship-contract/SKILL.md` | 已审计 | A-004, A-013, A-028, A-032 |
| `ship-frontend-design/SKILL.md` | 已审计 | A-030, A-031, A-032 |
| `ship-backend-design/SKILL.md` | 已审计 | A-031, A-032 |
| `ship-design-review/SKILL.md` | 已审计 | A-004, A-029, A-031 |
| `ship-delivery-plan/SKILL.md` | 已审计 | A-020, A-021, A-022 |
| `ship-plan-review/SKILL.md` | 已审计 | A-015, A-020, A-022, A-040 |
| `ship-build/SKILL.md` | 已审计 | A-010, A-022, A-031 |
| `ship-verify/SKILL.md` | 已审计 | A-014, A-019, A-033, A-034, A-036 |
| `ship-handoff/SKILL.md` | 已审计 | A-018, A-019, A-034, A-035 |
| `ship-spec/SKILL.md` | 已审计 | A-016, A-039 |
| `ship-contract/references/api-contract-template.md` | 已审计 | A-028 |
| `ship-frontend-design/references/frontend-design-template.md` | 已审计 | N-003 |
| `ship-backend-design/references/backend-design-template.md` | 已审计 | N-003 |
| `ship-discover/references/product-brief-template.md` | 已审计 | N-003 |
| `ship-shape/references/design-brief-template.md` | 已审计 | N-004 |
| `ship-shape/references/anti-slop-checklist.md` | 已审计 | N-004 |
| `ship-shape/references/design-direction-library.md` | 已审计 | N-004 |
| `ship-shape/references/wireframe-starter/index.html` | 已审计 | A-026 |
| `ship-shape/references/wireframe-starter/variant-template.html` | 已审计 | A-026 |

## 问题到确认项映射

| 确认项 | 覆盖问题 | 修复性质 |
|--------|----------|----------|
| C-001 默认阶段模型 | A-001, A-002, A-005, A-006, A-008 | 协议语义 + 文档 + validator |
| C-002 scenario 初始化与 Discover 跳过规则 | A-009, A-025, A-027 | runtime 初始化 + meta 字段 + 文档 |
| C-003 scope 与 contract 语义 | A-004, A-011, A-012, A-013, A-014, A-020, A-021, A-028, A-029, A-030, A-037, A-040 | 协议语义 + scope-aware 文档/runtime |
| C-004 fast-track 与 lightweight change flow | A-010, A-031, A-034 | 协议语义 + task source |
| C-005 build / verify 的任务事实源和并行语义 | A-022, A-033 | 协议语义 + build/verify 文档 |
| C-006 meta 状态字段 | A-023, A-024 | meta schema + runtime |
| C-007 spec proposal 写入归口 | A-016 | runtime 约束 + 文档 |
| C-008 固定技术栈事实源 | A-032 | 协议语义 + tech-discovery/contract 文档 |
| C-009 verify / handoff 完成语义 | A-018, A-019, A-035, A-036 | 产物 frontmatter + 验收语义 |
| C-010 runtime stage advancement helper | A-038 | runtime helper + tests |
| C-011 低风险一致性修复 | A-003, A-006, A-007, A-015, A-017, A-026, A-039 | 文档/runtime/test 稳定性 |

## 修复后建议验证矩阵

| 验证项 | 目标 |
|--------|------|
| `python3 ship-orchestrator/scripts/validate_workflow_docs.py` | 共享协议、README、模板、stage map、delegation registry 基础一致 |
| `/Users/rao/.pyenv/shims/python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'` | runtime helper 行为测试通过 |
| `rg -n "4 大阶段|4 个大阶段|12 个 canonical|12 阶段" ../README.md README.md ship-orchestrator ship-*` | 确认旧阶段数量口径已清除或只出现在审计文档 |
| `rg -n "plan.md" ship-build/SKILL.md ship-verify/SKILL.md` | 确认 build/verify 不再误用单一 plan 事实源 |
| `rg -n "skip_log|lifecycle_status" ship-orchestrator/_templates/meta/meta.yml.template ship-orchestrator/scripts/feature_meta_runtime.py ship-orchestrator/_templates/protocol/workflow-protocol.md` | 确认 skip/lifecycle schema 和 runtime 落点一致 |
| `rg -n "ship-discover|ship-shape" ship-orchestrator/scripts/feature_meta_runtime.py ship-orchestrator/scripts/test_spec_runtime.py ship-orchestrator/scripts/validate_workflow_docs.py` | 确认条件前置阶段纳入 delegation/runtime 校验 |
| `rg -n "consumer|entrypoint|前端页面" ship-contract ship-frontend-design ship-design-review` | 确认 contract 页面语义已泛化且没有误阻塞 backend_only |
| `rg -n "verification_mode|manual_only|docs_config" ship-verify/SKILL.md ship-handoff/SKILL.md ship-orchestrator/_templates/protocol/workflow-protocol.md` | 确认文档/配置类变更验收路径闭环 |
| `rg -n "record-spec-proposal|source-stage" ship-orchestrator/scripts/feature_meta_runtime.py ship-orchestrator/scripts/test_spec_runtime.py ship-spec/SKILL.md` | 确认 spec proposal 归口与测试一致 |

## 当前阻塞边界

以下修改会改变技能套件语义，必须先由用户确认 `.docs/ship-skills-confirmation.md`：

- 阶段数量和默认展示模型。
- scenario 初始化是否强制要求 `--scenario`。
- `ship-contract` 是否泛化为 interaction boundary contract。
- fast-track 是否真实跳过 delivery-plan / plan-review，以及 lightweight task source 放在哪里。
- handoff `complete` 是否允许用户接受风险后的 FAIL/BLOCKED AC。
- 是否新增 `skip_log`、`lifecycle_status` 和 stage advancement helper。
