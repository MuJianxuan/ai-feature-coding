# Ship workflow 五项问题修复计划

## 1. 背景

本计划基于对 `skills/` 工作流的完整梳理结果，目标是修正已确认的 5 个冲突点和逻辑引导错误。

当前主干 `standard + fullstack` 路径整体自洽，`validate_workflow_docs.py` 和现有单元测试均通过。问题主要集中在变体路径与文案合同：

- `backend_only` 与 `ship-shape` 跳过规则在文档和 runtime 之间不一致。
- `fast-track` 已写入协议，但 transition checker 与 build preflight 不支持真实执行。
- soft gate 文案把 artifact `stage_status` 和 meta `status` 混用。
- `ship-build` 入口条件写错字段。
- `skills/README.md` 默认原则漏写场景 D。

本次修复原则：

- 优先修正可执行 contract，不只改文案。
- 每个文档变更都同步 runtime / validator / tests。
- 不新增阶段，不扩大 workflow 范围。
- 保持现有 `standard` 主路径行为不变。

## 2. 总体目标

修复后应满足：

1. `backend_only` 下，若场景 A/C 激活 Discover，`ship-shape` 会被 runtime、transition checker 和文档一致地视为 skipped。
2. `fast-track` 能按协议走最小路径，不被 design / plan 产物缺失错误阻断。
3. `fast-track` 的任务事实源有明确文件、格式、validator 和 preflight 支持。
4. 所有非 review artifact frontmatter 只使用 `stage_status: draft | ready | complete`。
5. hard gate 入口和推进条件统一使用 `review_status: approved + user_sign_off + signed_at`。
6. README 入口说明覆盖 A/B/C/D 四种场景。

## 3. 修改项一：补齐 `backend_only` 跳过 `ship-shape`

### 3.1 问题

文档约定：

- `backend_only` 时跳过 `ship-frontend-design`。
- 若场景 A/C 且为 `backend_only`，还应跳过 `ship-shape`。

但 runtime 当前只在 `SCOPE_SKIP_MAP` 中跳过 `ship-frontend-design`，没有跳过 `ship-shape`。transition checker 也没有基于 `project_scope=backend_only` 裁剪 `ship-shape`。

影响：

- A/C + `backend_only` 创建后可能仍需要 `design-brief.md`。
- 从 `ship-discover` 推进到 `ship-define` 或后续阶段时，可能被缺失 `ship-shape` 产物阻断。

### 3.2 目标行为

当 `meta.yml.project_scope = backend_only`：

- `meta.yml.stages.ship-shape.status = skipped`。
- `stage_transition_check.py` 在计算 required previous stages 时跳过 `ship-shape`。
- `validate_feature_artifacts.py` 不要求 `design-brief.md`。
- 文档继续明确：`ship-shape` 跳过只适用于 `backend_only`，不影响 `frontend_only/fullstack`。

### 3.3 涉及文件

- `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/test_spec_runtime.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- 视情况同步 `skills/ship-orchestrator/SKILL.md` 和 `workflow-protocol.md`，保持文案更精确。

### 3.4 修改步骤

1. 修改 `SCOPE_SKIP_MAP`：
   - `backend_only` 从 `["ship-frontend-design"]` 改为 `["ship-shape", "ship-frontend-design"]`。
   - 保持 `frontend_only` 只跳过 `ship-backend-design`。

2. 修改 `stage_transition_check._required_previous_stages`：
   - `backend_only` 时从 previous stages 中移除 `ship-shape` 和 `ship-frontend-design`。
   - 保持 B/D scenario 仍跳过 `ship-discover` 与 `ship-shape`。

3. 增加测试：
   - 创建 `scenario=greenfield, project_scope=backend_only` 的 feature meta 后，断言 `ship-shape.status == skipped`。
   - 构造 A + backend_only，已有 `product-brief.md` / `requirements.md` 等必要产物但无 `design-brief.md`，检查推进不会因 `ship-shape` 缺失失败。

### 3.5 验收标准

- A + `backend_only` 不再要求 `design-brief.md`。
- C + `backend_only` 同样不要求 `design-brief.md`。
- `fullstack/frontend_only` 的 `ship-shape` 行为不变。

## 4. 修改项二：落地 `fast-track` 可执行路径

### 4.1 问题

协议和 orchestrator 文档允许 `fast-track` 最小路径：

```text
ship-define -> ship-define-review -> ship-build -> ship-verify -> ship-handoff
```

场景 A/C 的 fast-track 需要先经过 `ship-discover`，但默认跳过 `ship-shape`。

实际脚本缺口：

- `stage_transition_check.py` 不读取 `pipeline_mode`，仍按 standard 路径要求前置设计/计划产物。
- `build_task_preflight.py` 只读 `frontend-plan.md/backend-plan.md`，不支持文档中写的 `lightweight task source`。
- `lightweight task source` 没有明确文件名、格式、validator 和创建职责。

### 4.2 目标行为

`pipeline_mode: fast-track` 时：

- 允许从 `ship-define-review` 通过后直接进入 `ship-build`。
- 不要求 `tech-research.md`、`tech-selection.md`、`api-contract.md`、`frontend-design.md`、`backend-design.md`、`review-design.md`、`frontend-plan.md`、`backend-plan.md`、`review-plan.md`。
- `ship-build` 有明确轻量任务事实源。
- `build_task_preflight.py` 能校验轻量任务事实源中的单 `DOING`、AC refs、allowed files、verification command。

### 4.3 轻量任务事实源设计

建议新增文件：

```text
fast-track-tasks.md
```

放在 feature 根目录，与 `requirements.md` 同级。

frontmatter：

```yaml
---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---
```

任务条目沿用 `ship-build` 已支持的格式：

```markdown
### Task FT-001: 修复登录按钮状态
- status: DOING
- allowed_files:
  - src/pages/Login.tsx
