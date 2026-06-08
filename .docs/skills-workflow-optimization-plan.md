# Skills Workflow 优化修改计划

> 目的：把红队、黑队、白队审查发现的问题转成可直接执行的工程修改计划。本文只规划修改，不直接修改 `skills/` 源文件。

## 0. 背景与成功标准

### 0.1 已确认问题

审查对象：`skills/` 工作流技能套件，核心集中在：

- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/_templates/protocol/*.md`
- `skills/ship-orchestrator/_templates/meta/meta.yml.template`
- `skills/ship-orchestrator/scripts/*.py`
- `skills/ship-build/SKILL.md`
- `skills/ship-delivery-plan/SKILL.md`
- `skills/ship-plan-review/SKILL.md`

主要风险：

1. Source Code Edit Barrier 文档要求严格，但脚本没有完全机器化。
2. `current_stage == ship-build`、`allowed_files` 覆盖、workspace 路径边界、用户签字真实性存在校验缺口。
3. traceability、workflow doctor、validator strictness、meta template 存在不一致或可维护性不足。
4. 多处协议重复描述，未来容易漂移。

### 0.2 总体成功标准

完成本计划后应满足：

- 未到 `ship-build` 时，任何业务源码修改 preflight 都失败。
- 当前 DOING task 未授权的文件无法通过 implementation preflight。
- `feature_dir`、`spec_root`、`feature_root` 不能逃逸 workspace。
- hard gate 的用户签字具备可审计事件记录，不再只依赖文档 frontmatter 自证。
- Source Code Edit Barrier 只有一个协议事实源，其他文档引用它。
- `workflow_doctor.py` 能报告提前实现/越界修改风险。
- traceability 在 verify/handoff 阶段可进入 strict blocking mode。
- 新增或更新的 hardening tests 覆盖以上行为。

## 1. P0：源码修改屏障机器化

### 1.1 强制校验 `current_stage == ship-build`

**问题**

协议要求源码修改必须满足 `meta.yml.current_stage == ship-build`，但 `implementation_preflight.py` 当前只读取 `current_stage` 并调用 `check_transition(feature_dir, "ship-build")`，没有显式阻塞 `current_stage != ship-build`。

**涉及文件**

- `skills/ship-orchestrator/scripts/implementation_preflight.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

**修改方案**

1. 在 `implementation_preflight()` 读取 meta 后新增硬校验：
   - 若 `current_stage != "ship-build"`，追加 error：`current_stage_not_ship_build`。
   - error message 明确：`implementation edits require meta.yml.current_stage == ship-build`。
2. 保留 `stage_transition_check.py --target-stage ship-build` 作为上游完整性校验，但不能替代当前阶段相等校验。
3. 在 JSON 输出中保留：
   - `current_stage`
   - `required_stage: ship-build`
   - `allowed: false`
   - `issues[].code == current_stage_not_ship_build`

**测试计划**

新增单测：

- fixture 中 `review-plan.md` 已 `approved + user_sign_off + signed_at`。
- plan 中存在唯一 DOING task。
- 上游 artifact 足够让 `stage_transition_check(..., ship-build)` 通过。
- 但 `meta.yml.current_stage = ship-plan-review` 或 `ship-delivery-plan`。
- 期望 `implementation_preflight(...)["allowed"] == False`，且包含 `current_stage_not_ship_build`。

**验收标准**

- `python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py` 通过。
- 手动运行 `implementation_preflight.py <fixture> --json` 时，非 `ship-build` 阶段不放行。

### 1.2 增加 `--files` 并校验 `allowed_files` 覆盖

**问题**

文档要求当前 DOING task 的 `allowed_files` 覆盖要修改的文件，但 `build_task_preflight.py` 只检查任务块中存在 `allowed_files` 字样，没有解析路径，也没有校验实际待改文件。

**涉及文件**

- `skills/ship-orchestrator/scripts/build_task_preflight.py`
- `skills/ship-orchestrator/scripts/implementation_preflight.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-build/SKILL.md`
- `skills/ship-orchestrator/_templates/protocol/gate-protocol.md`

**修改方案**

1. 在 `build_task_preflight.py` 中新增解析函数：
   - `extract_allowed_files(block: str) -> list[str]`
   - 支持 YAML-like 列表：
     - `- allowed_files: src/a.ts`
     - `- allowed_files:` 下一行缩进列表
     - `allowed files:` / `允许文件:` 作为兼容别名
   - 返回规范化后的 workspace-relative path/glob。
2. 新增路径校验函数：
   - 禁止空值。
   - 禁止绝对路径。
   - 禁止 `..` 逃逸。
   - 禁止裸 `*`、`**/*` 这类过宽通配。
   - 允许明确文件、目录前缀或受限 glob，例如：`src/auth.ts`、`src/auth/**`、`src/**/*.test.ts`。
3. `build_task_preflight()` 返回的 DOING task 增加：
   - `allowed_files: [...]`
   - `invalid_allowed_files: [...]`
4. `implementation_preflight.py` 增加 CLI 参数：
   - `--files <path...>`：本次计划修改的业务源码文件。
   - 无 `--files` 时保持兼容，但返回 warning：`target_files_not_provided`。如果要严格执行，可加 `--strict-files`。
5. 在 `implementation_preflight()` 中：
   - 归一化 `--files` 为 workspace-relative path。
   - 逐个匹配唯一 DOING task 的 `allowed_files`。
   - 未命中时报 error：`file_not_allowed_by_doing_task`。
6. 保留 `build_task_preflight.py` 对唯一 DOING、AC refs、verification command、任务简报的既有检查。

**测试计划**

新增单测：

1. `--files src/auth.ts` 且 `allowed_files: src/auth.ts` → allowed。
2. `--files src/auth.test.ts` 但 `allowed_files: src/auth.ts` → error `file_not_allowed_by_doing_task`。
3. `allowed_files: ../secrets.env` → error `invalid_allowed_file_path`。
4. `allowed_files: /tmp/a.ts` → error `invalid_allowed_file_path`。
5. `allowed_files: **/*` → error `allowed_file_glob_too_broad`。
6. `allowed_files: src/auth/**` + `--files src/auth/service.ts` → allowed。

**验收标准**

- `build_task_preflight.py --json` 输出可见解析后的 `allowed_files`。
- `implementation_preflight.py --files ... --json` 能阻塞未授权文件。
- `ship-build/SKILL.md` 中“开始编码前运行”示例更新为包含 `implementation_preflight.py --files`。

### 1.3 将 implementation preflight 设为唯一源码修改入口

**问题**

文档中有的地方只提 `stage_transition_check.py + build_task_preflight.py`，有的地方要求 `implementation_preflight.py`，容易让执行者绕过统一入口。

**涉及文件**

- `skills/README.md`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `skills/ship-orchestrator/_templates/protocol/gate-protocol.md`
- `skills/ship-orchestrator/_templates/protocol/resume-protocol.md`
- `skills/ship-build/SKILL.md`

**修改方案**

1. 定义唯一规则：
   - 修改业务源码、测试、配置、迁移、脚本或构建文件前，必须运行 `implementation_preflight.py`。
   - `stage_transition_check.py` 和 `build_task_preflight.py` 是 implementation preflight 内部依赖，不作为人工执行的替代入口。
2. README 只写摘要并引用 orchestrator Source Code Edit Barrier。
3. `workflow-protocol.md` 保留完整协议事实源。
4. `gate-protocol.md` 只列“进入 ship-build 的 gate”，不要重复源码修改屏障全部条件。
5. `resume-protocol.md` 中恢复编码统一指向 `implementation_preflight.py --files`。

**测试计划**

- 更新 `validate_workflow_docs.py`，检测旧文案是否仍宣称“只通过 `stage_transition_check.py + build_task_preflight.py` 即可修改源码”。
- regression prompts 中 Source Code Edit Barrier 场景统一写 `implementation_preflight.py`。

**验收标准**

- 搜索 `stage_transition_check.py --target-stage ship-build` 时，不再出现“它单独足以授权源码修改”的表述。
- `validate_workflow_docs.py` 通过。

## 2. P0：workspace 与 feature 边界加固

### 2.1 禁止 workspace-relative path 逃逸

**问题**

`spec_runtime.py` 只禁止绝对路径，没有禁止 `../outside`。`_resolve_workspace_relative()` resolve 后可能落到 workspace 外。

**涉及文件**

- `skills/ship-orchestrator/scripts/spec_runtime.py`
- `skills/ship-orchestrator/scripts/test_spec_runtime.py`
- `skills/ship-spec/SKILL.md`

**修改方案**

1. 修改 `_normalize_relative_path()`：
   - 拆分 path parts。
   - 若包含 `..`，直接 `ValueError`。
   - 若 path 为 `.` 或空，按字段语义决定是否允许；`spec_root` / `feature_root` 不允许为 `.`。
2. 修改 `_resolve_workspace_relative()`：
   - resolve 后必须 `resolved.relative_to(workspace_root.resolve())` 成功。
   - 失败时报错：`path escapes workspace_root`。
3. 对 `feature_root` 增加约束：
   - 必须是 workspace 内目录。
   - 不允许指向项目根以外，也不允许指向源码目录如 `src`，除非明确后续支持。

**测试计划**

新增或更新 `test_spec_runtime.py`：

- `spec_root: ../spec` → fail。
- `feature_root: ../.docs` → fail。
- `spec_root: /tmp/spec` → fail。
- `spec_root: .docs/spec` → pass。
- project_group 下合法 `_shared` 和 `<project>` spec root 继续 pass。

**验收标准**

- `python3 skills/ship-orchestrator/scripts/test_spec_runtime.py` 通过。
- 所有 workspace config helper 返回的 resolved paths 都在 workspace root 内。

### 2.2 所有 gate/preflight 统一校验 feature_dir 位于 feature_root

**问题**

初始化阶段有 feature_dir 解析约束，但 `stage_transition_check.py`、`implementation_preflight.py`、`workflow_doctor.py` 接受任意目录，只要里面有 `meta.yml` 和 artifact 即可参与校验。

**涉及文件**

- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/implementation_preflight.py`
- `skills/ship-orchestrator/scripts/workflow_doctor.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`

**修改方案**

1. 新增共享 helper：
   - `resolve_and_validate_feature_dir(feature_dir: Path) -> FeatureContext`
   - 读取 `meta.yml.spec_context.feature_root` 或 workspace `.docs/ship/project.yml`。
   - 校验 `feature_dir` 在 `feature_root` 下，且目录名匹配 `feature-*`。
2. 所有入口脚本先调用该 helper。
3. 若老 fixture 没有 workspace config：
   - 在 tests 中补最小 `.docs/ship/project.yml`。
   - 或 helper 支持 test-only fallback，但必须有 warning，生产路径默认严格。
4. JSON 输出新增：
   - `workspace_root`
   - `feature_root`
   - `feature_dir_validated: true`

**测试计划**

- 伪造 `/tmp/fake-feature/meta.yml` 调用 `implementation_preflight.py` → fail。
- 合法 `.docs/feature-*/meta.yml` → pass 到后续 checks。
- `feature_dir` 在 workspace 下但不是 `feature-*` → fail。

**验收标准**

- gate/preflight/doctor 不再接受任意目录。
- 旧 fixtures 更新后测试全部通过。

## 3. P0/P1：用户签字与 gate 审计

### 3.1 引入 confirmation log

**问题**

当前 hard gate 只校验 `review_status: approved`、`user_sign_off`、`signed_at` 非空，无法区分真实用户确认和文件伪造。

**涉及文件**

- `skills/ship-orchestrator/_templates/meta/meta.yml.template`
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `skills/ship-orchestrator/_templates/protocol/gate-protocol.md`
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-define-review/SKILL.md`
- `skills/ship-design-review/SKILL.md`
- `skills/ship-plan-review/SKILL.md`

