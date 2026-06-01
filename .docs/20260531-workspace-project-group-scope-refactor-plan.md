# workspace/project-group scope 重构复盘与修改计划

## 1. 背景与问题复盘

当前 `skills` 工作流的 feature 创建模型以 `target project` 为中心：

- `ship-orchestrator` 在 NEW_FEATURE 时解析 `target project/.docs/ship/project.yml`。
- feature 目录写入 `target project` 的 `feature_root`，默认是 `.docs/feature-*`。
- `ship-spec` 只消费单一 `target project` 的 `spec_root`。
- 多项目父目录下，现有协议要求用户先选定一个 target project，不允许从父目录自动猜。

这个模型适合单项目或明确落在某个项目内的需求，但不适合“一个 workspace 下有多个一级项目，需求横跨其中多个项目”的场景。

用户提出的新目标是：

- 创建需求时，先识别当前目录是单项目根目录还是多项目组根目录。
- 多项目组场景下，需求目录放在项目组根目录 `.docs/feature-*`。
- 多项目组场景下，每个需求只需要记录默认关联的项目名称列表，例如 `projects: [web, api]`。
- 这些关联项目只是默认执行范围，不是不可突破的硬边界；用户明确要求探索其他项目时允许扩展。
- 不考虑旧信息兼容，可以直接重构到新模型。

## 2. 已确认的设计决策

### 2.1 feature 目录归属

多项目组需求目录统一放在项目组根目录：

```text
workspace/
├── .docs/
│   ├── ship/project.yml
│   └── feature-YYYYMMDD-<short-name>/
├── web/
└── api/
```

不把跨项目 feature 放到某个 primary project 的 `.docs/` 下。

### 2.2 多项目识别粒度

多项目组只支持“一级目录就是项目”：

```text
workspace/
├── web/
├── api/
└── admin/
```

暂不支持以下形式作为 project registry 的基础模型：

```text
workspace/
├── apps/web/
└── services/api/
```

如后续要支持二级路径，需要另开设计，不混入本次重构。

### 2.3 项目身份字段

取消 `project_id / project_name` 双字段。

原因：

- 两个字段同时存在会让用户困惑哪个才是真正身份。
- 本次目标强调简单、可读、可手工维护。
- 多项目组项目名直接使用一级目录名，既是显示名，也是查找目录的 key。

### 2.4 feature 元数据保持简单

feature `meta.yml` 不记录每个项目的 role、project root、project config 等复杂结构。

推荐只记录：

```yaml
workspace_mode: project_group
projects:
  - web
  - api
```

### 2.5 workspace 配置使用 YAML comment

`.docs/ship/project.yml` 每个字段直接用 YAML comment 解释，不额外创建 README 作为字段说明。

## 3. 目标配置模型

### 3.1 `.docs/ship/project.yml`

目标模板：

```yaml
# Ship workflow workspace config.
# 这个文件用于告诉 ship-orchestrator 当前目录是单项目根目录，还是多项目组根目录。

schema_version: 2

# single_project: 当前目录本身就是一个项目根目录。
# project_group: 当前目录是多个一级项目目录的父目录。
workspace_mode: project_group

# 工作区名称。默认可以使用当前目录名。
workspace_name: my-workspace

# feature 需求目录根路径。默认所有需求都创建到当前 workspace 的 .docs/ 下。
feature_root: ".docs"

# 仅 workspace_mode=project_group 时使用。
# 项目名称必须等于当前目录下的一级目录名，例如 ./web、./api。
# 不支持 apps/web 这种二级路径。
projects:
  - web
  - api
```

单项目示例：

```yaml
# Ship workflow workspace config.
schema_version: 2

# single_project: 当前目录本身就是一个项目根目录。
# project_group: 当前目录是多个一级项目目录的父目录。
workspace_mode: single_project

# 工作区名称。默认可以使用当前目录名。
workspace_name: demo-app

# feature 需求目录根路径。默认所有需求都创建到当前 workspace 的 .docs/ 下。
feature_root: ".docs"

# single_project 时保持空列表。
projects: []
```

### 3.2 feature `meta.yml`

新增字段建议放在现有 feature 基础信息附近：

```yaml
# 工作区范围。由 .docs/ship/project.yml 初始化。
workspace_mode: project_group

# 本需求默认关联的项目列表。
# project_group 时使用一级目录名；single_project 时可为空。
projects:
  - web
  - api
```