- ac_refs:
  - AC-AUTH-001
- verification_command: pnpm test -- Login
- evidence:
  - pending
```

说明：

- `fast-track-tasks.md` 是 build 阶段任务事实源，不新增 canonical stage。
- `stage_status` 只描述任务源准备状态；build 完成仍以 `meta.yml.stages.ship-build.tasks_done/tasks_total/status` 汇总。
- fast-track 若升级回 standard，保留该文件作为历史证据，但后续任务源切回 plan 文档。

### 4.4 涉及文件

- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `skills/ship-orchestrator/_templates/meta/meta.yml.template`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-build/SKILL.md`
- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/build_task_preflight.py`
- `skills/ship-orchestrator/scripts/validate_feature_artifacts.py`
- `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
- `skills/ship-orchestrator/scripts/test_spec_runtime.py`

### 4.5 修改步骤

1. 在共享协议中明确 `fast-track-tasks.md`：
   - 文件名。
   - frontmatter。
   - 任务格式。
   - ownership：由 `ship-define-review` 通过后或进入 `ship-build` 前创建，主上下文维护。

2. 修改 `ship-build/SKILL.md`：
   - 把 `lightweight task source` 改成明确的 `fast-track-tasks.md`。
   - 修改 Task Readiness Preflight 命令，增加 `--pipeline-mode <standard|fast-track>`。
   - 明确 fast-track 下不读 plan 文档。

3. 修改 `build_task_preflight.py`：
   - 增加 `--pipeline-mode` 参数，默认 `standard`。
   - `standard`：保持现有按 `project_scope` 读取 plan 的逻辑。
   - `fast-track`：只读取 `fast-track-tasks.md`。
   - 校验规则复用当前 DOING 检查。

4. 修改 `stage_transition_check.py`：
   - 读取 `meta.yml.pipeline_mode`。
   - 当目标阶段为 `ship-build`、`ship-verify`、`ship-handoff` 且 `pipeline_mode=fast-track` 时，required previous stages 使用 fast-track 最小路径。
   - B/D fast-track：required previous stages 至少包含 `ship-define`、`ship-define-review`。
   - A/C fast-track：required previous stages 至少包含 `ship-discover`、`ship-define`、`ship-define-review`，并跳过 `ship-shape`。

5. 修改 `validate_feature_artifacts.py`：
   - 在 `pipeline_mode=fast-track` 时，不因为缺少 design/plan/review-plan 产物报错。
   - 若存在 `fast-track-tasks.md`，校验 frontmatter stage / artifact_role / stage_status。
   - 不影响 standard 路径对 plan 产物的要求。

6. 增加测试：
   - B + fast-track：无 design/plan 产物，`check_transition(..., "ship-build")` 允许通过。
   - A + fast-track：有 `product-brief.md`、无 `design-brief.md`，仍允许从 define-review 后进入 build。
   - fast-track build preflight 读取 `fast-track-tasks.md` 并检查单 DOING。
   - standard build preflight 行为不变。

### 4.6 验收标准

- fast-track 不再被 standard 前置阶段阻断。
- fast-track 有明确任务事实源。
- standard 路径的 plan 校验不退化。
- 现有 63 个测试继续通过，并新增 fast-track 覆盖。