**修改方案**

1. 在 `meta.yml.template` 增加 append-only 审计结构：
   ```yaml
   confirmation_log: []
   ```
2. 定义条目字段：
   - `id`
   - `type: hard_gate_signoff | soft_gate_skip | uiux_gate | selected_scope_ac | shipkit_exit`
   - `stage`
   - `artifact`
   - `user_sign_off`
   - `signed_at`
   - `actor: user`
   - `source: current_session`
   - `message_excerpt`
3. hard gate review frontmatter 增加可选字段：
   - `confirmation_id: ""`
4. hard gate approved 判定更新为：
   - `review_status == approved`
   - `user_sign_off` 非空
   - `signed_at` 非空
   - `confirmation_id` 存在并能在 `meta.yml.confirmation_log` 找到匹配条目
5. 为兼容已有 feature：
   - 第一期 validator 对缺少 `confirmation_id` 给 warning。
   - strict mode 或新 feature 中升级为 error。
6. `feature_meta_runtime.py` 增加函数：
   - `append_confirmation_log(...)`
   - `validate_gate_confirmation(...)`

**测试计划**

- approved gate 无 `confirmation_id`：legacy mode warning，strict mode error。
- approved gate 有不存在的 `confirmation_id`：error。
- confirmation log stage/artifact 不匹配：error。
- pending gate 不要求 confirmation id。
- 子代理草案 `review_status: pending` 且 signoff 为空仍 pass。

