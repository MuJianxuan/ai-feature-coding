# ship-* skills 一致性审计

更新时间：2026-05-24

## 审计目标

本审计用于梳理当前仓库内所有 `ship-*` 技能、共享协议、运行时 helper 与校验脚本之间的语义一致性，识别以下问题：

- 阶段数量、阶段命名、默认展示口径是否一致
- scenario / scope / fast-track 是否在各阶段中闭环
- delegation / spec hook / gate / ownership 是否在文档和运行时中一致
- 已有校验脚本是否覆盖真实协议，而不是旧口径

## 当前证据范围

已读取并核对：

- `../README.md`
- `README.md`
- `ship-*/SKILL.md`
- `ship-orchestrator/_templates/protocol/workflow-protocol.md`
- `ship-orchestrator/_templates/meta/meta.yml.template`
- `ship-orchestrator/_templates/README.md`
- `ship-orchestrator/_templates/review/review.md.template`
- `ship-contract/references/api-contract-template.md`
- `ship-frontend-design/references/frontend-design-template.md`
- `ship-backend-design/references/backend-design-template.md`
- `ship-discover/references/product-brief-template.md`
- `ship-shape/references/design-brief-template.md`
- `ship-shape/references/anti-slop-checklist.md`
- `ship-shape/references/design-direction-library.md`
- `ship-shape/references/wireframe-starter/index.html`
- `ship-shape/references/wireframe-starter/variant-template.html`
- `ship-orchestrator/scripts/workflow_stage_map.py`
- `ship-orchestrator/scripts/feature_meta_runtime.py`
- `ship-orchestrator/scripts/spec_runtime.py`
- `ship-orchestrator/scripts/validate_workflow_docs.py`
- `ship-orchestrator/scripts/test_spec_runtime.py`

已运行：

```bash
python3 ship-orchestrator/scripts/validate_workflow_docs.py
```

结果：`workflow docs validation: OK`。

注意：该结果只能证明当前脚本断言通过，不能证明整套协议无冲突。脚本本身存在旧口径断言，见问题 A-005。

补充验证：

```bash
/Users/rao/.pyenv/shims/python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'
```

结果：21 个测试通过。

注意：当前通过的测试命令是从仓库根运行 `python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'`；已确认与 `validate_workflow_docs.py` 同步通过。

## 已确认的设计事实

### F-001: 当前运行时 stage map 是 14 个 canonical stages

证据：

- `ship-orchestrator/scripts/workflow_stage_map.py` 中 `CANONICAL_STAGE_ORDER` 包含：
  `ship-discover`, `ship-shape`, `ship-define`, `ship-define-review`, `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review`, `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify`, `ship-handoff`
- `ship-orchestrator/scripts/validate_workflow_docs.py` 中 `validate_stage_map_script()` 明确断言 `len(CANONICAL_STAGE_ORDER) == 14`

### F-002: `ship-discover` / `ship-shape` 是条件性 pre-Define stages

证据：

- `workflow-protocol.md` 明确 `ship-discover` 和 `ship-shape` 是条件性前置阶段，仅场景 A/C 激活
- `ship-orchestrator/SKILL.md` 的 scenario detection 也把 A/C 路由到 `ship-discover`，B/D 跳过 Discover

### F-003: `ship-spec` 是 utility，不是 canonical stage

证据：

- `ship-spec/SKILL.md` 写明不是 canonical stage，不进入 `workflow_stage_map.py`
- `workflow-protocol.md` 的 Spec Hook Contract 将其接入 `ship-tech-discovery / ship-frontend-design / ship-backend-design / ship-build / ship-handoff`

### F-004: `verification.md` 是 `ship-verify` 与 `ship-handoff` 的共享产物

证据：

- `workflow-protocol.md` 的 Testing / Handoff Ownership 明确：
  - `ship-verify` 创建或更新 `verification.md`，写自动化测试结果，验证通过后置为 `ready`
  - `ship-handoff` 补齐 AC 映射、残余风险和最终结论，完成后置为 `complete`
- `ship-verify/SKILL.md` 与 `ship-handoff/SKILL.md` 的 frontmatter 均以该共享模型描述

结论：这不是冲突，不应修成两个独立文件。

## 待确认问题

### A-001: macro stage 数量口径混乱

状态：需要用户确认修复方向。

现象：

- `README.md` 开头写“对外默认只展示 5 个大阶段（Discover 可选）”
- `README.md` 后续又写“首屏只讲一个入口和四个大阶段”
- `ship-orchestrator/SKILL.md` 写“4 个大阶段视图”，但下方 Stage Routing Rules 写“5 个大阶段，Discover 可选”
- `workflow-protocol.md` 写“对外默认展示四个大阶段”，但表格实际包含 `discover / define / design / build / close` 5 行
- `ship-orchestrator/_templates/README.md` 写 `macro_stage` 是“4 大阶段摘要”
- `../README.md` 仍把默认视图写成 `Define → Design → Build → Close` 4 个大阶段，且维护检查要求“默认视图仍然是 4 大阶段”

建议决策：

统一为：`[Discover →] Define → Design → Build → Close`，即 5 个 macro stages，其中 Discover 是条件性展示阶段。

影响：

- 需要同步 `README.md`
- 需要同步 `ship-orchestrator/SKILL.md`
- 需要同步 `workflow-protocol.md`
- 需要同步 `ship-orchestrator/_templates/README.md`
- 需要同步 `validate_workflow_docs.py` 中旧的“4 大阶段”断言

### A-002: canonical stage 数量口径混乱

状态：需要用户确认修复方向。

现象：

- 运行时和协议主体已是 14 个 canonical stages
- `../README.md` 仍写“内部 canonical stages 从 14 个收敛到 12 个”
- `README.md` 仍残留“12 个 canonical stages”和“完整 12 阶段路由顺序”
- `ship-orchestrator/SKILL.md` 仍写“用户无需记住 12 个内部阶段名”

建议决策：

统一为：14 个 canonical stages，前 2 个为条件性 pre-Define stages。

影响：

- 更新 README / orchestrator 文案
- 更新 `_templates/README.md` 中硬门禁阶段编号说明（见 A-006）
- 增加校验脚本对旧“12 阶段”文案的禁止断言

### A-003: delegation runtime 缺少 `ship-discover` / `ship-shape`

状态：确认后可直接修复。

现象：

- `workflow-protocol.md` Delegation Matrix 和 canonical node id 表包含 `ship-discover` / `ship-shape`
- `ship-discover/SKILL.md` 和 `ship-shape/SKILL.md` 都定义了 `Delegation Boundary`
- `feature_meta_runtime.py` 的 `CANONICAL_DELEGATION_NODES` 没有 `ship-discover` / `ship-shape`

影响：

- `resolve_delegation("ship-discover", ...)` 或 `resolve_delegation("ship-shape", ...)` 会报 unknown node
- `validate_workflow_docs.py` 目前通过，是因为它只检查 runtime registry 中已有 node 是否出现在协议里，没有反向检查协议 node 是否出现在 runtime registry

建议修复：

- 在 `feature_meta_runtime.py` 中补充两个 `assistive_only` node
- 在 `test_spec_runtime.py` 增加覆盖
- 在 `validate_workflow_docs.py` 增加 `ship-discover` / `ship-shape` 的 runtime registry 覆盖断言

### A-004: project_scope 单侧模式适配不完整

状态：需要确认 `ship-contract` 的范围语义后修复。

已对齐部分：

- `workflow-protocol.md` 定义了 `project_scope: fullstack | backend_only | frontend_only`
- `ship-design-review/SKILL.md` 有 Scope Adaptation
- `ship-delivery-plan/SKILL.md` 有 Scope Adaptation
- `ship-plan-review/SKILL.md` 有 Scope Adaptation
- `meta.yml.template` 有 `project_scope` 和 skipped 状态字段
- `feature_meta_runtime.py` 有 `SCOPE_SKIP_MAP`

不完整部分：

- `ship-verify/SKILL.md` 没有 Scope Adaptation；退出 checklist 硬性要求前后端测试全通过
- `ship-build/SKILL.md` 仍按 frontend-plan + backend-plan 双 plan 描述，没有明确单侧任务消费规则
- `ship-orchestrator/SKILL.md` 阶段表中 `ship-design-review` / `ship-delivery-plan` / `ship-plan-review` 仍按 fullstack 文档集合描述

待确认点：

`ship-contract` 当前协议说所有 scope 默认保留，但 `ship-contract/SKILL.md` 的 When NOT to Use 又说“纯前端项目（无后端交互）无需接口规约”。需要确认 frontend_only 的 contract 语义：

