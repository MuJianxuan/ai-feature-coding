# ship-* skills 目标完成度审计

更新时间：2026-05-24

本文件按用户目标审计当前完成度。目标是：深入梳理当前 `ship-*` 的所有技能，完整分析整套技能，确保技能之间没有语义冲突、矛盾点或不合理设计；遇到问题及时沟通并找用户确认。

## 目标拆解

| 要求 | 当前证据 | 判定 |
|------|----------|------|
| 梳理所有 `ship-*` 技能 | `.docs/ship-skills-traceability.md` 覆盖 16 个 `ship-*` `SKILL.md` 文件 | 已完成审计覆盖 |
| 梳理 references / templates / scripts | `.docs/ship-skills-traceability.md` 覆盖 references、`_templates`、runtime scripts 和 tests | 已完成审计覆盖 |
| 分析语义冲突和设计不合理处 | `.docs/ship-skills-audit.md` 记录 A-001 至 A-040 | 已完成问题识别 |
| 区分问题与非问题 | `.docs/ship-skills-audit.md` 记录 N-001 至 N-004 | 已完成初步分类 |
| 遇到需要产品/协议决策的问题找用户确认 | `.docs/ship-skills-confirmation.md` 归并 C-001 至 C-011；`.docs/ship-skills-decision-log.md` 已记录 accepted | 已完成确认 |
| 确保最终技能之间无冲突 | 语义文件、runtime、validator 和关键文档已同步修复并通过验证 | 已完成修复 |
| 验证修复后的最终状态 | `validate_workflow_docs.py` 与 unit tests 已通过 | 已完成验证 |

## 已交付文档

| 文档 | 用途 | 状态 |
|------|------|------|
| `.docs/ship-skills-audit.md` | 详细审计报告，记录事实、A 问题、N 非问题 | 已生成 |
| `.docs/ship-skills-confirmation.md` | 把 A-001 至 A-040 归并为 C-001 至 C-011 用户确认项 | 已生成 |
| `.docs/ship-skills-decision-log.md` | 记录 C 决策状态和用户最终决策 | 已生成，均为 accepted |
| `.docs/ship-skills-traceability.md` | 文件覆盖、问题映射、修复后验证矩阵 | 已生成 |
| `.docs/ship-skills-remediation-plan.md` | 用户确认后的分批修复计划 | 已生成 |

## 当前完成结论

当前仓库已按 C-001 至 C-011 的推荐方案执行，相关语义文件、runtime helper、validator、README 与关键 tests 均已同步修复并通过验证。

## 当前可证明完成的部分

已通过当前状态证明：

- 已发现并记录 40 个问题项：
  - 阶段模型与口径：A-001, A-002, A-005, A-006, A-008
  - scenario / Discover / generation mode：A-009, A-025, A-027
  - scope / contract / 单侧裁剪：A-004, A-011, A-012, A-013, A-014, A-020, A-021, A-028, A-029, A-030, A-037, A-040
  - fast-track / lightweight / task source：A-010, A-022, A-031, A-033, A-034
  - meta / lifecycle / stage advancement：A-023, A-024, A-038
  - delegation / spec hook / runtime helper：A-003, A-016, A-017, A-039
  - 固定技术栈事实源：A-032
  - verify / handoff：A-018, A-019, A-035, A-036
  - examples / assets / dependency：A-007, A-015, A-026
- 已记录 4 个非问题项：N-001 至 N-004。
- 已把 40 个问题归并为 11 个用户确认决策：
  - C-001 默认阶段模型
  - C-002 scenario 初始化与 Discover 跳过规则
  - C-003 scope 与 contract 语义
  - C-004 fast-track 与 lightweight change flow
  - C-005 build / verify 任务事实源和并行语义
  - C-006 meta 状态字段
  - C-007 spec proposal 写入归口
  - C-008 固定技术栈事实源
  - C-009 verify / handoff 完成语义
  - C-010 runtime stage advancement helper
  - C-011 低风险一致性修复
- 已制定确认后的修复批次和验证矩阵。

## 进入下一阶段的条件

无需再等待用户确认；后续只需保持当前语义约束不回退。

## 当前完成定义

当前已经满足：

- `.docs/ship-skills-decision-log.md` 中 C-001 至 C-011 均有最终决策。
- `.docs/ship-skills-audit.md` 中 A-001 至 A-040 均被标记为已修复、按用户决策保留或明确延后。
- 语义文件与 runtime 已按 `.docs/ship-skills-remediation-plan.md` 修复。
- `validate_workflow_docs.py` 已扩展，能防止关键冲突回归。
- unit tests 覆盖 scenario、scope、delegation、spec proposal、stage advancement 等关键 runtime 行为。
- 所有验证命令通过。