**验收标准**

- hard gate 签字不再完全由 review 文件自证。
- 三个 review skill 文档明确：只有主上下文在用户明确批准后写 review frontmatter 和 confirmation log。

### 3.2 规范 ShipKit exit escape hatch

**问题**

协议允许用户明确退出 ShipKit 后不再强制门禁，这是产品选择，但需要强确认和审计，避免被“直接做”等模糊话术触发。

**涉及文件**

- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/_templates/protocol/resume-protocol.md`
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`

**修改方案**

1. 定义退出必须满足：
   - 用户明确说“退出 ShipKit / stop ShipKit workflow”。
   - agent 复述后果：不再强制 workflow gate。
   - 用户二次确认。
2. 写入 `confirmation_log`：
   - `type: shipkit_exit`
   - `stage`
   - `reason`
3. 在 orchestrator 文档中明确：
   - “直接做”“先开发”“我确认”都不是退出 ShipKit。

**测试计划**

- regression prompt：用户说“直接做”仍被阻塞。
- 用户明确“退出 ShipKit”但未二次确认 → 不退出。
- 二次确认后允许跳出 workflow，但需要留下 audit note。

**验收标准**

- escape hatch 可用但不可误触发。

## 4. P1：workflow doctor 与提前实现检测

### 4.1 `workflow_doctor.py` 增加 git/worktree 诊断