## 5. 修改项三：修正 soft gate 的 `stage_status` 文案

### 5.1 问题

orchestrator soft gate 写了：

```text
stage_status: draft / in_progress
```

但共享协议和 validator 规定非 review artifact frontmatter 只允许：

```text
draft / ready / complete
```

`in_progress` 是 `meta.yml.stages.<stage>.status` 的摘要状态，不是 artifact frontmatter 的 `stage_status`。

### 5.2 目标行为

所有 workflow 文档中：

- artifact frontmatter 使用 `stage_status: draft | ready | complete`。
- meta 摘要状态使用 `status: pending | in_progress | ready | blocked | completed | skipped`。
- soft gate 文案不再把 `in_progress` 写成 artifact frontmatter 值。

### 5.3 涉及文件

- `skills/ship-orchestrator/SKILL.md`
- 视搜索结果同步其他 `SKILL.md` / README / protocol。

### 5.4 修改步骤

1. 全局搜索：

```bash
rg -n "stage_status: .*in_progress|stage_status.*in_progress|draft / in_progress|draft / ready / complete" skills README.md
```

2. 修改 `ship-orchestrator/SKILL.md` soft gate：

建议改为：

```text
1. 检查上游文档 frontmatter 中 stage_status 字段。
2. stage_status: ready 或 complete -> 允许推进。
3. stage_status: draft -> 提示用户当前阶段未完成，询问是否允许软门禁强制推进。
4. 若 meta.yml.stages.<stage>.status 为 in_progress/blocked，但 artifact 已 ready，以 artifact frontmatter 为事实源并回写 meta.yml。
5. 上游文档不存在 -> 阻断，路由回上游阶段。
```

3. 若其他文档也有同类混用，一并修正。

4. 增加或更新 `validate_workflow_docs.py` 检查：
   - 禁止出现 `stage_status: draft / in_progress`。
   - 禁止出现把 `in_progress` 作为 artifact `stage_status` 值的表达。

### 5.5 验收标准

- `rg` 不再搜到 artifact `stage_status` 与 `in_progress` 的混用。
- `validate_workflow_docs.py` 可以防止该问题回归。

## 6. 修改项四：修正 `ship-build` 入口条件字段

### 6.1 问题

`ship-build/SKILL.md` 的 When to Use 写：

```text
ship-plan-review 已通过（stage_status: ready）
```

但 `ship-plan-review` 是 hard gate，事实字段应为：

```text
review_status: approved
user_sign_off: non-empty
signed_at: non-empty
```

### 6.2 目标行为

`ship-build` 入口条件与 hard gate contract 一致。

standard 模式：

- `review-plan.md.review_status = approved`
- `review-plan.md.user_sign_off` 非空
- `review-plan.md.signed_at` 非空

fast-track 模式：

- `review-define.md.review_status = approved`
- `review-define.md.user_sign_off` 非空
- `review-define.md.signed_at` 非空
- `fast-track-tasks.md` 已准备好，或进入 build 前创建。

### 6.3 涉及文件

- `skills/ship-build/SKILL.md`
- `skills/ship-orchestrator/SKILL.md`
- `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `skills/ship-orchestrator/scripts/stage_transition_check.py`
- `skills/ship-orchestrator/scripts/validate_workflow_docs.py`

### 6.4 修改步骤

1. 修改 `ship-build/SKILL.md` When to Use。
2. 在 `ship-build` 的 Scope Adaptation 中补充 standard / fast-track 各自入口 gate。
3. 在 `validate_workflow_docs.py` 增加文本检查：
   - `ship-build/SKILL.md` 不应出现 `ship-plan-review 已通过（stage_status: ready）`。
   - 应出现 `review_status: approved`、`user_sign_off`、`signed_at`。
4. 若修改项二已经调整 `stage_transition_check.py`，同步覆盖 standard / fast-track gate 判断。

### 6.5 验收标准

- 文档不再误导 agent 查 `stage_status`。
- transition checker 与文档入口条件一致。

## 7. 修改项五：补齐 README 的场景 D

### 7.1 问题

`skills/README.md` 的表格列出 A/B/C/D 四类入口，但默认原则写成：

```text
orchestrator 自动识别场景（A/B/C）并路由到正确的起点
```

漏掉 D，会弱化 PRD Direct 的正式入口地位。

### 7.2 目标行为

README 默认原则应写：

```text
orchestrator 自动识别场景（A/B/C/D）并路由到正确的起点
```

### 7.3 涉及文件

- `skills/README.md`
- 可选：`README.md` 中若有类似概括，也一并核对。

### 7.4 修改步骤

1. 修改 `skills/README.md` 默认原则。
2. 全局搜索 `A/B/C`，确认是否还有漏 D 的 workflow 入口概括。
3. 若发现只面向旧三场景的表述，按语义判断是否改成 A/B/C/D。

### 7.5 验收标准

- PRD Direct 在 README 中和其他三类入口同等呈现。
- `validate_workflow_docs.py` 继续通过。

## 8. 推荐实施顺序

### Step 1：修小文案但加回归检查

先修修改项三、四、五。

验证：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
rg -n "stage_status: .*in_progress|draft / in_progress|A/B/C\\)" skills README.md
```