语义：

- `projects` 是本需求默认范围。
- 后续阶段默认围绕这些项目做需求整理、技术探索、设计和任务拆分。
- 用户明确要求探索未列入的其他项目时允许执行，但应在阶段文档中记录为临时扩展范围或发现项。
- 如果用户希望该项目成为本需求默认范围，应确认后追加到 feature `meta.yml.projects`。

## 4. 创建需求时的新引导流程

### 4.1 Workspace Config Gate

NEW_FEATURE 创建需求目录前，第一步必须处理 workspace 配置。

流程：

1. 读取当前目录 `.docs/ship/project.yml`。
2. 如果存在：
   - 读取 `workspace_mode / workspace_name / feature_root / projects`。
   - 校验字段是否满足当前 schema。
   - 进入 Feature Scope Interview。
3. 如果不存在：
   - 暂停 feature 创建。
   - 告知用户需要初始化 workspace config。
   - 询问当前目录是 `single_project` 还是 `project_group`。
   - 如果是 `project_group`，列举当前目录一级目录作为候选项目。
   - 用户确认后创建 `.docs/ship/project.yml`。
   - 再进入 Feature Scope Interview。

一级目录候选过滤建议：

- 排除隐藏目录：`.git`、`.docs`、`.vscode` 等。
- 排除依赖或产物目录：`node_modules`、`dist`、`build`、`target`、`coverage` 等。
- 排除明显不是项目的临时目录。
- 不做复杂项目探测，不根据 `package.json` 等自动决定最终项目列表。

### 4.2 Feature Scope Interview

Workspace Config Gate 通过后，创建 feature 前固定询问：

1. 需求目录名称
   - agent 根据需求生成推荐短名。
   - 用户可以确认或修改。
   - 最终目录为 `feature-YYYYMMDD-<short-name>`。

2. 本需求关联项目
   - `single_project`：不询问项目列表，默认当前 workspace。
   - `project_group`：展示 `.docs/ship/project.yml.projects`，让用户选择本需求默认关联项目。

3. 新项目反补
   - 如果用户填写的项目名不在 `.docs/ship/project.yml.projects` 中：
     - 检查当前目录下是否存在同名一级目录。
     - 若存在，询问是否加入 `.docs/ship/project.yml`。
     - 用户确认后追加到 workspace config。
     - 再写入 feature `meta.yml.projects`。
   - 如果同名一级目录不存在：
     - 询问用户是否项目目录尚未创建，或项目名是否写错。
     - 默认不写入 workspace config，除非用户明确确认允许登记一个尚不存在的项目名。

## 5. 后续阶段行为调整

### 5.1 `ship-define`

默认读取 feature `meta.yml.projects`，在需求整理中标明本需求默认关联项目。

要求：

- AC / domain 不强制按项目拆，但涉及项目应可追踪。
- 如果需求描述明显涉及未登记项目，应提示用户是否追加到本需求默认项目列表。

### 5.2 `ship-tech-discovery`

Project Reality First 的默认扫描范围改为：

- `single_project`：当前 workspace 根目录。
- `project_group`：feature `meta.yml.projects` 中列出的一级目录。

允许行为：

- 用户明确要求“也探索一下其他项目”时，可以临时读取其他一级目录。
- 临时扩展应写入 `tech-research.md` 的证据或备注，而不是静默扩大默认范围。

不允许行为：

- 在 `project_group` 下默认扫描整个 workspace。
- 在没有用户确认的情况下把未登记项目追加到 workspace config。

### 5.3 `ship-contract`

跨项目需求时，contract 不再只表达单项目内部前后端契约，而应表达 involved projects 之间的边界。

要求：

- 明确哪些项目是生产者、消费者或被影响方。
- 这些角色由技术探索阶段基于代码事实判断，不在 feature `meta.yml` 中预设。

### 5.4 `ship-frontend-design` / `ship-backend-design`

不要从 feature `meta.yml.projects` 预设前后端角色。

阶段内应通过 Project Reality First 和 tech selection 判断：

- 哪些项目包含 UI / page / component。
- 哪些项目包含 API / service / job / persistence。
- 如果项目类型不明显，记录证据和不确定项。

### 5.5 `ship-delivery-plan` / `ship-build`

任务拆分时，每个任务应能看出目标项目。

建议任务字段增加或要求出现：

```yaml
project: web
```