**问题**

恢复协议要求检测非法提前实现，但 `workflow_doctor.py` 目前只聚合 artifact validation 和 transition next action。

**涉及文件**

- `skills/ship-orchestrator/scripts/workflow_doctor.py`
- `skills/ship-orchestrator/_templates/protocol/resume-protocol.md`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`

**修改方案**

1. 新增只读诊断：
   - 调用 `git status --porcelain`。
   - 区分 workflow artifact 改动与业务源码改动。
   - workflow artifact 范围：`feature_root/feature-*` 内文档和 resource。
   - 其他源码、测试、配置、迁移、脚本、构建文件为 implementation changes。
2. 若 `current_stage` 未到 `ship-build` 且存在 implementation changes：
   - doctor 输出 error：`implementation_changes_before_build_gate`。
3. 若已到 `ship-build` 但 changed files 不在 DOING task `allowed_files`：
   - doctor 输出 error：`implementation_changes_outside_allowed_files`。
4. JSON 输出增加：
   - `worktree_status`
   - `implementation_changes`
   - `workflow_artifact_changes`
   - `outside_allowed_files`

**测试计划**

- 在临时 git repo fixture 中构造提前改源码，doctor 应 error。
- 改 `.docs/feature-*/requirements.md` 不报提前实现。
- `ship-build` 阶段改 allowed file 不报错。
- `ship-build` 阶段改非 allowed file 报错。

**验收标准**

- resume protocol 的“非法提前实现检测”有脚本实现。
- doctor 输出可用于恢复时决策。

## 5. P1：traceability 与 strict validator

### 5.1 traceability 增加 strict mode

**问题**

`validate_traceability.py` 对 AC 缺少 contract/plan/test 链路只给 warning，但到 verify/handoff 阶段这些缺口应阻塞。

**涉及文件**

- `skills/ship-orchestrator/scripts/validate_traceability.py`
- `skills/ship-orchestrator/scripts/validate_verification.py`
- `skills/ship-orchestrator/scripts/validate_handoff.py`
- `skills/ship-orchestrator/tests/regression-prompts.md`

**修改方案**

1. CLI 增加：
   - `--strict`
   - `--stage <ship-contract|ship-delivery-plan|ship-verify|ship-handoff>`
2. severity 策略：
   - early design/build planning：trace gap 可 warning。
   - `ship-verify`：缺 test link 为 error。
   - `ship-handoff`：缺 contract/plan/test/handoff 任一关键链路为 error。
3. `validate_verification.py` 和 `validate_handoff.py` 内部调用 strict traceability，或在 `validate_feature_artifacts.py` 聚合时按当前阶段升级 severity。

**测试计划**

- requirements 有 AC，verification 缺对应 AC：
  - 非 strict warning。
  - `--strict --stage ship-verify` error。
- handoff 缺 AC：`--strict --stage ship-handoff` error。
- orphan AC refs 继续 warning 或按 strict 策略升级。

**验收标准**

- close 前 AC 链路缺口不可被 warning 掩盖。

### 5.2 建立 `validate_all.py` 聚合器

**问题**

当前 README 列出很多 validator 命令，执行者容易漏跑，CI 也难统一。

**涉及文件**

- `skills/ship-orchestrator/scripts/validate_all.py`（新增）
- `skills/README.md`
- `skills/ship-orchestrator/tests/README.md`

**修改方案**

1. 新增聚合脚本，按当前 feature 状态和 project_scope 运行：
   - `validate_feature_artifacts.py`
   - `validate_requirements.py`
   - `validate_contract.py`
   - `validate_tech_discovery.py`
   - `validate_design_alignment.py`
   - `validate_delivery_plan.py`
   - `validate_traceability.py`
   - `validate_verification.py`
   - `validate_handoff.py`
   - `workflow_doctor.py`
2. 输出统一 JSON：
   - `ok`
   - `errors_count`
   - `warnings_count`
   - `checks[]`
   - `issues[]`
3. 支持 `--strict`。

**测试计划**

- 构造一个已有 fixture，validate_all 输出包含多个 check。
- 任一子检查 error 时 `ok=false`。
- strict mode 能升级 traceability。

**验收标准**

- README 的常用校验命令优先推荐 `validate_all.py`。

## 6. P1：meta template 与 scope freeze 对齐

### 6.1 `meta.yml.template` 增加 `scope_freeze`

**问题**

`validate_feature_artifacts.py` 在 design review approved 后要求 `scope_freeze`，但 `meta.yml.template` 没有该结构，恢复和手动初始化容易漏填。

**涉及文件**

- `skills/ship-orchestrator/_templates/meta/meta.yml.template`
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`

