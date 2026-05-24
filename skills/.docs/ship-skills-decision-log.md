# ship-* skills 决策记录

更新时间：2026-05-24

本文记录 `.docs/ship-skills-confirmation.md` 中 C-001 至 C-011 的用户确认状态。用户已确认按 C-001 至 C-011 的推荐方案执行，且对应修复已落地。

状态说明：

- `pending`：等待用户确认。
- `accepted`：用户接受推荐方案。
- `changed`：用户确认了不同于推荐方案的替代决策。
- `deferred`：用户明确延后，不阻塞其他独立修复。

## 决策总览

| ID | 决策主题 | 状态 | 默认推荐 | 用户最终决策 |
|----|----------|------|----------|--------------|
| C-001 | 默认阶段模型 | accepted | 5 macro stages；14 canonical stages；Discover 条件性展示 | 按推荐方案执行 |
| C-002 | scenario 初始化与 Discover 跳过规则 | accepted | `init --scenario` 必填；A/C 到 `ship-discover`；B/D 到 `ship-define`；显式跳过写 `skip_log` | 按推荐方案执行 |
| C-003 | scope 与 contract 语义 | accepted | `ship-contract` 泛化为 interaction boundary contract；scope-aware 裁剪所有下游检查 | 按推荐方案执行 |
| C-004 | fast-track 与 lightweight change flow | accepted | fast-track 可跳过正式 plan gate，但必须有 lightweight task source 和 `skip_log` | 按推荐方案执行 |
| C-005 | build / verify 任务事实源和并行语义 | accepted | standard 读双 plan；单侧读对应 plan；fast-track 读 lightweight task source；正式编码全局单 `DOING` | 按推荐方案执行 |
| C-006 | meta 状态字段 | accepted | 增加 `skip_log` 和 feature-level `lifecycle_status` | 按推荐方案执行 |
| C-007 | spec proposal 写入归口 | accepted | `record-spec-proposal` 只允许 `source_stage=ship-handoff` | 按推荐方案执行 |
| C-008 | 固定技术栈事实源 | accepted | 固定技术栈仍生成 minimal `tech-selection.md` | 按推荐方案执行 |
| C-009 | verify / handoff 完成语义 | accepted | `complete` 表示交付关闭；允许用户接受风险后的 FAIL/BLOCKED AC；测试命令写 `verification.md` | 按推荐方案执行 |
| C-010 | runtime stage advancement helper | accepted | 增加最小 stage advancement helper，并纳入测试 | 按推荐方案执行 |
| C-011 | 低风险一致性修复 | accepted | 在 C-001 至 C-010 确认后统一修复低风险一致性问题 | 按推荐方案执行 |

## 决策详情

### C-001: 默认阶段模型

关联问题：A-001, A-002, A-005, A-006, A-008

默认推荐：

- macro stage 统一为 5 个：`[Discover →] Define → Design → Build → Close`。
- `Discover` 仅在场景 A/C 展示。
- canonical stage 统一为 14 个，前 2 个为条件性 pre-Define stages。

用户最终决策：按推荐方案执行。

### C-002: scenario 初始化与 Discover 跳过规则

关联问题：A-009, A-025, A-027

默认推荐：

- `feature_meta_runtime.py init --scenario` 必填。
- A/C 初始化到 `ship-discover`。
- B/D 初始化到 `ship-define`，并把 Discover/Shape 标记为 `skipped`。
- 用户显式跳过 Discover/Shape 时写 `skip_log`。

用户最终决策：按推荐方案执行。

### C-003: scope 与 contract 语义

关联问题：A-004, A-011, A-012, A-013, A-014, A-020, A-021, A-028, A-029, A-030, A-037, A-040

默认推荐：

- `ship-contract` 保留为 interaction boundary contract。
- 无 API / worker / batch 场景产出 empty/internal contract。
- 单侧 scope 保留 delivery-plan / plan-review，但只产出和评审对应侧 plan。
- 所有 scope-aware 阶段按 scope 裁剪 checklist、reviewed documents、macro summary、verification track 和 plan-review 流程。

用户最终决策：按推荐方案执行。

### C-004: fast-track 与 lightweight change flow

关联问题：A-010, A-031, A-034

默认推荐：

- fast-track 可跳过 `ship-delivery-plan / ship-plan-review`。
- fast-track 必须有受控 lightweight task source。
- lightweight flow 必须定义 `change_type`、最小任务源、验证模式、handoff 规则和 `skip_log`。
- 文档/配置类变更仍经过 `ship-verify`，使用 manual/docs verification mode。

用户最终决策：按推荐方案执行。

### C-005: build / verify 任务事实源和并行语义

关联问题：A-022, A-033

默认推荐：

- standard/fullstack 下任务事实源是 `frontend-plan.md + backend-plan.md`。
- single-side scope 下只读取对应侧 plan。
- fast-track 下读取 C-004 确认的 lightweight task source。
- 正式编码保持全局单 `DOING`。

用户最终决策：按推荐方案执行。

### C-006: meta 状态字段

关联问题：A-023, A-024

默认推荐：

- 增加 `skip_log: []`。
- 增加 feature-level `lifecycle_status: active | blocked | completed | abandoned`。
- `abandoned` 不进入 stage status 枚举。

用户最终决策：按推荐方案执行。

### C-007: spec proposal 写入归口

关联问题：A-016

默认推荐：

- `record-spec-proposal` 只允许 `source_stage=ship-handoff`。
- 设计/build 阶段只记录候选观察或 warnings，不写入 `pending_proposals`。

用户最终决策：按推荐方案执行。

### C-008: 固定技术栈事实源

关联问题：A-032

默认推荐：

- 固定技术栈场景仍生成 minimal `tech-selection.md`。
- `tech-research.md` 可简化或跳过，但 `tech-selection.md` 必须保留沿用依据、版本、来源和风险。

用户最终决策：按推荐方案执行。

### C-009: verify / handoff 完成语义

关联问题：A-018, A-019, A-035, A-036

默认推荐：

- `handoff.md` 必须有标准 frontmatter。
- `verification.md` 由 verify 创建时预置 spec 字段，handoff 后续补齐。
- `stage_status=complete` 表示交付关闭，不等于所有 AC PASS。
- FAIL/BLOCKED AC 允许在用户接受风险并签字后关闭。
- 测试命令必须写入 `verification.md`；只有长期项目入口且用户确认时才写 README 或 CI。

用户最终决策：按推荐方案执行。

### C-010: runtime stage advancement helper

关联问题：A-038

默认推荐：

- 增加最小状态推进 helper。
- helper 读取产物 frontmatter，校验 gate/status，更新 `meta.yml.current_stage`、`stages.*.status`、`macro_stage`。
- scenario、scope、skip_log、lifecycle 与 stage advancement 一并纳入测试。

用户最终决策：按推荐方案执行。

### C-011: 低风险一致性修复

关联问题：A-003, A-006, A-007, A-015, A-017, A-026, A-039

默认推荐：

- 在 C-001 至 C-010 确认后统一修复低风险一致性问题。
- 不改变核心产品语义，但要纳入 validator 和 unit tests 防回归。

用户最终决策：按推荐方案执行。