或在 markdown task 标题/元信息中明确目标项目。

原因：

- 多项目需求中，任务如果只写文件或模块，很容易丢失执行归属。
- 这不要求 feature `meta.yml` 复杂化，只是在执行计划里记录事实。

### 5.6 `ship-spec`

本次重构需要重新定义 `ship-spec` 的边界。

建议第一阶段保持简单：

- workspace config 仍只定义 `feature_root` 和 `projects`。
- 默认 spec root 仍是 workspace `.docs/spec`。
- 不为每个一级项目单独维护 `project/.docs/spec`。

原因：

- 用户当前诉求是需求范围与项目组识别，不是多 spec root。
- 若同时引入 per-project spec root，会重新带回复杂 mapping。

后续如果确实需要 per-project spec，可另开方案。

## 6. 需要修改的文件与具体计划

### 6.1 模板

1. `skills/ship-orchestrator/_templates/project/project.yml.template`
   - 改为 schema_version 2。
   - 移除 `project_id / project_name / project_root / spec_root / module_layout`。
   - 新增 `workspace_mode / workspace_name / feature_root / projects`。
   - 每个字段添加 YAML comment。

2. `skills/ship-orchestrator/_templates/meta/meta.yml.template`
   - 新增 `workspace_mode`。
   - 新增 `projects: []`。
   - 保持字段简单，不加 project object 列表。
   - 评估是否保留现有 `spec_context.target_project_*`；如果保留，需要改名或降级为 spec utility 内部字段，避免与 workspace model 冲突。

### 6.2 runtime helper

1. `skills/ship-orchestrator/scripts/spec_runtime.py`
   - 将 `ProjectSpecContext` 重构为 workspace context。
   - `load_project_context` 改为读取 `workspace_mode / workspace_name / feature_root / projects`。
   - 移除对 `project_id` 必填的依赖。
   - 移除 `module_layout.mode == project_level_only` 的校验。
   - 新增 project_group 项目名校验：项目名必须是非空字符串，且推荐等于一级目录名。
   - `feature_root` 解析基于 workspace root。

2. `skills/ship-orchestrator/scripts/feature_meta_runtime.py`
   - `init` 增加 `--project` 可重复参数，用于写入 feature `meta.yml.projects`。
   - 初始化 feature 时写入 `workspace_mode` 和 `projects`。
   - `resolve_feature_dir` 改为基于 workspace `feature_root`。
   - 新增或调整 workspace config 缺失错误信息：从 “provide --project-config” 改成 “initialize .docs/ship/project.yml first”。
   - 如果 `workspace_mode=project_group` 且未传 projects，应阻塞或返回需要用户选择项目。

3. 可选新增 helper
   - `workspace_config_runtime.py`
   - 职责：
     - 扫描一级目录候选项目。
     - 初始化 `.docs/ship/project.yml`。
     - 追加新项目到 `projects`。
   - 是否新增单独脚本取决于实现复杂度；如果逻辑很少，可以先放在 `feature_meta_runtime.py`。

### 6.3 orchestrator 文档

1. `skills/ship-orchestrator/SKILL.md`
   - 增加 Workspace Config Gate。
   - 增加 Feature Scope Interview。
   - 修改 NEW_FEATURE 目录创建流程。
   - 删除或替换 “target project” 单边界措辞。
   - 明确 project_group 下 feature 创建在 workspace `feature_root`。
   - 明确项目名来自 `.docs/ship/project.yml.projects`，且等于一级目录名。

2. `skills/README.md`
   - 默认使用方式补充 workspace config。
   - 多项目父目录说明改成：先初始化 workspace config，再为 feature 选择关联 projects。

3. `README.md`
   - 更新最小 project config 示例为 workspace config。
   - 更新 helper 示例，加入 `--project web --project api`。

4. `skills/ship-spec/SKILL.md`
   - 从 target project spec boundary 改成 workspace spec boundary。
   - 暂不引入 per-project spec root。