**修改方案**

新增：

```yaml
scope_freeze:
  status: open          # open | frozen | reopened
  frozen_scope: ""
  frozen_at: ""
  frozen_by_gate: ""
  user_sign_off: ""
  reopen_reason: ""
  reopened_at: ""
```

同步更新 helper：

- `ensure_scope_freeze(data)` 初始化默认结构。
- `scope_freeze_is_valid()` 接受 `status=open` 作为设计评审前默认状态。
- design review approved 后必须转为 `frozen`。

**测试计划**

- 新 feature meta 初始化包含 `scope_freeze.status=open`。
- design review approved 但未 frozen → error。
- frozen_scope 与 project_scope 不一致 → error。

**验收标准**

- template、runtime、validator 对 scope freeze 字段一致。

## 7. P1/P2：结构化 schema 替代关键词启发式

### 7.1 先处理高价值 validator

**问题**

frontend/backend design、observability、AC evidence 等部分检查依赖关键词，容易被空洞模板绕过，也可能误伤。

**涉及文件**

- `skills/ship-orchestrator/scripts/validate_frontend_design.py`
- `skills/ship-orchestrator/scripts/validate_backend_design.py`
- `skills/ship-orchestrator/scripts/validate_contract.py`
- `skills/ship-orchestrator/scripts/validate_verification.py`
- 对应 `SKILL.md` 与 references templates

**修改方案**

第一阶段只做最小结构化增强：

1. 要求关键章节中出现表格或列表字段：
   - `AC ID`
   - `Source / Evidence`
   - `Owner`
   - `N/A reason`
2. 对 observability 要求：
   - `metrics`
   - `logs`
   - `traces` 或 `N/A reason`
   - `alerts` 或 `N/A reason`
3. 对 verification 要求：
   - 每个 AC 有 `PASS / FAIL / BLOCKED / NOT_TESTED`。
   - `NOT_TESTED` 必须有 reason。

**测试计划**

- 空洞模板含关键词但缺字段 → warning/error。
- 简单项目写明 `N/A reason` → pass。
- 复杂项目缺 observability owner → warning。

**验收标准**

- validator 不再只靠关键词存在判断核心完整性。

