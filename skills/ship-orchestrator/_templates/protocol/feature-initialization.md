# Feature Initialization Protocol

本协议定义 NEW_FEATURE 模式下的目录创建流程和初始化规则。

## 初始化流程

### 1. Workspace Config Gate

读取当前目录 `.docs/ship/project.yml`：
- 若不存在，暂停创建并询问 `single_project` 或 `project_group`
- 若是 `project_group` 初始化，列举当前目录一级目录候选项目，排除隐藏目录、依赖目录和产物目录，用户确认后写入 `.docs/ship/project.yml`

### 2. Feature Scope Interview

确认短名，并在 `project_group` 下让用户选择本 feature 默认关联 projects。

若用户选择的新项目不在 workspace config 中：
- 先检查同名一级目录
- 存在时询问是否追加到 `.docs/ship/project.yml.projects`

### 3. 生成功能短名

根据用户输入提取功能短名（short-name），转换为 kebab-case。

**短名生成规则**：
- 优先使用用户输入中的功能名词
- 若用户未提供，从需求描述中提取核心动词+名词组合
- 长度控制在 2-5 个英文单词或拼音
- 避免特殊字符，仅保留字母数字和连字符

**目录命名冲突处理**：
- 同日同短名：追加 -v2、-v3 后缀
- 短名为空：使用 feature-YYYYMMDD-<timestamp> 兜底

### 4. 生成日期前缀

生成日期前缀 YYYYMMDD（基于当前日期）。

### 5. 创建 feature 目录

在 workspace `feature_root` 下创建目录 `feature-YYYYMMDD-<short-name>/`。

### 6. 创建 resource 子目录

创建 `resource/` 子目录用于存放 PRD、原型、截图等参考资料。

### 7. 复制模板文件

#### 所有场景

- 复制 `./_templates/meta/meta.yml.template` 到 feature 目录，重命名为 `meta.yml`
- 复制 `./_templates/resource/README.md.template` 到 `resource/README.md`

#### 场景 B/D

- 复制 `./_templates/requirements/raw-prd-inbox.md.template` 到 `requirements.md`

#### 场景 E

- 不复制 raw PRD inbox

#### 场景 A/C

- 不复制 raw PRD inbox（直接进入 `ship-discover`）

### 8. 填充 meta.yml 初始字段

#### 基础字段

- `feature_name`：功能名称
- `feature_id`：feature-YYYYMMDD-<short-name>
- `created_at`：创建时间戳
- `workspace_mode`：single_project / project_group
- `projects`：关联项目列表（project_group 下）

#### Macro Stage

- `macro_stage.current`：当前大阶段
- `macro_stage.label`：大阶段标签
- `macro_stage.summary`：大阶段摘要
- `macro_stage.next_user_decision`：下一次用户决策点

#### Delegation

- `delegation.default_mode: current_context`
- `delegation.ask_on_parallel_stage: true`
- `delegation.ask_on_assistive_node: true`
- `delegation.node_overrides: {}`
- `delegation.warnings: []`

#### Spec Context

- `spec_context.workspace_mode`
- `spec_context.workspace_name`
- `spec_context.spec_root`
- `spec_context.resolved_spec_roots`
- `spec_context.feature_root`
- `spec_context.resolution_source`

#### Stages

将所有阶段的 status 初始化为 `pending`。

## 场景特定初始化

### 场景 A（零到一）

**meta.yml 设置**：
- `scenario: greenfield`
- `discovery_mode: greenfield`
- `current_stage: ship-discover`
- `stages.ship-discover.status: pending`
- `stages.ship-shape.status: pending`（若涉及 UI）

**初始化行为**：
- 不创建 raw `requirements.md` inbox
- 直接进入 `ship-discover`

### 场景 B（产品提供）

**meta.yml 设置**：
- `scenario: product_provided`
- `current_stage: ship-define`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`（默认）
- `stages.ship-define.generation_mode: interview`
- `stages.ship-define.status: blocked`，`block_reason: awaiting_materials`（若先创建目录）

**初始化行为**：
- 创建 raw `requirements.md` inbox
- 创建 `resource/README.md`
- 若已有材料，直接进入 `ship-define`
- 若先创建目录，保持 blocked 态等待用户补材料

### 场景 C（迭代增强）

**meta.yml 设置**：
- `scenario: evolve`
- `discovery_mode: evolve`
- `current_stage: ship-discover`
- `evolve_source.feature_dirs` 或 `code_paths` 或 `existing_behavior_summary`（至少一种）
- `stages.ship-discover.status: pending`

**初始化行为**：
- 必须有现状基线
- 若用户未指定基线，先询问，不创建目录
- 记录 `evolve_source` 至少包含一种基线类型

### 场景 D（PRD 直通）

**meta.yml 设置**：
- `scenario: prd_direct`
- `current_stage: ship-define`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`（默认）
- `stages.ship-define.generation_mode: prd_direct`
- `stages.ship-define.status: blocked`，`block_reason: awaiting_materials`（若先创建目录）

**初始化行为**：
- 创建 raw `requirements.md` inbox
- 创建 `resource/README.md`
- `ship-define` 走 prd_direct 模式（零提问纯提取）
- 若先创建目录，保持 blocked 态等待用户补材料