5. `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
   - 更新 Project Resolution Contract 为 Workspace Resolution Contract。
   - 新增 feature `projects` 的语义。
   - 明确 `projects` 是默认范围，不是硬安全边界。

6. `skills/ship-orchestrator/_templates/README.md`
   - 更新 project template 字段说明。

### 6.4 validators / tests

1. `skills/ship-orchestrator/scripts/validate_workflow_docs.py`
   - 替换校验项：
     - 移除 `target_project_id / target_project_root / project_root / module_layout` 强校验。
     - 新增 `workspace_mode / workspace_name / projects` 强校验。

2. `skills/ship-orchestrator/scripts/test_spec_runtime.py`
   - 更新 project config fixture。
   - 新增测试：
     - single_project config 可加载。
     - project_group config 可加载。
     - project_group projects 只接受一级目录名。
     - feature_dir 创建在 workspace `.docs/feature-*`。
     - 多项目 feature meta 写入 `projects: [web, api]`。
     - workspace config 缺失时，创建需求返回明确阻塞错误。

3. `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
   - 搜索并替换对旧 target project 字段的断言。
   - 增加 project_group workflow 场景回归。

## 7. 验证计划

### 7.1 静态搜索复查

执行：

```bash
rg -n "project_id|project_name|project_root|target_project|target project|module_layout" skills README.md
```

预期：

- 除非出现在历史说明或迁移说明中，否则不应再作为当前协议字段出现。
- 如果保留 `target_project` 只用于旧注释，需要明确标记 deprecated；本次不考虑旧兼容，原则上应删除。

### 7.2 文档一致性校验

执行：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

预期：

- 通过。
- 校验项应覆盖 workspace config、feature projects、Workspace Config Gate。

### 7.3 runtime 单测

执行：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

预期：

- 旧 target project fixture 全部更新。
- 新增 workspace/project_group 场景通过。

### 7.4 手工 smoke test

准备临时目录：

```text
/tmp/ship-workspace-smoke/
├── web/
├── api/
└── admin/
```

验证：

1. 无 `.docs/ship/project.yml` 时，初始化流程提示创建 workspace config。
2. 选择 `project_group` 后，候选项目展示 `web / api / admin`。
3. 创建 `.docs/ship/project.yml`。
4. 创建 feature 时选择 `web / api`。
5. feature 目录创建到 `.docs/feature-YYYYMMDD-*`。
6. `meta.yml` 写入：

```yaml
workspace_mode: project_group
projects:
  - web
  - api
```

7. 输入不存在但当前目录存在的一级目录名时，可确认反补到 `.docs/ship/project.yml.projects`。

## 8. 风险与需要注意的地方

### 8.1 spec_context 命名冲突

现有 `meta.yml.spec_context` 里有 `target_project_id / target_project_root / spec_root / feature_root`。

本次目标取消 target project 模型后，需要决定：

- 要么把它改成 workspace spec context。
- 要么暂时保留但改名，避免和 workspace scope 混淆。

建议：同步改成 workspace 语义，不保留 target project 命名。

### 8.2 项目名等于目录名的约束必须写清楚

这是保持简单的关键约束。

如果文档没有写清楚，用户会自然想填中文项目名或业务名，后续技术探索无法解析目录。

### 8.3 `projects` 是默认范围，不是硬边界

设计文档、阶段 skill、validator 都要避免把 `projects` 理解成安全沙箱。

正确语义：

- 默认围绕这些项目执行。
- 临时探索其他项目允许。
- 是否把其他项目加入默认范围，需要用户确认。

### 8.4 不要提前引入 role

不要在 workspace config 或 feature meta 中加入：

- frontend/backend role
- primary project
- project_config
- per-project spec_root

这些信息应由技术探索阶段基于代码事实判断；否则又会回到复杂模型。

## 9. 推荐实施顺序

1. 先改文档协议与模板
   - `project.yml.template`
   - `meta.yml.template`
   - `workflow-protocol.md`
   - `ship-orchestrator/SKILL.md`

2. 再改 runtime helper
   - `spec_runtime.py`
   - `feature_meta_runtime.py`

3. 再改阶段 skill 文案
   - `ship-tech-discovery`
   - `ship-contract`
   - `ship-build`
   - `ship-spec`

4. 最后改 validator 与 tests
   - `validate_workflow_docs.py`
   - `test_spec_runtime.py`
   - `test_workflow_hardening.py`

5. 执行完整验证
   - 文档校验
   - runtime 单测
   - 手工 smoke test

## 10. 当前不做的事情

- 不做旧 `project_id / project_name` 配置兼容。
- 不支持二级项目路径，例如 `apps/web`。
- 不引入 per-project `.docs/ship/project.yml`。
- 不引入每项目 role、primary project 或复杂 project object。
- 不让 feature `meta.yml` 记录过多解析信息。