- 方案 1：frontend_only 仍保留 `ship-contract`，用于描述外部 API / consumer contract；仅“完全无 API 交互”时显式简化或跳过
- 方案 2：frontend_only 默认跳过 `ship-contract`，但这会连带影响 frontend-design / design-review / plan-review 的入口条件

建议采用方案 1，因为现有协议已声明 `ship-contract` 在所有 scope 下默认保留。

### A-005: 校验脚本通过但断言目标过期

状态：确认 A-001/A-002 后可修复。

现象：

- `validate_workflow_docs.py` 运行通过
- 但 `validate_root_readme_commands()` 读取的是仓库上级 `../README.md`，并仍要求其包含“4 大阶段”
- 该脚本未禁止 README 中出现“12 个 canonical stages / 12 阶段”
- 该脚本未反向验证协议 canonical delegation node ids 与 runtime registry 完全一致

建议修复：

- 改为验证 5-stage wording
- 增加旧口径禁用断言
- 增加 protocol node id 与 runtime node id 的双向一致性校验

进一步审计发现的覆盖盲区：

- 脚本 docstring 仍写“4-stage default view”
- `validate_protocol_doc()` 只检查 `CANONICAL_DELEGATION_NODES` 中的 runtime node 是否出现在协议，不检查协议表里的 canonical node 是否都存在于 runtime registry；因此 A-003 没被拦住
- `validate_stage_delegation_boundaries()` 的 stage_skill_paths 不包含 `ship-discover` / `ship-shape`，因此前置阶段缺失或偏离 delegation boundary 不会被发现
- `validate_readmes()` 只检查 Define/Design/Build/Close 是否出现，不检查 Discover 是否作为条件性 macro stage 出现
- `validate_root_readme_commands()` 明确要求 “4 大阶段” 文案，因此会鼓励旧口径继续存在
- 没有检查 `../README.md` / `README.md` / `SKILL.md` 中是否残留 “12 个 canonical stages / 12 阶段”
- 没有检查 `ship-verify` 是否实现协议要求的 `Scope Adaptation`
- 没有检查 `feature_meta_runtime.py init` 是否按 scenario 初始化 `current_stage`

建议新增校验：

- `validate_macro_stage_wording()`：要求 5-stage / `[Discover →] Define → Design → Build → Close`，禁止“4 大阶段”旧口径
- `validate_no_legacy_stage_count_wording()`：禁止“12 个 canonical stages / 12 阶段”出现在 README / orchestrator 主文档
- `validate_delegation_registry_bidirectional()`：协议 canonical node id 与 runtime registry 双向一致
- `validate_scope_adaptation_sections()`：协议列出的受 scope 影响阶段必须有 `## Scope Adaptation`
- `validate_feature_meta_init_contract()`：用临时目录初始化 4 种 scenario，验证 current_stage / skipped / generation_mode / macro_stage

### A-006: review template 阶段编号注释过期

状态：可直接修复，低风险。

现象：

- `ship-orchestrator/_templates/README.md` 写 `review.md.template` 是“02/08/11 阶段共用”
- 当前 canonical stage 表中 hard gate 是 02 / 07 / 09：
  - `ship-define-review`
  - `ship-design-review`
  - `ship-plan-review`

建议修复：

改为不写易漂移的编号，直接写三阶段名。

### A-007: 测试入口依赖 PATH / 工作目录，缺少稳定说明

状态：可直接修复，低风险。

现象：

- 从仓库根执行 `python3 -m unittest ship-orchestrator/scripts/test_spec_runtime.py` 会因为 `feature_meta_runtime` 的同目录 import 不在 `sys.path` 中失败
- 从 `ship-orchestrator/scripts` 目录执行 `python3 -m unittest test_spec_runtime.py` 会解析到 `/opt/homebrew/bin/python3`，该环境缺少 `yaml`
- 从仓库根执行 `/Users/rao/.pyenv/shims/python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'` 可以通过 14 个测试
- 仓库中没有 `requirements.txt` / `pyproject.toml` / `uv.lock` 等 Python 依赖声明

影响：

- 维护者可能以不同工作目录或 Python 解释器运行测试，得到互相矛盾的结果
- `validate_workflow_docs.py` 和 runtime helper 都依赖 PyYAML，但依赖没有在仓库内显式声明

建议修复：

- 在 README 维护章节给出唯一推荐测试命令：从仓库根运行 `python3 -m unittest discover -s ship-orchestrator/scripts -p 'test_*.py'`
- 增加 Python 依赖声明（例如 `requirements.txt`，至少包含 `PyYAML`），或在 README 明确依赖 PyYAML
- 可选：调整 `test_spec_runtime.py` 的 import setup，使它从仓库根和脚本目录都稳定运行

### A-008: `ship-define` / `ship-define-review` 描述仍称第 1/2 阶段

状态：需要与 A-002 一起修复。

现象：

- `ship-define/SKILL.md` description 写 `ShipKit stage 1 (Define)`
- `ship-define/SKILL.md` Overview 写“需求定义是开发工作流的第一个阶段”
- `ship-define-review/SKILL.md` Overview 写“需求评审是开发工作流的第二个阶段”

分析：

在场景 B/D 直接进入 Define 时，这种说法可理解；但在完整 14-stage 协议中，`ship-discover` / `ship-shape` 已是条件性前置阶段，因此“第一个/第二个阶段”容易与 canonical stage order 冲突。

建议修复：

改为“Define 大阶段的核心阶段 / Define 大阶段的硬门禁”，避免使用绝对序号。

### A-009: NEW_FEATURE 初始化链路没有按 scenario 设置起点 stage

状态：需要用户确认 scenario 初始化策略后修复。

现象：

- `ship-orchestrator/SKILL.md` 和 `workflow-protocol.md` 都定义：
  - 场景 A/C 起点为 `ship-discover`
  - 场景 B/D 起点为 `ship-define`
- `ship-orchestrator/SKILL.md` 的 Feature Directory Initialization 却固定写“current_stage: ship-define”
- `feature_meta_runtime.py create_feature_meta()` 固定执行 `data["current_stage"] = "ship-define"`
- `feature_meta_runtime.py init` CLI 没有 `--scenario` 参数，也没有按 scenario 设置 `stages.ship-discover.discovery_mode`、`stages.ship-define.generation_mode`、B/D skipped 状态等完整初始化

运行验证：

```bash
python3 ship-orchestrator/scripts/feature_meta_runtime.py init /private/tmp/ship-audit-demo --feature-name Demo --feature-id feature-demo
```

结果摘要：

```yaml
current_stage: ship-define
scenario: ''
macro_stage:
  current: define
stages:
  ship-discover:
    status: pending
```

影响：

- 对场景 A/C，如果使用 helper 初始化，会直接定位到 `ship-define`，绕开 `ship-discover`
- `current_stage=ship-define` 与 `stages.ship-discover.status=pending` 同时存在，恢复时可能出现“当前在 Define，但 Discover 还 pending”的不一致
- B/D 的 skipped 与 generation mode 也主要停留在文档流程描述，helper 没有显式实现

建议修复：

- `feature_meta_runtime.py init` 增加 `--scenario greenfield|product_provided|prd_direct|evolve`
- 按 scenario 计算初始 `current_stage`：
  - `greenfield/evolve` → `ship-discover`
  - `product_provided/prd_direct` → `ship-define`
- 初始化对应 stage 摘要：
  - A/C：`stages.ship-discover.discovery_mode`
  - B/D：`stages.ship-discover.status = skipped`、`stages.ship-shape.status = skipped`
  - B：`stages.ship-define.generation_mode = interview`
  - D：`stages.ship-define.generation_mode = prd_direct`
- `ensure_macro_stage()` 根据初始 current_stage 自动刷新 macro stage
- 增加单元测试覆盖 4 种 scenario

待确认点：

是否允许 `--scenario` 必填？建议必填，因为 orchestrator 协议已要求 NEW_FEATURE 启动确认前必须先判定 scenario；对旧调用可临时默认 `product_provided` 或 `greenfield`，但会隐含业务判断。

### A-010: fast-track 最小路径与 `ship-build` 入口条件冲突

状态：需要用户确认 fast-track 下 build 的任务来源。

现象：

- `workflow-protocol.md` 定义 fast-track 最小路径为：
  `ship-define → ship-define-review → ship-build → ship-verify → ship-handoff`
- `workflow-protocol.md` 还明确“若未生成设计/计划文档，必须在启动确认或需求评审中明确记录 fast-track 原因和风险”
- `ship-orchestrator/SKILL.md` 同样写 fast-track 允许不生成设计/计划产物
- 但 `ship-build/SKILL.md` 的 When to Use 要求：
  - `frontend-plan.md` 和 `backend-plan.md` 已通过 plan-review gate
  - plan 尚未通过评审则回到 `ship-plan-review`