## 8. P2：可观测性与回归覆盖

### 8.1 增加 workflow events log

**涉及文件**

- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`

**修改方案**

1. 在 feature 目录下新增 append-only：
   - `.workflow/events.jsonl` 或 `workflow-events.jsonl`
2. 事件类型：
   - `stage_transition`
   - `preflight_run`
   - `validator_run`
   - `user_confirmation`
   - `shipkit_exit`
3. 每条包含：
   - `event_id`
   - `timestamp`
   - `actor`
   - `stage`
   - `summary`
   - `issues_hash`

**验收标准**

- workflow doctor 能显示 last transition / last validator run。

### 8.2 补齐 golden path fixtures

**涉及文件**

- `skills/ship-orchestrator/tests/fixtures/*`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/tests/README.md`

**建议新增 fixtures**

1. `a-greenfield-happy-path`
2. `c-evolve-happy-path`
3. `fullstack-build-ready`
4. `frontend-only-happy-path`
5. `backend-only-happy-path`
6. `implementation-preflight-file-scope-violation`
7. `workspace-path-escape`

**验收标准**

- 每个 P0/P1 修复点至少有一个 regression test。
- tests README 列出风险点到测试用例映射。

## 9. 推荐实施顺序

### Phase 1：P0 安全闭环

1. `implementation_preflight.py` 强制 `current_stage == ship-build`。
2. `build_task_preflight.py` 解析 `allowed_files`。
3. `implementation_preflight.py --files` 校验待改文件。
4. `spec_runtime.py` 禁止 workspace path escape。
5. 更新 hardening tests。

**阶段验收**

```bash
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
```

### Phase 2：协议收敛与审计

1. Source Code Edit Barrier 文档去重。
2. 增加 `confirmation_log`。
3. 三个 hard gate review skill 更新签字流程。
4. `meta.yml.template` 增加 `scope_freeze`。

**阶段验收**

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

### Phase 3：恢复诊断与 strict validation

1. `workflow_doctor.py` 增加 git/worktree 诊断。
2. `validate_traceability.py --strict`。
3. `validate_all.py` 聚合器。
4. 更新 README 和 tests README。

**阶段验收**

```bash
python3 skills/ship-orchestrator/scripts/validate_all.py <fixture> --strict --json
python3 skills/ship-orchestrator/scripts/workflow_doctor.py <fixture> --json
```

### Phase 4：结构化 schema 与 fixtures

1. frontend/backend/contract/verification validator 结构化增强。
2. 补 golden path fixtures。
3. 完善 regression prompts。

**阶段验收**

```bash
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

## 10. 风险与取舍

### 10.1 兼容性风险

- 增加 `confirmation_id` 和 `confirmation_log` 会影响已有 feature。
- 建议使用 legacy warning + strict error 的迁移策略。

### 10.2 测试 fixture 维护成本

- 引入 workspace 边界校验后，旧 fixture 可能缺 `.docs/ship/project.yml`。
- 建议统一 fixture helper 生成最小 workspace config。

### 10.3 执行复杂度

- `--files` 需要执行者在修改前声明文件。
- 这是必要约束；可通过工具包装自动从 planned patch 或用户指定文件中传入。

## 11. 最小首个 PR 范围

如果要拆成第一个最小安全 PR，建议只包含：

1. `implementation_preflight.py`：
   - 强制 `current_stage == ship-build`。
   - 增加 `--files` 参数。
2. `build_task_preflight.py`：
   - 解析 `allowed_files`。
   - 校验 path/glob 基础安全。
3. tests：
   - 非 ship-build 阶段不放行。
   - 未授权文件不放行。
   - `../`、绝对路径、过宽 glob 不放行。
4. docs：
   - `ship-build/SKILL.md` 更新 preflight 示例。
   - `ship-orchestrator/SKILL.md` 明确 `implementation_preflight.py --files` 是源码修改入口。

首个 PR 不处理 confirmation log、doctor、strict traceability，避免范围过大。

## 12. 完成定义

本计划全部完成时，需要满足：

- P0 项全部有脚本校验和 regression test。
- P1 项至少有文档收敛、validator strict mode 或 doctor 诊断覆盖。
- 所有变更通过：
  ```bash
  python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
  python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
  python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
  ```
- `skills/README.md` 的维护章节更新为优先使用聚合校验命令。