### 场景 E（技术方案选区入口）

**meta.yml 设置**：
- `scenario: technical_plan_provided`
- `project_context: existing_project`（强制）
- `current_stage: ship-tech-discovery`
- `stages.ship-discover.status: skipped`
- `stages.ship-shape.status: skipped`
- `stages.ship-define.status: skipped`
- `stages.ship-define-review.status: skipped`
- `stages.ship-define.generation_mode: technical_plan`（用于派生 requirements index 兼容标识）
- `technical_plan_source.selected_scope` 非空
- `technical_plan_source.selection_mode: referenced_sections | pasted_excerpt`
- `technical_plan_source.ignored_source_policy: out_of_scope`
- `technical_plan_source.repository_scan_required: true`

**初始化行为**：
- 只创建 `resource/README.md`
- 不创建 raw `requirements.md` inbox
- `requirements.md` 由 `ship-tech-discovery` 开头派生
- `selection_mode=pasted_excerpt` 时归档为 `resource/technical-plan-excerpt.md`，并写入 `pasted_excerpt_file`

**约束条件**：
- 只允许 `project_context: existing_project`
- 若用户说是新项目，必须阻塞并建议改走场景 A/B/D

## 资料准备态解除规则

### 触发条件

当用户说"资料放好了 / PRD 填好了"。

### 检查规则

检查 `requirements.md` 是否不是空 raw inbox 模板，或 `resource/` 下存在至少一个非 `README.md` 文件。

### 解除行为

1. 若两者都为空，继续保持 `stages.ship-define.status: blocked` 和 `block_reason: awaiting_materials`，提示用户补资料
2. 若存在资料，清空 `block_reason`，将 `stages.ship-define.status` 改为 `pending`
3. 将控制权交给 `ship-define`；`ship-define` 启动后再将状态改为 `in_progress`

## UIUX Material Gate

### 适用场景

场景 B/D，且：
- `project_scope = fullstack | frontend_only`
- feature 涉及 UI

### 检查时机

在启动 `ship-define` 前。

### 材料覆盖度判定

| 覆盖度 | 定义 | 处理方式 |
|--------|------|---------|
| `sufficient` | 材料可访问，覆盖 Must Have 主流程、关键页面/状态、核心异常路径 | 直接供 define 提取 |
| `partial` | 可访问但只覆盖部分页面或缺少异常/状态 | 允许继续，但必须在 requirements/design 中记录 UIUX risk 或 open question |
| `screenshot_only` | 只有截图 | 主流程截图覆盖完整时可继续，否则按 `partial` 处理，并记录无法确认交互细节 |
| `inaccessible` | 链接打不开、权限不足、文件损坏 | 视为缺材料，用户需补材料或授权 `ship-shape` |

### 用户授权生成线框

用户选择"按你的理解做线框 / 生成线框"时：
1. 覆写 `stages.ship-shape.status: pending`
2. 记录 `activation_mode: uiux_material_gate_insert`
3. 写入 `uiux_gate_user_sign_off`
4. 写入 `uiux_gate_signed_at`
5. 设置 `current_stage: ship-shape`
6. 完成后再回到 `ship-define`

### Inserted Shape 回流 Define Normalize 顺序

1. 先检查 `requirements.md` frontmatter，raw inbox 必须先 normalize
2. 再读取 `resource/README.md` 和 source documents
3. 再读取 `design-brief.md` 与 `resource/wireframes/`
4. 把 `design-brief.md` 作为 UIUX source，不覆盖 PRD source
5. 冲突写入 conflict/open question
6. 保持 B 的 `generation_mode: interview`、D 的 `generation_mode: prd_direct`

## 启动确认模板

NEW_FEATURE 启动确认必须包含：
- 简述功能名称和目标
- 标明识别到的场景（A/B/C/D/E）及起点阶段
- 标明识别到的范围（fullstack / backend_only / frontend_only）及跳过的阶段
- 列出将要经历的大阶段序列（含 Discover 是否激活）
- 预估涉及的技术领域
- 标明下一次需要用户确认的门禁时点
- 若组合为 `D + backend_only`，必须做材料类型确认
- 若场景为 E，必须额外按顺序展示场景 E 启动摘要
- **明确提示：本次确认只表示启动 ShipKit workflow 并进入 `<current_stage>`，不会开始编码；编码只能在 `ship-plan-review` 通过后进入 `ship-build`**
- 场景 E 的启动确认中也要补充：**即使用户确认 selected scope，也只进入 `ship-tech-discovery`，不会直接实现接口**
- 等待用户一句话确认（"好的""开始""go"等均视为确认）

## 初始化验证

### feature_meta_runtime.py

```bash
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init \
  --feature-dir <feature_dir> \
  --scenario greenfield \
  --project-context new_project
```

### validate_feature_artifacts.py

```bash
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
```

检查项：
- `meta.yml` 存在且合法
- `scenario` 合法
- `project_context` 合法（场景 E 必须是 existing_project）
- `technical_plan_source` 存在（场景 E）
- `selected_scope` 非空（场景 E）
- `evolve_source` 至少一种基线（场景 C）
- 场景 B/D 有 raw PRD inbox 或 resource 材料
- 场景 E 不创建 raw PRD inbox