- `ship-build/SKILL.md` 的执行循环也以 plan.md 任务列表为唯一任务来源

影响：

- 按 fast-track 最小路径推进时，没有 `frontend-plan.md` / `backend-plan.md` / `review-plan.md`，`ship-build` 却无法合法进入
- “允许不生成计划产物”与“build 只消费计划产物”构成直接流程断裂

可选修复方向：

1. **fast-track 仍要求轻量计划产物**：不跳过 `ship-delivery-plan / ship-plan-review`，只把它们简化。这会推翻现有最小路径，但保持 build 模型简单。
2. **fast-track 为 build 定义轻量任务源**：例如 `requirements.md` / `review-define.md` 中的 Fast-Track Task List，或在 `meta.yml` 增加 `fast_track_tasks`，并规定 `ship-build` 在 `pipeline_mode=fast-track` 时消费该任务源。
3. **fast-track 入口前自动生成临时 plan**：由 orchestrator 在进入 build 前生成最小 `frontend-plan.md` / `backend-plan.md` 或单侧 plan，并记录跳过正式 plan-review 的风险。这需要重新定义硬门禁是否真的被跳过。

建议倾向：

采用方案 2：保留 fast-track 的最小路径，同时给 `ship-build` 一个受控的轻量任务源；但需要定义任务状态、DoD、AC 映射和验证证据如何记录，不能让 fast-track 变成无计划编码。

待确认点：

fast-track 是否应该真的跳过 `ship-delivery-plan / ship-plan-review`？如果是，需要确认轻量任务源放在哪里。

### A-011: `project_scope=backend_only` 初始化后 `ship-delivery-plan.current_part` 仍为 frontend

状态：可与 A-004 一起修复。

现象：

- `meta.yml.template` 注释写：
  `ship-delivery-plan.current_part`: `fullstack: frontend|backend|sync; backend_only: backend; frontend_only: frontend`
- `ship-delivery-plan/SKILL.md` 的 Scope Adaptation 也定义：
  - `backend_only` 子段序列为 `backend`
  - `frontend_only` 子段序列为 `frontend`
- `feature_meta_runtime.py apply_scope_skips()` 只设置被跳过设计阶段的 status，没有同步 `ship-delivery-plan.current_part`

运行验证：

```bash
python3 ship-orchestrator/scripts/feature_meta_runtime.py init /private/tmp/ship-audit-backend-only --feature-name BackendOnly --feature-id feature-backend-only --project-scope backend_only
```

结果摘要：

```yaml
project_scope: backend_only
stages:
  ship-frontend-design:
    status: skipped
  ship-delivery-plan:
    current_part: frontend
```

影响：

- backend-only feature 恢复到 delivery-plan 时，会从不存在的 frontend 子段开始
- 与 scope contract 的“单侧模式下不产出缺失侧 plan 文件”冲突

建议修复：

- 在 `apply_scope_skips()` 或 feature init 中根据 scope 设置：
  - `backend_only` → `stages.ship-delivery-plan.current_part = backend`
  - `frontend_only` → `stages.ship-delivery-plan.current_part = frontend`
  - `fullstack` → `frontend`
- 增加单元测试覆盖 `backend_only` / `frontend_only`

### A-012: 单侧 scope 下 orchestration 文案仍默认询问“并行启动前后端设计”

状态：可与 A-004 一起修复。

现象：

- `workflow-protocol.md` 允许前后端设计按各自 `node_id` 独立决策，且 scope contract 会跳过缺失侧
- `ship-orchestrator/SKILL.md` 节点级行为仍写：
  `ship-contract` 完成后：默认询问是否并行启动前后端设计子代理

影响：

- 对 `backend_only` / `frontend_only` feature，用户可能被问到一个不适用的“双侧并行”问题
- 与 `project_scope` 的 skipped 机制语义不一致

建议修复：

改为 scope-aware 描述：

- `fullstack`：询问是否并行启动前后端设计，或分别设置 `ship-frontend-design` / `ship-backend-design`
- `backend_only`：仅进入 `ship-backend-design`，不询问前端设计
- `frontend_only`：仅进入 `ship-frontend-design`，不询问后端设计

### A-013: `ship-contract` 的 scope 语义在协议和技能内冲突

状态：需要用户确认 contract 在“无 API / 无后端交互”场景下的权威规则。

现象：

- `workflow-protocol.md` 明确：
  `ship-contract` 在所有 scope 下默认保留（后端 API 需要契约给消费者，前端需要契约描述所消费的外部 API）
- `workflow-protocol.md` Conditional Stages 表也写 `ship-contract` 在 `fullstack / backend_only / frontend_only` 下均 active
- `ship-orchestrator/SKILL.md` Scope Detection 也写 `ship-contract` 在所有 scope 下默认保留
- 但 `ship-contract/SKILL.md` When NOT to Use 写：
  - 纯前端项目（无后端交互）—— 无需接口规约
  - 纯后端批处理/定时任务 —— 使用后端设计阶段直接定义

影响：

- 如果“无后端交互纯前端”或“纯后端批处理”出现，协议层没有 `ship-contract` 的 skip 机制，stage map 仍要求进入 contract
- 若按 `ship-contract/SKILL.md` 跳过 contract，下游 `ship-frontend-design / ship-backend-design / ship-design-review / ship-build` 仍普遍以 `api-contract.md` 为入口或事实源

可选修复方向：

1. **保留 active，但允许 empty/internal contract**：所有 scope 仍生成 `api-contract.md`，无 API 时写“无接口/无外部调用”，后端批处理写输入/输出/任务契约。这最符合现有协议。
2. **新增 `no_api` 或 `worker_only` scope**：明确跳过 contract，并系统性调整下游入口条件。这是更大协议改动。
3. **允许 soft skip contract**：通过 `skip_log` 跳过，但所有下游必须声明无 contract 时的替代事实源。

建议倾向：

采用方案 1：保留 `ship-contract` 作为“交互边界契约”，不局限于前后端 HTTP API；无 API 时产出一个显式空契约，避免下游引用缺失。

### A-014: `ship-verify` 没有实现协议要求的 scope 裁剪

状态：可与 A-004 一起修复。

现象：

- `workflow-protocol.md` Verify Track Adaptation 定义：
  - `backend_only` 跳过 frontend component / E2E 轨道
  - `frontend_only` 跳过 backend unit / integration / contract 轨道
  - `fullstack` 所有轨道可用
- `ship-verify/SKILL.md` 没有 `## Scope Adaptation` 节
- `ship-verify/SKILL.md` 的退出 checklist 硬性要求：
  - 后端单元测试通过率 100%
  - 后端集成测试通过率 100%
  - 后端契约测试通过率 100%
  - 前端组件测试通过率 100%
  - E2E 关键路径通过率 100%

影响：

- `backend_only` feature 会被不适用的前端测试项阻塞
- `frontend_only` feature 会被不适用的后端测试项阻塞
- delegation node id 虽然列出了所有测试轨，但没有说明单侧模式如何标记 skipped / na

建议修复：

- 在 `ship-verify/SKILL.md` 增加 `## Scope Adaptation`
- 修改退出 checklist：缺失侧测试轨标记为 `N/A`，不计入通过率要求
- 规定 `verification.md` 中记录 skipped track 的原因和 `project_scope`
- `validate_workflow_docs.py` 增加对 scope-affected stages 的 `## Scope Adaptation` 检查

### A-015: AC / Domain ID 示例格式不一致，影响跨文档追踪

状态：可直接修复，低风险。

现象：

- `ship-define/SKILL.md` 定义 Domain ID 格式为 `D-{MODULE}-{NNN}`，示例为 `D-AUTH-001`
- `ship-define/SKILL.md` PRD Direct 示例中 AC ID 为 `AC-AUTH-001`，Domain 为 `D-AUTH-001`
- `ship-handoff/SKILL.md` 推荐 AC ID 格式为 `AC-{Domain}-{NNN}`
- `ship-orchestrator/_templates/meta/meta.yml.template` 的 `ac_index` 示例却写：
  - `id: AC-001`
  - `domain: TODO`
- 同一模板的 `domain_index` 示例写：
  - `id: TODO`
  而不是 `D-TODO-001` 或模块级 Domain ID
- `ship-plan-review/SKILL.md` 示例中使用 `AC-003`，没有 Domain segment

影响：

- `requirements.md` / `meta.yml.ac_index` / `verification.md` 之间的 AC 引用可能不一致
- `domain_index` 无法直接对应 `requirements.md` 中的 Domain ID
- 自动化校验 AC 覆盖、handoff AC 映射时，难以判断 `TODO` 与 `D-TODO-001` 是否同一对象

