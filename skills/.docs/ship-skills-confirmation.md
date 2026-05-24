# ship-* skills 协议确认清单

更新时间：2026-05-24

本文从 `.docs/ship-skills-audit.md` 的 A-001 至 A-040 归并出需要用户确认的协议决策。确认后再修改 `SKILL.md`、共享协议、runtime helper、README 或测试。

用户确认结果记录在 `.docs/ship-skills-decision-log.md`。

## C-001: 默认阶段模型

关联问题：A-001, A-002, A-005, A-006, A-008

证据现状：

- `workflow_stage_map.py` 已是 14 个 canonical stages。
- `README.md`、`../README.md`、`workflow-protocol.md`、`ship-orchestrator/SKILL.md` 仍混有 4/5 macro stages、12/14 canonical stages 的旧口径。

建议确认：

- macro stage 统一为 5 个：`[Discover →] Define → Design → Build → Close`。
- `Discover` 是条件性 macro stage，只在场景 A/C 展示。
- canonical stage 统一为 14 个，前 2 个是条件性 pre-Define stages。
- 删除“第 1/第 2 阶段”“12 阶段”“4 大阶段”等绝对旧口径，改成 macro/stage role 描述。

## C-002: scenario 初始化与 Discover 跳过规则

关联问题：A-009, A-025, A-027

证据现状：

- 文档定义 A/C 起点为 `ship-discover`，B/D 起点为 `ship-define`。
- `feature_meta_runtime.py init` 固定 `current_stage: ship-define`，没有 `--scenario`。
- `ship-discover` / `ship-shape` 文档允许用户显式跳过，但共享协议缺少 `skip_log` 落点。

建议确认：

- `feature_meta_runtime.py init --scenario` 设为必填，取值 `greenfield | product_provided | prd_direct | evolve`。
- A/C 初始化到 `ship-discover`；B/D 初始化到 `ship-define`，并把 Discover/Shape 标记为 `skipped`。
- D 设置 `stages.ship-define.generation_mode = prd_direct`；其他 Define 模式显式写 `interview`。
- 用户可显式跳过 Discover/Shape，但必须写入 `skip_log`，并在后续 Define/Review 中作为风险处理。

## C-003: scope 与 contract 语义

关联问题：A-004, A-011, A-012, A-013, A-014, A-020, A-021, A-028, A-029, A-030, A-037, A-040

证据现状：

- 协议已有 `project_scope: fullstack | backend_only | frontend_only`。
- 多个阶段仍按 fullstack 固定文案和 checklist 执行。
- `ship-contract` 在协议中默认所有 scope 保留，但 `ship-contract/SKILL.md` 又说纯前端/纯后端部分场景无需接口规约。

建议确认：

- `ship-contract` 保留为通用 interaction boundary contract，不只代表前后端 HTTP API。
- 无 API / worker / batch 场景仍产出显式 empty/internal contract，说明 `N/A` 和原因。
- `backend_only` / `frontend_only` 仍保留 `ship-delivery-plan` 与 `ship-plan-review`，但只产出和评审对应侧 plan。
- 所有 scope-aware 阶段的 checklist、reviewed documents、macro summary、verification track、plan-review 流程都按 scope 裁剪。
- 将 contract 中“前端页面”泛化为 `consumer / entrypoint`；frontend-design 只要求当前前端实际消费的接口有页面/组件/route action 映射。

## C-004: fast-track 与 lightweight change flow

关联问题：A-010, A-031, A-034

证据现状：

- fast-track 文档允许跳过设计/计划，最小路径直接进入 `ship-build`。
- `ship-build` 当前要求已通过 plan-review 的 plan。
- 多个阶段写了“直接进入实现 / 无需本阶段 / 轻量 diff review”，但共享协议没有轻量任务源、状态或 handoff 规则。
- `ship-verify` 说纯文档/配置改动可跳过，`ship-handoff` 又要求 `verification.md.stage_status=ready`。

建议确认：

- 支持 fast-track 真实跳过 `ship-delivery-plan / ship-plan-review`。
- fast-track 必须有受控 lightweight task source，例如 `requirements.md` 或 `review-define.md` 中的 Fast-Track Task List。
- lightweight change flow 保留，但必须写明 `change_type`、最小任务源、验证模式、handoff 规则和 `skip_log`。
- 文档/配置类变更不跳过 `ship-verify`，而是走 `verification_mode: manual_only | docs_config`，由 `ship-verify` 产出 `verification.md.stage_status=ready`。

## C-005: build / verify 的任务事实源和并行语义

关联问题：A-022, A-033

证据现状：