预期：

- 文案合同无混用。
- README 覆盖 A/B/C/D。

### Step 2：修 `backend_only` shape skip

修改 runtime + transition checker + tests。

验证：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

预期：

- A/C + `backend_only` 不再要求 `ship-shape`。
- 现有 scope 测试不回退。

### Step 3：落地 fast-track

先定 `fast-track-tasks.md` 合同，再改 preflight / transition / feature validation / tests。

验证：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 -m unittest skills/ship-orchestrator/scripts/test_spec_runtime.py
```

建议额外做一个临时 feature fixture smoke：

```bash
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <tmp-feature-dir> --target-stage ship-build --json
python3 skills/ship-orchestrator/scripts/build_task_preflight.py <tmp-feature-dir> --pipeline-mode fast-track --json
```

预期：

- fast-track fixture 无 design/plan 产物也能进入 build。
- `fast-track-tasks.md` 中恰好一个 DOING 时 preflight 通过。

## 9. 风险与注意事项

### 9.1 fast-track 不能变成“无计划编码”

风险：

- 如果 `fast-track-tasks.md` 过于宽松，会把 fast-track 变成绕过治理。

控制：

- `fast-track-tasks.md` 必须至少包含 task id、status、allowed_files、AC refs、verification command。
- build preflight 必须阻断缺少这些字段的 DOING task。
- `ship-define-review` 仍不可跳过。

### 9.2 不要破坏 standard 路径

风险：

- 为了 fast-track 裁剪 artifact requirement，误让 standard 缺 design/plan 也通过。

控制：

- `validate_feature_artifacts.py` 根据 `pipeline_mode` 分支。
- standard 测试必须继续覆盖缺失 plan/design 的失败路径。

### 9.3 `backend_only` skip 不应影响 `frontend_only`

风险：

- 把 `ship-shape` 普遍跳过，导致 frontend-only 的 UI 探索丢失。

控制：

- skip 规则只绑定 `backend_only`。
- 增加 `frontend_only` 下 `ship-shape` 不被 scope skip 的测试。

## 10. 最终复查清单

修改完成后逐项复查：

- [ ] `skills/README.md` 默认原则写 A/B/C/D。
- [ ] `ship-orchestrator/SKILL.md` soft gate 没有把 `in_progress` 写成 artifact `stage_status`。
- [ ] `ship-build/SKILL.md` When to Use 使用 `review_status: approved + user_sign_off + signed_at`。
- [ ] `feature_meta_runtime.py` 的 `backend_only` 会跳过 `ship-shape` 和 `ship-frontend-design`。
- [ ] `stage_transition_check.py` 支持 `backend_only` 跳过 `ship-shape`。
- [ ] `stage_transition_check.py` 支持 `pipeline_mode=fast-track` 的 required previous stages。
- [ ] `build_task_preflight.py` 支持 `--pipeline-mode fast-track` 并读取 `fast-track-tasks.md`。
- [ ] `validate_feature_artifacts.py` 不让 fast-track 被缺失 design/plan 误阻断，同时不放松 standard。
- [ ] 新增测试覆盖 5 个修复点。
- [ ] `python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py` 通过。
- [ ] `python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py` 通过。

## 11. 建议提交粒度

建议分 3 个 commit 或 3 个实施批次：

1. `docs: fix workflow wording regressions`
   - 修改项三、四、五。
   - 增加 docs validator 防回归。

2. `fix: align backend-only shape skip runtime`
   - 修改项一。
   - 增加 backend_only shape skip 测试。

3. `feat: implement fast-track task source`
   - 修改项二。
   - 新增 `fast-track-tasks.md` 合同、preflight 支持和 transition tests。

若希望一次性落地，也应按上述顺序在同一分支内推进，避免 fast-track 代码改动和简单文案修复互相掩盖。