建议修复：

- 统一 Domain ID 示例为 `D-{MODULE}-{NNN}`，例如 `D-TODO-001`
- 统一 AC ID 示例为 `AC-{MODULE}-{NNN}` 或明确 `AC-{DomainSlug}-{NNN}`；建议采用现有 define/handoff 示例口径：`AC-AUTH-001`
- `meta.yml.template` 示例改为：
  - `ac_index[].id: AC-TODO-001`
  - `ac_index[].domain: D-TODO-001`
  - `domain_index[].id: D-TODO-001`
- `ship-plan-review/SKILL.md` 示例 `AC-003` 改为 `AC-ORD-003` 或同类格式
- 后续可在校验脚本中增加简单格式检查

### A-016: `record-spec-proposal` 的 source stage 约束过宽

状态：需要确认是否收紧运行时语义。

现象：

- `ship-spec/SKILL.md` 明确采用 Proposal-First Writeback：在 `ship-handoff` 阶段生成待沉淀 proposal
- `workflow-protocol.md` 也写明 `ship-handoff` hook 的用途是“汇总已引用规范并生成待沉淀 proposal”
- `feature_meta_runtime.py record_spec_proposal()` 不校验 `source_stage`
- CLI 参数 `record-spec-proposal --source-stage` 使用 `choices=VALID_STAGE_HOOKS`，因此允许：
  - `ship-tech-discovery`
  - `ship-frontend-design`
  - `ship-backend-design`
  - `ship-build`
  - `ship-handoff`
- 当前 `test_spec_runtime.py` 没有覆盖 `record_spec_proposal`

影响：

- 文档说“handoff 阶段统一生成 proposal”，运行时却允许任何 spec hook 阶段写入 pending proposal
- 后续如果用 `pending_proposals` 做验收闭环，可能出现 build/design 阶段提前沉淀 proposal，绕开 handoff 的 AC / 风险 / 交付上下文汇总

可选决策：

- 方案 1：收紧为仅允许 `source_stage=ship-handoff`
- 方案 2：保留多阶段 proposal，但改文档定义为“各 hook 阶段可提出候选，ship-handoff 统一审核归档”

建议采用方案 1，因为现有协议多处强调 `ship-handoff` 是 proposal writeback 的唯一归口。

### A-017: `spec_runtime.py` 的 path 输出隐含 `.docs/spec` 两级目录假设

状态：可直接修复，低风险。

现象：

- `_parse_spec()` 输出 `path=str(path.relative_to(spec_root.parent.parent))`
- 当 `spec_root=.docs/spec` 时，该逻辑正好输出 `.docs/spec/...`
- 但 CLI 允许自定义 `--spec-root`；如果 spec_root 不是 `.docs/spec` 形态，输出路径会相对 `spec_root.parent.parent`，得到不稳定路径
- 验证命令：

```bash
python3 - <<'PY'
from pathlib import Path
import tempfile, sys
sys.path.insert(0, 'ship-orchestrator/scripts')
from spec_runtime import scan_specs
root=Path(tempfile.mkdtemp(prefix='ship-spec-layout-'))
spec_root=root/'custom-spec'
spec_root.mkdir(parents=True)
(spec_root/'x.md').write_text('''---
spec_id: x
scope: project
stage_hooks:
  - ship-build
last_updated: ""
---
# x
''', encoding='utf-8')
print(scan_specs(spec_root))
PY
```

观察到 `path` 类似 `ship-spec-layout-.../custom-spec/x.md`，而不是稳定的 `custom-spec/x.md` 或绝对路径。

影响：

- `matched_specs[].path` 可能因 spec_root 布局不同而变化，影响任务证据、handoff 引用和测试断言
- 当前测试只覆盖 `.docs/spec` 默认布局，无法发现该假设

建议修复：

- 明确 helper 只支持 `.docs/spec`，并在 CLI / 文档中拒绝其他目录；或
- 增加 `project_root` 概念，默认取当前工作目录，输出相对 project root 的路径；或
- 输出相对 `spec_root` 的路径，并同时返回 `spec_root`

建议采用第二种：保留 `--spec-root` 灵活性，同时让证据路径稳定。

### A-018: `ship-handoff` 只定义 `verification.md` frontmatter，缺少 `handoff.md` frontmatter

状态：可直接修复，低风险。

现象：

- `workflow-protocol.md` 规定所有非评审阶段产物都有通用 frontmatter 最小集合
- `ship-handoff/SKILL.md` 的 Output 章节详细定义了 `verification.md Frontmatter`
- 同一章节只列出 `handoff.md 核心章节`，没有给出 `handoff.md Frontmatter`
- `ship-orchestrator/SKILL.md` 阶段表要求 `ship-handoff` 的输出判定为“`handoff.md` 完成且 `verification.md stage_status: complete`”，但没有 handoff.md 自身状态字段示例

影响：

- `handoff.md` 作为正式阶段产物没有统一 frontmatter 示例，和共享协议“阶段文档 frontmatter 是事实源”不完全闭环
- 恢复流程可能只能依赖 `verification.md` 判断 handoff 状态，而不能独立判断 `handoff.md` 是否完整

建议修复：

- 在 `ship-handoff/SKILL.md` 增加 `handoff.md Frontmatter`：
  - `stage: ship-handoff`
  - `stage_status: draft | complete`
  - `updated_at`
  - `all_ac_verified`
  - `referenced_spec_ids`
  - `spec_warnings`
- 明确 `verification.md.stage_status=complete` 与 `handoff.md.stage_status=complete` 都满足时，`meta.yml.stages.ship-handoff.status=completed`

### A-019: `verification.md` frontmatter 在 verify 与 handoff 两处定义不一致

状态：可直接修复，低风险。

现象：

- `workflow-protocol.md` 的 Spec Hook Contract 写：`ship-tech-discovery / ship-frontend-design / ship-backend-design / ship-handoff` 的相关产物 frontmatter 应包含 `spec_checked_at / referenced_spec_ids / spec_warnings`
- `ship-verify/SKILL.md` 的 `verification.md` frontmatter 只包含：
  - `stage`
  - `stage_status`
  - `updated_at`
  - `all_ac_verified`
- `ship-handoff/SKILL.md` 同样在 `verification.md` frontmatter 中包含这些字段
  - `spec_checked_at`
  - `referenced_spec_ids`
  - `spec_warnings`

影响：

- 同一个共享文件在两个阶段的 frontmatter 模型不一致
- `ship-verify` 创建文件后，`ship-handoff` 需要补字段；但协议没有说明这是增量补齐还是 verify 阶段遗漏
- 自动化校验难以判断 `verification.md` 缺少 spec 字段是否错误

建议修复：

- 统一共享 `verification.md` frontmatter：建议 `ship-verify` 创建时也预置 spec 字段为空值，`ship-handoff` 后续补齐
- 或明确 handoff 阶段会增量扩展 frontmatter，并在协议中说明 verify 阶段允许暂缺 spec 字段

### A-020: `ship-delivery-plan` 的 When NOT to Use 与 scope adaptation 冲突

状态：需要用户确认单侧 scope 下是否仍使用 `ship-delivery-plan`。

现象：

- `ship-delivery-plan/SKILL.md` 的 `When NOT to Use` 写：“仅有单端工作且无需双侧协同计划”时不用本阶段
- 同一文件的 `## Scope Adaptation` 又明确支持：
  - `backend_only`：产出 `backend-plan.md`
  - `frontend_only`：产出 `frontend-plan.md`
- `workflow-protocol.md` 的 `Project Scope Contract` 也把 `ship-delivery-plan` 定义为 scope-aware 阶段，而不是跳过阶段
- `ship-plan-review/SKILL.md` 同样支持单侧 plan review

影响：

- backend_only/frontend_only 时，orchestrator 应该进入 `ship-delivery-plan` 还是直接跳过该阶段不清晰
- 如果按 `When NOT to Use` 跳过，后续 `ship-plan-review` / `ship-build` 缺少计划输入
- 如果按 Scope Adaptation 保留，`When NOT to Use` 会误导执行者跳过必要计划阶段

建议决策：

- 单侧 scope 仍保留 `ship-delivery-plan`，但只产出对应侧 plan；`When NOT to Use` 改成“完全没有实施任务 / 纯文档改动 / 已有已评审计划”之类的条件
- 或者把单侧 scope 下的计划语义改为可跳过，但这会连带修改 `ship-plan-review`、`ship-build` 和 meta 状态机