- `ship-delivery-plan` 定义双 plan：`frontend-plan.md` / `backend-plan.md`。
- `ship-build` 和 `ship-verify` 多处仍写单一 `plan.md`。
- `ship-build` 同时写“前后端可并行”和“全局单 DOING”。

建议确认：

- standard/fullstack 下任务事实源是 `frontend-plan.md + backend-plan.md`。
- single-side scope 下只读取对应侧 plan。
- fast-track 下读取 C-004 确认的 lightweight task source。
- 正式编码保持全局单 `DOING`，`meta.yml.stages.ship-build.current_task_id` 仍为单值；“并行”只用于计划拆分、只读准备、验证和证据整理。

## C-006: meta 状态字段：skip 与 lifecycle

关联问题：A-023, A-024

证据现状：

- orchestrator 要求软门禁强制推进记录到 `meta.yml.skip_log`，模板/runtime 没有该字段。
- INSPECT_FEATURES 使用 `abandoned`，模板/runtime 没有 feature-level lifecycle。

建议确认：

- 增加 `skip_log: []`，记录 `at / from_stage / to_stage / gate_type / reason / user_sign_off`。
- 增加 feature-level `lifecycle_status: active | blocked | completed | abandoned`。
- stage status 保持现有枚举，不把 `abandoned` 混入 stage status。

## C-007: spec proposal 写入归口

关联问题：A-016

证据现状：

- 文档说 Proposal-First writeback 归口在 `ship-handoff`。
- runtime 允许 `record-spec-proposal --source-stage` 使用所有 spec hook。

建议确认：

- `record-spec-proposal` 只允许 `source_stage=ship-handoff`。
- 设计/build 阶段只记录候选观察或 warnings，不写入 `pending_proposals`。

## C-008: 固定技术栈时的事实源

关联问题：A-032

证据现状：

- `ship-tech-discovery` 允许固定技术栈时跳过。
- `ship-contract`、frontend/backend design 和 spec matching 又依赖 `tech-selection.md`。

建议确认：

- 固定技术栈场景仍生成 minimal `tech-selection.md`。
- 可简化或跳过 `tech-research.md`，但 `tech-selection.md` 必须记录沿用依据、版本、来源和风险。

## C-009: verify / handoff 的完成语义

关联问题：A-018, A-019, A-035, A-036

证据现状：

- `handoff.md` 缺少 frontmatter 定义。
- `verification.md` frontmatter 在 verify 和 handoff 两处不一致。
- handoff 的 `complete` 是否允许 FAIL/BLOCKED AC 语义不清。
- verify 要求把测试命令写入 README 或 CI，可能扩大 feature diff。

建议确认：

- `handoff.md` 也必须有标准 frontmatter。
- `verification.md` frontmatter 由 verify 创建时预置 spec 字段，handoff 后续补齐。
- `stage_status=complete` 表示交付关闭，不等于所有 AC PASS；允许 FAIL/BLOCKED，但必须有用户接受风险签字字段。
- 测试命令必须写入 `verification.md`；只有长期项目入口且用户确认时才写 README 或 CI。

## C-010: runtime stage advancement helper

关联问题：A-038

证据现状：

- 协议要求阶段完成后由 orchestrator 读取 frontmatter 并回写 `meta.yml`。
- runtime 目前没有 `advance-stage` / `sync-frontmatter-status` 类 helper。

建议确认：

- 增加最小状态推进 helper，负责读取产物 frontmatter、校验 gate/status、更新 `meta.yml.current_stage`、`stages.*.status`、`macro_stage`。
- scenario、scope、skip_log、lifecycle 与 stage advancement 一并纳入单元测试。

## C-011: 低风险一致性修复

关联问题：A-003, A-006, A-007, A-015, A-017, A-026, A-039

这些项不改变核心产品语义，建议在 C-001 至 C-010 确认后一起修：

- delegation runtime 补 `ship-discover` / `ship-shape`。
- review template README 去掉易漂移阶段编号。
- 统一 AC / Domain ID 示例。
- 修正 `spec_runtime.py` 自定义 `--spec-root` path 输出。
- wireframe starter 补 CDN integrity 或明确模板实例化规则。
- 统一 runtime helper 命令工作目录说明。
- 增加 Python 依赖说明或 manifest，稳定测试入口。

## 建议确认方式

若以上推荐方向符合预期，可以回复：

```text
按 C-001 到 C-011 的推荐方案执行。
```

如果有分歧，建议直接指出编号，例如：

```text
C-004 不同意，fast-track 仍必须生成轻量 plan；C-009 complete 必须要求所有 AC PASS。
```