建议采用前者，因为现有 protocol、plan-review 和 meta template 已经围绕“单侧仍有 plan”设计。

### A-021: `ship-delivery-plan` 的退出 checklist 没有按 scope 裁剪

状态：可直接修复，低风险。

现象：

- `ship-delivery-plan/SKILL.md` 的 Scope Adaptation 规定：
  - `backend_only` 只产出 `backend-plan.md`
  - `frontend_only` 只产出 `frontend-plan.md`
  - 单侧模式不执行 `sync` 子段
- 但同一文件 Verification checklist 仍硬性要求：
  - `frontend-plan.md frontmatter` 已设置
  - `backend-plan.md frontmatter` 已设置
  - `frontend-plan.md` 中所有页面/组件已拆解
  - `backend-plan.md` 中所有业务域/接口已拆解
  - `sync 子段已完成`
  - 两份文档 `stage_status` 均 ready

影响：

- backend_only/frontend_only 下会出现“正确缺失的产物”导致 checklist 永远无法通过
- 与 `workflow-protocol.md` 的“被跳过阶段的产物不生成，下游不得引用不存在产物”原则冲突

建议修复：

- Verification checklist 改成 scope-aware：
  - fullstack 检查双 plan + sync
  - backend_only 只检查 backend-plan，frontend-plan 明确 N/A
  - frontend_only 只检查 frontend-plan，backend-plan 明确 N/A
- `validate_workflow_docs.py` 可增加受 scope 影响阶段的 checklist 裁剪检查。

### A-022: `ship-build` 混用 `plan.md` 与双 plan，且并行/单 DOING 语义冲突

状态：需要用户确认实施阶段的任务事实源和并行语义。

现象：

- `ship-delivery-plan/SKILL.md` 明确不合并成单一 `delivery-plan.md`，保留 `frontend-plan.md` / `backend-plan.md`
- `README.md` 和 orchestrator 阶段表也都列出双 plan
- 但 `ship-build/SKILL.md` 多处写 `plan.md`：
  - 产物：“代码改动 + plan.md 中的任务状态更新”
  - Process Step 8：“在 plan.md 更新状态”
  - Step 1：“从 plan.md 的 TODO 列表选择”
  - Resume：“读取 plan.md 找到当前 DOING 任务”
  - 退出 checklist：“plan.md 中状态已更新为 DONE”
- 同一文件还存在并行语义不一致：
  - Contract-First Execution Order 写 Phase 2“前后端可并行”
  - Delegation Boundary / DOING 唯一性又写“正式编码任务串行”“同一时刻整个 plan 中最多只能有 1 个任务处于 DOING”

影响：

- 执行者不知道任务状态事实源是单个 `plan.md`、两个 plan 文件，还是抽象地指所有 plan
- 如果 fullstack 下允许前后端各一个 DOING，则当前 `meta.yml.stages.ship-build.current_task_id` 单值不够表达
- 如果全局只允许一个 DOING，则 “前后端可并行” 应改为“计划可并行拆分，正式实现串行推进；辅助支线可并行”

建议决策：

- 明确 `ship-build` 消费 `frontend-plan.md` / `backend-plan.md` 中的任务条目；文案中的 `plan.md` 改为“对应 plan 文件”或“双 plan”
- 明确正式编码是否全局单任务：
  - 方案 1：全局单 `DOING`，保持 `current_task_id` 单值，删除/改写“前后端可并行”表述
  - 方案 2：前后端各允许一个 `DOING`，需要扩展 meta 为 `current_frontend_task_id` / `current_backend_task_id`，并重写 build 委派边界

建议采用方案 1，和当前 delegation/user_gate_only 设计更一致。

### A-023: 软门禁强制推进要求写 `skip_log`，但 meta 协议和模板没有该字段

状态：可直接修复，低风险。

现象：

- `ship-orchestrator/SKILL.md` 的软门禁失败处理写：用户可选择强制推进，并“记录到 meta.yml 的 skip_log”
- 同文件 Verification checklist 也要求“软门禁跳过已记录到 meta.yml 的 skip_log（如有）”
- `workflow-protocol.md` 的 `meta.yml Summary Contract` 没有定义 `skip_log`
- `ship-orchestrator/_templates/meta/meta.yml.template` 没有 `skip_log`
- `feature_meta_runtime.py` 没有 `ensure_skip_log` 或记录软门禁跳过的 helper

影响：

- 执行协议要求记录强制推进，但模板/runtime 没有落点
- 恢复时无法区分“正常 ready 推进”和“用户承担风险强制推进”

建议修复：

- 在 `workflow-protocol.md` 定义 `skip_log` 对象结构，例如 `at / from_stage / to_stage / gate_type / reason / user_sign_off`
- 在 `meta.yml.template` 增加 `skip_log: []`
- 可选：在 `feature_meta_runtime.py` 增加 `record-skip` helper，并补测试

### A-024: INSPECT_FEATURES 提到 `abandoned`，但 meta 状态枚举没有

状态：需要用户确认是否引入 feature-level lifecycle。

现象：

- `ship-orchestrator/SKILL.md` 的 Inspect Protocol 输出字段包含状态标识：`in_progress / blocked / completed / abandoned`
- `workflow-protocol.md` 的 `meta.yml Summary Contract` 普通阶段状态只有 `pending / in_progress / ready / blocked / completed`
- `meta.yml.template` 也没有 feature-level `lifecycle_status` 或 `abandoned` 字段
- Resume Protocol 只过滤 `ship-handoff` 尚未 `completed` 的活跃 feature，无法表达用户主动放弃的 feature

影响：

- `abandoned` 是 feature 整体状态还是某个 stage 的状态不清楚
- 如果用户终止 feature，现有 meta 没有权威字段记录，INSPECT 只能靠推断或无法展示

可选决策：

- 方案 1：增加 feature-level 字段 `lifecycle_status: active | blocked | completed | abandoned`，stage status 仍保持现有枚举
- 方案 2：删除 INSPECT 中的 `abandoned`，只用当前 stage summary 表达活跃/阻塞/完成

建议采用方案 1，因为它能明确区分“某阶段 blocked”和“整个 feature 已放弃”。

### A-025: 用户显式跳过 Discover/Shape 与 orchestrator 强制路由规则存在张力

状态：需要用户确认“用户显式跳过”的权限边界。

现象：

- `ship-discover/SKILL.md` 的 `When NOT to Use` 写：用户明确说“跳过探索直接录入需求”时尊重用户意图
- `ship-shape/SKILL.md` 的 `When NOT to Use` 写：用户明确说“不需要设计，直接开始”时尊重用户意图
- `workflow-protocol.md` 的 fast-track 规则写：场景 A/C 即便选择 fast-track，也应至少经过 `ship-discover`
- `ship-orchestrator/SKILL.md` 的 scenario routing 也把 A/C 起点固定为 `ship-discover`

影响：

- 当用户只有一句话想法（场景 A）但明确要求“跳过探索直接录入需求”时，应该 obey 用户进入 `ship-define`，还是以协议质量门为准先 `ship-discover`，当前不明确
- 对 `ship-shape` 的跳过相对清晰：fast-track 默认跳过；但非 fast-track 下用户说“不需要设计”是否直接 `ship-define`，需要在 meta 中如何记录跳过原因，也没有定义

建议决策：

- `ship-discover`：场景 A/C 默认强制，但允许用户显式 override；override 必须写入 `skip_log`，并在 `ship-define` 中把缺失产品简报作为风险/假设处理
- `ship-shape`：保持可跳过，但必须记录跳过原因；若后续 UI 复杂度升高，升级回 standard 并补做
- 或者严格禁止跳过 `ship-discover`，则需要删除 `ship-discover/SKILL.md` 的 “尊重用户意图” 文案

建议采用第一种，符合“用户可强制推进软门禁但需留痕”的整体设计。

### A-026: `ship-shape` wireframe starter 与 CDN integrity 要求不一致

状态：可直接修复，低风险。

现象：

- `ship-shape/SKILL.md` 要求 HTML 技术骨架使用 React / ReactDOM / Babel CDN，并“带 integrity hash”
- `ship-shape/references/wireframe-starter/variant-template.html` 的注释也写“实施时必须补充 integrity SRI hash”
- 但 starter 模板中的三个 `<script>` 标签实际没有 `integrity` 属性

影响：

- 参考模板无法直接满足技能自身的浏览器验证/安全要求
- 执行者复用模板时容易遗漏 SRI，导致产物不符合 `ship-shape` 要求

建议修复：

- 给 starter 模板中的 CDN script 补齐当前版本的 SRI hash；或
- 如果希望模板保持占位，明确它是“需实例化后才合规”，并在 Verification 中检查每个变体 script 都有 integrity

建议采用补齐 SRI hash，并在校验脚本中检查 starter 模板与 `ship-shape` 要求一致。

### A-027: `requirements.md.generation_mode` 被 review 依赖，但 interview 模式 frontmatter 没有该字段

状态：可直接修复，低风险。

现象：

- `ship-define-review/SKILL.md` 在评审开始前要求检查 `requirements.md` 的 `generation_mode` 字段：
  - `prd_direct` → 执行 PRD Direct 评审流程
  - 无此字段或 `interview` → 标准评审流程
- `ship-define/SKILL.md` 的普通 interview 模式 frontmatter 只包含：
  - `stage`
  - `stage_status`
  - `updated_at`
  - `evidence_complete`
- 同一文件的 PRD Direct frontmatter 才包含 `generation_mode: prd_direct`
- `meta.yml.template` 中 `stages.ship-define.generation_mode` 注释写 `interview | prd_direct`，但 helper 当前不初始化该字段（见 A-009）

影响：

- 标准 requirements.md 缺少 `generation_mode` 时虽然 review 文案说可默认 interview，但跨文档证据不完整
- `review-define.md` frontmatter 又要求从 requirements.md 继承 `generation_mode`；如果 requirements.md 无字段，只能留空或猜测
- 恢复/审计时无法区分“确认为 interview”与“旧文档缺字段”

建议修复：

- 在 `ship-define/SKILL.md` 普通 frontmatter 中加入 `generation_mode: interview`
- 在 `workflow-protocol.md` 或 Scenario Routing Rules 中说明 `requirements.md.generation_mode` 是 Define 阶段产物字段
- 在 `feature_meta_runtime.py init --scenario` 中同步设置 `stages.ship-define.generation_mode`
- 在校验脚本中检查 `ship-define` 两种 frontmatter 都包含 generation mode。

### A-028: `ship-contract` 强制“关联前端页面”，不适配 backend_only / 外部 API 消费者场景

状态：需要与 A-013 的 contract 语义一起确认。

现象：

- `workflow-protocol.md` 和 orchestrator 当前倾向于所有 scope 保留 `ship-contract`
- `ship-contract/SKILL.md` 的核心目标和 evidence 标准要求：
  - “每个接口可追溯到具体的验收标准（AC ID）和前端页面”
  - Step 3 verify：“每个接口关联 AC ID + 前端页面”
  - evidence_complete：“每个接口至少关联一个前端页面”
  - Verification：“每个接口是否标注了调用页面？”
- `backend_only` scope 可能没有前端页面，只有外部消费者、CLI、worker、webhook 或其他服务调用者
- `ship-contract/SKILL.md` 自身 When NOT to Use 中也提到纯后端批处理/定时任务（见 A-013）

影响：

- 如果采用 A-013 建议，把 `ship-contract` 定义为“交互边界契约”并在 backend_only 中保留，则“前端页面”要求会错误阻塞 backend_only API/worker 契约
- 对外部 API 而非自家前端调用的场景，正确追踪对象应是 `consumer / client / entrypoint`，不一定是页面

建议修复：

- 将 contract 中“关联页面”泛化为“关联消费者/入口（consumer/entrypoint）”：
  - fullstack/frontend_only：页面或组件入口
  - backend_only API：外部消费者、SDK、服务调用方、CLI 命令、webhook
  - no-api/internal：显式写 `N/A` 和原因
- `api-contract-template.md` 同步调整字段名，避免只写 Page。

### A-029: `ship-design-review` 的 scope adaptation 有表述，但 checklist/output 仍硬性按三文档执行

状态：可与 A-004 一起修复。

现象：

- `ship-design-review/SKILL.md` 的 Scope Adaptation 规定：
  - `backend_only` 只评审 `api-contract.md + backend-design.md`
  - `frontend_only` 只评审 `api-contract.md + frontend-design.md`
  - 缺失侧检查项标记为 `na`
- 但同一文件后续仍有 fullstack 固定表述：
  - Overview 写统一评审三份技术方案
  - Cross-Validation Protocol 固定 Step 2 扫描 frontend、Step 3 扫描 backend、Step 4 交叉比对前后端数据模型
  - Review Checklist 硬性要求“前端页面-接口映射表”“后端 Service 方法”“数据模型前后端一致”
  - Output frontmatter 示例固定 `reviewed_documents: ["api-contract.md", "frontend-design.md", "backend-design.md"]`
  - Verification checklist 固定要求读取 frontend-design 和 backend-design

影响：

- 单侧 scope 下执行者需要自行判断哪些 checklist 是 N/A，技能正文没有逐项裁剪后的可执行清单
- 子代理或自动校验按后续 checklist 执行时，会把正确缺失的侧向文档判为失败

建议修复：

- 在 `ship-design-review/SKILL.md` 的 Cross-Validation / Review Checklist / Verification 中显式标注 scope-aware N/A 规则
- Output frontmatter 示例改为根据 `project_scope` 动态列出 `reviewed_documents`
- `validate_workflow_docs.py` 增加对 scope-aware review 的固定 fullstack 列表残留检查。

### A-030: `ship-frontend-design` 要求每个 contract 接口至少被页面引用，不适配 backend_only 或非页面消费者契约

状态：需要与 A-028 一起确认。

现象：

- `ship-frontend-design/SKILL.md` 的 Page-API Mapping Protocol 要求：
  - “每个接口在 api-contract.md 中至少被一个页面引用”
  - evidence_complete 也要求每个接口在映射表中至少被一个页面引用
  - Red Flags 中把“接口被定义但无任何页面调用”判为 contract 冗余接口
- 在 fullstack 产品 UI 场景下该规则合理
- 但若 `api-contract.md` 包含：
  - 后端仅供外部消费者使用的接口
  - webhook / batch / admin-only 非页面入口
  - frontend_only 消费第三方 API 的部分端点
  则“每个接口都被页面引用”可能不成立

影响：

- `ship-frontend-design` 会把合法的非页面接口误判为冗余
- 与 A-028 中 contract 泛化为 consumer/entrypoint 的方向不一致

建议修复：

- 将规则改为：每个“当前前端需要消费的接口”至少被一个页面/组件/route action 引用
- `api-contract.md` 中非当前前端消费的接口标记 `consumer_scope: backend_only | external | internal | frontend`，frontend-design 只校验 frontend scope
- design-review 按 scope 和 consumer_scope 判断冗余，而不是简单“所有接口都必须被页面引用”。

### A-031: 多个阶段声明可“直接进入实现/跳过”，但共享协议没有轻量变更路径

状态：需要用户确认是否支持 lightweight change flow。

现象：

- `ship-frontend-design/SKILL.md` When NOT to Use：
  - “仅是已有页面的样式微调 —— 直接进入实现阶段”
- `ship-backend-design/SKILL.md` When NOT to Use：
  - “仅是已有逻辑的重构（无新功能） —— 直接进入实现阶段”
- `ship-design-review/SKILL.md` When NOT to Use：
  - “仅修改了一个接口的小变更 —— 使用轻量 diff review”
  - “纯 UI 样式调整，不涉及接口变更 —— 无需本阶段”
- `ship-tech-discovery/SKILL.md` When NOT to Use：
  - “技术栈已完全固定且本次无需重新验证”
  - “仅是纯业务改动，无新技术引入、无架构决策”
- 但 `workflow-protocol.md` 当前只定义 standard / fast-track 两类主路径；fast-track 仍保留 define-review / verify / handoff，但没有定义“直接实现”的最小产物、任务来源、review 替代物或 meta 记录

影响：

- 这些 When NOT to Use 语句会让执行者绕过 `ship-delivery-plan` / `ship-plan-review` / `ship-build` 的前置条件，和 A-010/A-022 形成同类断裂
- “轻量 diff review” 没有 skill、模板、frontmatter 或门禁状态定义，无法恢复、审计或校验
- 对纯重构/样式微调这类工作，当前套件缺少正式的 `change_type` / `lightweight` 协议；简单写“直接进入实现”会破坏 workflow 的可追踪性

可选决策：

- 方案 1：删除各阶段“直接进入实现/无需本阶段”的旁路文案，所有变更都至少走 fast-track 最小路径
- 方案 2：新增 lightweight change flow，例如 `change_type: feature | bugfix | refactor | style | docs`，并定义最小产物、轻量任务源、验证和 handoff
- 方案 3：保留旁路但要求写 `skip_log` + 明确替代事实源，例如 diff brief / task checklist

建议采用方案 2 或 3；不建议保留无协议支撑的“直接进入实现”。

### A-032: `ship-tech-discovery` 可跳过，但 `ship-contract` 和下游强依赖 `tech-selection.md`

状态：需要用户确认固定技术栈场景的事实源。

现象：

- `ship-tech-discovery/SKILL.md` When NOT to Use 写：
  - 技术栈已完全固定且本次无需重新验证
  - 仅是纯业务改动，无新技术引入、无架构决策
- 但 `ship-contract/SKILL.md` When to Use 要求 `ship-tech-discovery` 已完成且 `tech-selection.md.stage_status = ready`
- `ship-contract/SKILL.md` Step 1 要从 `tech-selection.md` 判断 API 风格
- `ship-frontend-design/SKILL.md` / `ship-backend-design/SKILL.md` 的 spec matching 也基于 `tech-selection.md` 的技术栈标签
- `meta.yml.template` 虽有 `tech_stack` 字段，但没有声明它可以替代 `tech-selection.md`

影响：

- 一旦按 tech-discovery 的 When NOT to Use 跳过，本应进入 `ship-contract`，但 contract 入口条件不满足
- 固定技术栈场景的事实源不明确：是已有项目代码、`meta.yml.tech_stack`、还是需要生成一个 minimal `tech-selection.md`

建议决策：

- 固定技术栈场景仍生成 minimal `tech-selection.md`，记录“沿用既有技术栈”的证据、版本、来源和 ADR-lite；可跳过 `tech-research.md` 或简化 research
- 或允许 `meta.yml.tech_stack` 作为 `ship-contract` 的替代输入，但需要改 contract/frontend/backend 的入口条件和 spec matching 规则

建议采用 minimal `tech-selection.md`，保持下游事实源稳定。

### A-033: `ship-verify` 仍以 `plan.md` 为输入，和双 plan 事实源冲突

状态：可与 A-022 一起修复。

现象：

- `ship-delivery-plan/SKILL.md` 明确不合并成单一 `delivery-plan.md`，保留 `frontend-plan.md` / `backend-plan.md`
- `ship-build/SKILL.md` 混用 `plan.md` 的问题已记录为 A-022
- `ship-verify/SKILL.md` 的 Process 也写：
  - Step 1：读取 `plan.md`，识别已 DONE 的任务
  - Step 1-3：列出所有 DONE 任务，对照 Verification Per Task 检查测试是否齐全
- 但 current protocol 和 README 的正式 plan 产物是 `frontend-plan.md` / `backend-plan.md`

影响：

- verify 阶段不知道应该扫描哪个 plan 文件或如何合并双 plan 中的 DONE 任务
- backend_only/frontend_only 下更容易出现读错不存在 plan 的问题
- 若 fast-track 跳过 plan（见 A-010），verify 也缺少任务来源

建议修复：

- 将 `ship-verify` 的输入改为 scope-aware task source：
  - fullstack：读取 `frontend-plan.md` + `backend-plan.md`
  - backend_only：读取 `backend-plan.md`
  - frontend_only：读取 `frontend-plan.md`
  - fast-track：读取经用户确认的 lightweight task source（待 A-010 决策）
- 和 `ship-build` 共用同一任务事实源定义，避免 build/verify 各自发明。

### A-034: 纯文档/配置改动跳过 verify，但 handoff 入口要求 `verification.md.stage_status=ready`

状态：需要用户确认文档/配置类交付的最小验收路径。

现象：

- `ship-verify/SKILL.md` When NOT to Use 写：
  - “纯文档/配置类改动 —— 不需要传统测试，使用 `ship-handoff` 阶段的手工验证”
- `ship-handoff/SKILL.md` When to Use 要求：
  - `ship-verify` 已完成，且 `verification.md.stage_status = ready`
- `ship-handoff/SKILL.md` When NOT to Use 又写：
  - `ship-verify` 尚未将 `verification.md` 置为 `ready` 时不进入 handoff
- `workflow-protocol.md` 也定义 `ship-verify` 创建/更新 `verification.md`，自动化验证通过后置为 `ready`

影响：

- 如果按 verify 的 When NOT to Use 跳过测试阶段，就没有 `verification.md.stage_status=ready`，handoff 又不能进入
- 文档/配置类改动到底是由 verify 生成“manual-only verification.md”，还是 handoff 直接创建 verification.md，当前不明确

建议决策：

- 方案 1：不跳过 `ship-verify`，而是让 `ship-verify` 支持 `verification_mode: manual_only | docs_config`，产出 `verification.md.stage_status=ready`，说明自动化测试 N/A 与原因
- 方案 2：允许 `ship-handoff` 在文档/配置类改动下直接创建 `verification.md`，但需要修改 handoff 入口条件和 workflow ownership

建议采用方案 1，保持 `verification.md` ownership 稳定。

### A-035: `ship-handoff` 的 `complete` 是否允许 FAIL/BLOCKED AC 语义不清

状态：需要用户确认验收完成语义。

现象：

- `ship-handoff/SKILL.md` frontmatter 中 `all_ac_verified` 注释为“所有 AC 都有明确结果（含 N/A）则为 true”
- AC Mapping Protocol 允许 PASS / FAIL / BLOCKED / N/A 四态
- Risk Assessment 允许 P1/P2/P3 风险进入 handoff 的已知缺陷或后续建议
- stage_status 判定规则写：
  - 存在 P0 残余风险且未与用户对齐 → `draft`
  - 存在未映射 AC → `draft`
  - `AC 全部 PASS / N/A 已解释，FAIL/BLOCKED 已登记并对齐` → `complete`
- 这句话同时出现“AC 全部 PASS / N/A”和“FAIL/BLOCKED 已登记”，语义不够精确

影响：

- `complete` 是表示“所有 AC 通过”，还是表示“所有 AC 均有明确结论，用户接受残余风险后关闭交付”不明确
- `all_ac_verified=true` 可能被误解为所有 AC PASS，而文档实际注释是“所有 AC 有结果”
- 如果允许带 P1/P2 FAIL/BLOCKED complete，需要用户签字/接受风险字段；当前 frontmatter 没有 `accepted_risks` / `user_acceptance` 之类字段

可选决策：

- 方案 1：严格完成语义：只有所有 AC 为 PASS 或解释过的 N/A，才允许 `stage_status=complete`；任何 FAIL/BLOCKED 都保持 `draft` 或回到 build
- 方案 2：交付关闭语义：允许 FAIL/BLOCKED 在用户明确接受风险后 `complete`，但必须增加 accepted risk sign-off，并改名或补充 `all_ac_verified` 含义

建议采用方案 2 但补字段，因为真实交付常有已知缺陷验收；不过必须把用户接受风险作为硬条件。

### A-036: `ship-verify` 要求把测试命令写入项目 README 或 CI 配置，可能造成不必要的项目文件改动

状态：需要用户确认证据落点。

现象：

- `ship-verify/SKILL.md` 退出 checklist 要求“测试运行命令已写入项目 README 或 CI 配置”
- 但 `ship-verify` 的目标是验证实现产物并更新 `verification.md`
- 对一次 feature 级验证而言，把命令写入项目 README/CI 可能是额外代码库改动，尤其是临时命令、一次性环境命令或已有 README 维护策略不允许时
- `verification.md` 已经要求记录测试运行命令

影响：

- verify 阶段可能为了满足 checklist 修改全局 README/CI，扩大 feature diff
- 与 `ship-build` Scope Discipline 的“只改任务定义内文件、不顺手改”精神存在张力

建议修复：

- 改成：测试命令必须写入 `verification.md`；只有当命令属于长期项目规范且用户确认时，才同步到项目 README 或 CI
- 对缺少长期测试入口的项目，在 handoff 后续建议中记录“补 CI/README 测试入口”。

### A-037: `workflow_stage_map.py` 的用户摘要是 fullstack 固定文案，不感知 scope

状态：可与 A-004 一起修复。

现象：

- `workflow_stage_map.py` 是 `meta.yml.macro_stage.summary / next_user_decision` 的运行时来源
- 其中 `ship-delivery-plan` 写：“Frontend and backend implementation plans...”
- `ship-plan-review` 写：“Frontend and backend plans...”
- `ship-design-review` 写：“Contract, frontend, and backend designs...”
- `ship-contract` 写：“frontend and backend alignment”
- 但 `workflow-protocol.md` 已定义 `backend_only` / `frontend_only`，这些阶段在单侧 scope 下只涉及一侧产物或 consumer contract

影响：

- `backend_only` / `frontend_only` feature 的默认状态摘要会向用户展示不存在的侧向产物
- 这与 A-012 的 orchestrator 文案问题同源，但运行时 helper 会把该文案写入 `meta.yml.macro_stage`，影响恢复和 INSPECT 输出

建议修复：

- 让 `stage_view_for()` 保持 stage 基础文案，但新增 scope-aware wrapper，例如 `stage_view_for(stage, project_scope)`；或
- 在 `feature_meta_runtime.ensure_macro_stage()` 根据 `data.project_scope` 覆盖 `summary / next_user_decision`
- 增加 backend_only/frontend_only 单元测试，确保摘要不再出现被跳过侧。

### A-038: orchestrator 描述阶段完成后“回调调度器”，但 runtime helper 没有状态推进契约

状态：需要确认是否要把状态推进做成 helper。

现象：

- `ship-orchestrator/SKILL.md` 写：阶段 skill 完成后必须回调调度器，调度器读取产物 frontmatter、回写 `meta.yml` 对应阶段状态、同步 `current_part`、更新 `macro_stage`
- `workflow-protocol.md` 也定义：阶段开始时 `in_progress`，产物达到条件时 `ready`/评审状态，成功切换后上一阶段 `completed`，下一阶段写入 `current_stage`
- 但 `feature_meta_runtime.py` 当前只有：
  - `init`
  - `refresh`
  - delegation override/warning
  - spec sync/proposal
- 没有 `advance-stage`、`mark-stage-ready`、`sync-frontmatter-status`、`complete-stage` 等 helper
- `test_spec_runtime.py` 也没有覆盖阶段推进状态机

影响：

- 最关键的 “frontmatter 是事实源 → meta 是索引层” 同步规则只能靠 agent 手工执行，容易漏写或写错
- A-009/A-011/A-023/A-024/A-035 等状态类问题都缺少 runtime 层收口点
- 校验脚本只能检查文档字符串，不能验证真实状态转换

可选决策：

- 方案 1：保持 runtime helper 轻量，只把状态推进作为人工协议；但需要在文档中明确“helper 不负责 stage transition”
- 方案 2：新增最小状态推进 helper，读取/校验 frontmatter 后更新 `meta.yml`，并把 scenario/scope/skip_log/lifecycle 一起纳入测试

建议采用方案 2，因为这套技能的核心价值是可恢复、可审计；状态推进手工化会削弱这个目标。

### A-039: runtime helper 命令示例依赖调用目录，`skills/` 目录内不可直接执行

状态：可直接修复，低风险。

现象：

- `ship-spec/SKILL.md` 的 Runtime Helpers 示例使用：
  - `python3 skills/ship-orchestrator/scripts/spec_runtime.py ...`
  - `python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py ...`
- `../README.md` 的维护命令也使用同样的 `skills/...` 相对路径
- 这些命令从项目根 `/Users/rao/AiDoWork/ai-feature-coding` 运行时路径成立，但从当前 skills 根 `/Users/rao/AiDoWork/ai-feature-coding/skills` 运行时会解析成 `skills/skills/...`
- 验证结果：

```bash
python3 skills/ship-orchestrator/scripts/spec_runtime.py --help
```

在 `skills/` 目录下失败：

```text
can't open file '/Users/rao/AiDoWork/ai-feature-coding/skills/skills/ship-orchestrator/scripts/spec_runtime.py'
```

而在 `skills/` 目录下使用：

```bash
python3 ship-orchestrator/scripts/spec_runtime.py --help
```

路径可解析成功。

影响：

- 维护者按 `ship-spec/SKILL.md` 示例在 skills 包目录内执行会失败
- 技能被安装到只包含 `skills` 内容的环境时，`skills/...` 前缀可能不再成立
- 这与 A-007 的 Python 解释器 / PyYAML 依赖问题叠加，会让 runtime helper 的推荐入口不稳定

建议修复：

- 在 README / `ship-spec/SKILL.md` 明确命令的工作目录，例如“从仓库根运行”
- 或改用相对当前 skill 包更稳的路径示例，例如在 `skills/README.md` 中写 `python3 ship-orchestrator/scripts/...`
- 对上级 `../README.md` 保留 `skills/...` 路径，但在 `skills/README.md` / `ship-spec/SKILL.md` 使用包内相对路径
- 统一维护章节给出推荐 Python 解释器 / 依赖安装方式，和 A-007 一并处理

### A-040: `ship-plan-review` 的 scope adaptation 有表述，但流程和输出仍固定双 plan

状态：可与 A-004 / A-020 一起修复。

现象：

- `ship-plan-review/SKILL.md` 的 Scope Adaptation 规定：
  - `backend_only` 只评审 `backend-plan.md`
  - `frontend_only` 只评审 `frontend-plan.md`
  - 缺失侧检查项和双侧对齐检查项标记为 `na`
- 但同一文件后续仍有 fullstack 固定表述：
  - Overview 写评审 `frontend-plan.md` 和 `backend-plan.md` 两份实施计划
  - Process Step 1 固定读取 `frontend-plan.md + backend-plan.md`
  - Review Checklist 硬性要求前端任务覆盖、后端任务覆盖、接口对齐任务在前后端共享时间线前部
  - Output frontmatter 示例固定 `reviewed_documents: ["frontend-plan.md", "backend-plan.md"]`
  - Verification checklist 固定要求“已读取并理解 frontend-plan.md 全部任务定义”和“已读取并理解 backend-plan.md 全部任务定义”

影响：

- 单侧 scope 下执行者需要自行判断哪些 checklist 是 N/A，技能正文没有逐项裁剪后的可执行流程
- 子代理或自动校验按后续 checklist 执行时，会把正确缺失的 plan 判为失败
- 与 A-021 的 delivery-plan scope 裁剪缺口会连续传导到 plan-review gate，导致单侧 feature 卡在 plan-review

建议修复：

- 在 Process / Review Checklist / Verification 中显式标注 scope-aware N/A 规则
- Output frontmatter 示例改为根据 `project_scope` 动态列出 `reviewed_documents`
- 对单侧 scope，把“前后端共享时间线”改为对应侧任务依赖与 contract/entrypoint 顺序检查
- `validate_workflow_docs.py` 增加对 plan-review 固定双 plan 残留的检查

## 初步非问题项

### N-001: `verification.md.stage: ship-handoff` 出现在 ship-verify 产物说明中

判断：不是冲突。

原因：共享协议已定义 `verification.md` 最终 ownership 在 handoff，`ship-verify` 只写测试章节并将 `stage_status` 置为 `ready`。

### N-002: fast-track 跳过 design/plan 但仍保留 define-review/verify/handoff

判断：不是冲突。

原因：`workflow-protocol.md` 明确 fast-track 不是跳过流程直接编码，最小路径保留 `ship-define-review`、`ship-verify`、`ship-handoff`。

### N-003: stage reference templates 与阶段 SKILL 的关系

判断：当前没有发现冲突。

证据：

- `api-contract-template.md`、`frontend-design-template.md`、`backend-design-template.md` 都声明“写作引导模板，不是固定格式”
- 对应阶段 SKILL 也声明模板是写作引导，不是 rigid schema；章节顺序可调整，不适用章节可裁剪
- 三个模板的“必答问题 / 推荐写法 / 常见空话警报”与阶段 SKILL 的输出要求方向一致

### N-004: `ship-shape` reference assets 与主 SKILL 一致

判断：当前没有发现冲突。

证据：

- `design-brief-template.md` 的 frontmatter 与 `ship-shape/SKILL.md` 输出定义一致
- `anti-slop-checklist.md` 与 `ship-shape/SKILL.md` Anti-Slop Discipline 对齐
- `design-direction-library.md` 与 `ship-shape/SKILL.md` 的 5 学派 × 2 流派一致

## 建议下一步

待用户确认 `.docs/ship-skills-confirmation.md` 中 C-001 至 C-011 的协议决策后再修改语义文件。

优先确认的高影响决策：

1. C-001：阶段模型是否统一为 5 个 macro stages、14 个 canonical stages。
2. C-003：`ship-contract` 是否统一为通用 interaction boundary contract，并按 scope 裁剪下游 checklist。
3. C-004 / C-005：fast-track、lightweight change flow、build/verify 任务事实源如何定义。
4. C-006 / C-010：`skip_log`、`lifecycle_status`、stage advancement helper 是否进入 runtime。
5. C-009：handoff `complete` 是否允许用户接受风险后的 FAIL/BLOCKED AC。

确认后建议修复顺序：

1. 修正共享协议、上级 README 和 skills README 口径
2. 修正 `feature_meta_runtime.py` delegation registry
3. 补测试与校验脚本
4. 修正 scope 单侧模式在 `ship-build` / `ship-verify` / orchestrator 阶段表里的文字和退出条件
5. 修正测试入口、runtime helper 命令路径和 Python 依赖说明
6. 运行校验脚本和单元测试
