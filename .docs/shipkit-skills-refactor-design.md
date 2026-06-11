# ShipKit Skills 重构设计方案

状态：draft  
日期：2026-06-10  
目标：把当前 `skills/` 技能集重构为更适合团队和个人使用的、单一完整推进的技能开发工作流。

## 1. 已确认决策

| 决策 | 结论 | 依据 |
|---|---|---|
| 下一步动作 | 先产出设计文档，不直接修改 `skills/` | 用户确认“先写设计文档（推荐）”；当前路径、场景、meta schema 均存在耦合，直接改文件返工风险高。 |
| 工作流模式 | 只保留单一完整推进模式 | 用户确认“单一 full_flow”；当前 `ship-orchestrator`/`ship-understand`/`ship-design`/`ship-grill-me` 都显式区分 `quick_start/full_flow/prd_direct/split_first`。 |
| 新窗口阶段启动 | 阶段技能必须显式接收需求目录 | 用户确认“必须显式传目录”；当前 `ship-understand` 仍允许“读取或创建 feature 目录”，职责过宽。 |
| 需求来源 schema | 在 `meta.yml` 增加 `source_refs` 列表 | 用户确认“source_refs 列表”；当前 `meta.yml.template` 没有 PRD/UIUX/link/会议纪要等来源字段。 |
| TODO 保真 | 每个技能启动后必须创建/恢复 agent TODO | 用户明确要求“必须提示调用 agent 的 todo 工具创建好 TODO”；当前各 `SKILL.md` 未定义 TODO preflight。 |
| workspace 范围 | 创建需求目录时先读 `.docs/ship/project.yml`，再询问用户确认单项目/多项目组和涉及项目；写入 `meta.yml.workspace_mode/workspace_name/projects` | 用户确认“先读配置再问”“workspace + projects”；`ship-spec` 已定义 `workspace_mode/projects`，并要求只加载 `meta.yml.projects` 指定项目的 spec。 |

## 2. 当前工件事实与问题

### 2.1 当前能力

- `skills/` 下已有 7 个技能：`ship-orchestrator`、`ship-split`、`ship-understand`、`ship-design`、`ship-build`、`ship-spec`、`ship-grill-me`。
- 当前主流程是 `[可选] ship-split → ship-understand → ship-design → ship-build`。
- `meta.yml` 是单一事实源，当前包含 `feature_name/current_stage/status/scenario/spec_refs/artifacts/design_template_*`。
- Design Reference Template 已有内置模板与 `validate_design.py` 结构校验。

### 2.2 已发现问题

| 问题 | 证据 | 影响 |
|---|---|---|
| 文档路径过期 | `skills/README.md` 与 `skills/MANIFEST.yml` 仍写实现根目录 `new-skills`；仓库未找到 `new-skills/`。 | 用户/agent 可能引用不存在路径。 |
| 测试路径失效 | 执行 `python3 skills/ship-orchestrator/tests/test_validators.py` 报 `ModuleNotFoundError: No module named '_lib'`；测试文件中 `SCRIPTS = ROOT / "new-skills" / ...`。 | 当前 validator 自测不可运行。 |
| 多场景与目标冲突 | `ship-orchestrator` 定义 `quick_start/full_flow/prd_direct/split_first`；`validate_design.py` 以 scenario 判断模板是否必需。 | 与“只需要一个模式，不需要快速模式”冲突。 |
| 阶段职责不够硬 | `ship-understand` 流程第 1 步允许“读取或创建 feature 目录”。 | 新窗口阶段技能可能误创建/误恢复目录。 |
| meta 无需求来源 | `meta.yml.template` 没有 `source_refs`。 | `ship-understand` 无法仅根据需求目录恢复 PRD/UIUX/link 等输入。 |
| TODO 未制度化 | 各 `SKILL.md` 没有“启动后创建 TODO”的硬规则。 | 长流程中 agent 容易遗忘阶段任务。 |
| workspace/project scope 未前置 | `ship-spec` 已定义 `.docs/ship/project.yml` 和“只加载 `meta.yml.projects` 指定项目的 spec”，但当前 `meta.yml` schema 没有 `workspace_mode/workspace_name/projects`。 | 多项目组根目录下推进需求时，后续探索和 spec 加载范围不稳定。 |

## 3. 目标工作流

### 3.1 核心原则

1. **一个模式**：只要进入 ShipKit feature flow，就走完整流程：`orchestrator → understand → design → build → done`。
2. **入口与阶段分离**：
   - `ship-orchestrator` 只负责访谈、创建/恢复需求目录、写 `meta.yml`、路由和门禁。
   - `ship-understand/design/build` 都必须由用户提供 `feature_dir`，不自动猜、不自动创建。
3. **meta.yml 是跨窗口契约**：新窗口不依赖上一窗口对话记忆，只依赖 `feature_dir/meta.yml` 与 artifact 文件。
4. **TODO 是会话内保真机制**：每个技能加载后必须先创建/恢复该阶段 TODO，再执行阶段步骤。
5. **grill-me 是阻塞质询机制**：Understand 和 Design 都必须做 blocking review；只问阻塞决策，且必须附证据和推荐答案。
6. **Design → Build 仍是唯一硬用户确认门禁**：设计 ready 后必须停下等待用户明确确认。
7. **workspace/project scope 前置**：创建需求目录时确认当前工作区是 `single_project` 还是 `project_group`，并把需求涉及的项目列表写入 `meta.yml.projects`，后续所有阶段以此限定探索和 spec 加载范围。

### 3.2 推荐目录结构

```text
.docs/feature-YYYYMMDD-slug/
├── meta.yml
├── requirements.md
├── design.md
├── build-plan.yml
├── verification.md
└── resource/
    ├── README.md              # 可选：人工说明来源文件
    ├── prd.md                 # 可选：PRD 快照
    ├── uiux.md                # 可选：UI/UX 说明或截图索引
    └── links.md               # 可选：外部链接清单
```

## 4. meta.yml 目标 schema

建议用 `workflow: full_flow` 替代 `scenario`，表达“单一完整流程”，但不再承载分支逻辑。

```yaml
feature_name: "{{FEATURE_NAME}}"
workflow: full_flow
workspace_mode: single_project # single_project | project_group
workspace_name: "{{WORKSPACE_NAME}}"
projects: []                # single_project 可为空或写当前项目名；project_group 必须至少 1 个项目名
current_stage: understand # understand | design | build | done
status: in_progress       # in_progress | blocked | completed
created_at: "{{ISO_TIMESTAMP}}"
updated_at: "{{ISO_TIMESTAMP}}"

source_refs:
  - id: SRC-001
    type: prd              # prd | uiux | link | issue | meeting | note | screenshot | other
    title: "{{SOURCE_TITLE}}"
    path_or_url: "resource/prd.md"
    role: primary          # primary | supporting | constraint
    status: available      # available | inaccessible | stale | needs_user
    notes: ""

spec_refs: []
requested_design_template: ""
design_template_ref: ""
design_template_reason: ""

artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md

# blocked_reason: awaiting_grill_answers | awaiting_user_confirmation | test_failures | missing_feature_dir | missing_source
# parent_split_id: ""
# split_id: ""
# split_dependency: []
# build_approved_at: ""      # 用户确认进入 Build 后由 orchestrator 写入
# build_approved_by: ""      # user | product_owner | tech_lead | other
# build_approval_note: ""    # 记录确认原话或摘要
```

### schema 说明

- `source_refs` 只登记来源，不把大段 PRD 塞进 `meta.yml`。
- 外部链接如果无法访问，应写 `status: inaccessible`，并由阶段技能向用户索要可读快照。
- `workflow: full_flow` 是兼容性和可读性字段，不再允许 `quick_start/prd_direct/split_first` 分支。
- `split` 不再是 scenario；`ship-split` 是独立前置分析技能，只产出拆分建议，确认后的子 feature 目录创建统一交回 `ship-orchestrator` 执行。
- `workspace_mode/workspace_name/projects` 是跨窗口的调研范围契约；多项目组根目录下，Understand/Design/Build/Spec 都只能围绕 `projects` 指定项目展开，除非用户确认扩大范围。
- orchestrator 创建需求目录时先读取 `.docs/ship/project.yml`：若存在，用其中 `workspace_mode/workspace_name/projects` 作为推荐答案；若不存在，再基于仓库事实和用户回答创建本需求自己的 workspace scope。
- workspace 项目名校验规则：若 `.docs/ship/project.yml` 存在，`meta.yml.projects` 必须是 `project.yml.projects` 的子集；若不存在且为 `project_group`，orchestrator 必须确认每个项目名能对应到仓库内项目目录或明确记录用户提供的项目路径，否则阻塞为 `missing_workspace_scope`。

## 5. 技能职责重构

### 5.1 ship-orchestrator

职责收敛为：

1. 判断是否需要进入 ShipKit feature flow；普通问答/小修 bug 不强行进入。
2. 先读取 `.docs/ship/project.yml`，拿到 workspace 默认配置；若不存在，记录为待确认信息。
3. 固定访谈并确认三类创建信息：需求目录名、workspace 类型/涉及项目、需求来源。
4. 收集并登记 `source_refs`：PRD、UIUX、链接、截图、issue、会议纪要等。
5. 创建 `.docs/feature-*` 目录与基础 artifacts 占位文件，并把 `workspace_mode/workspace_name/projects/source_refs` 写入 `meta.yml`。
6. 创建/恢复 orchestrator TODO。
7. 处理 Design → Build 确认：收到用户明确确认后，写入 `current_stage: build`、`status: in_progress`，清理 `blocked_reason`，并记录 `build_approved_at/build_approved_by/build_approval_note`。
8. 输出新窗口 handoff 指令，例如：

```text
需求目录已创建：.docs/feature-20260610-example
当前阶段：understand
workspace：project_group
涉及项目：web, api
下一步请在新窗口调用 ship-understand，并明确传入 feature_dir：
.docs/feature-20260610-example
```

固定访谈问题：

1. **需求目录名**：基于需求标题推荐 `.docs/feature-YYYYMMDD-slug`，允许用户改名。
2. **workspace 类型/项目范围**：
   - 若 `.docs/ship/project.yml` 存在，先展示检测到的 `workspace_mode/workspace_name/projects`，请用户确认本需求涉及哪些项目。
   - 若 `single_project`，`projects` 可为空或写当前项目名；后续探索默认整个当前项目。
   - 若 `project_group`，必须让用户给出本需求涉及的项目名列表；后续探索和 spec 加载只围绕这些项目。
   - 若 `.docs/ship/project.yml` 存在，用户给出的项目名必须属于 `project.yml.projects`；若不属于，先修正项目名或补充 workspace 配置。
   - 若 `.docs/ship/project.yml` 不存在但用户选择 `project_group`，必须确认每个项目名能对应到仓库内项目目录；无法确认时停止创建并要求用户补充项目名/路径。
3. **需求来源**：登记至少一个 primary `source_refs`；可以是 PRD、UIUX、link、issue、meeting、note、screenshot 或 other。

不作为固定必问题：Design 模板意图。只有用户主动提出或需求材料明确要求时，orchestrator 才把原话写入 `requested_design_template`。

不做：

- 不生成 `requirements.md` 正文。
- 不解析 Design 模板。
- 不判断 quick/prd/split 场景。
- 不在 Design 确认前修改业务代码。

### 5.2 ship-understand

硬前置：

- 用户必须提供 `feature_dir`。
- 必须读取 `feature_dir/meta.yml`。
- 必须创建/恢复本阶段 TODO。
- 若 `source_refs` 为空或 primary 来源不可读，先进入阻塞质询。

推荐 TODO：

1. 加载需求目录与 `meta.yml`。
2. 读取 `source_refs` 与 `resource/` 来源材料。
3. 根据 `workspace_mode/projects` 限定仓库探索范围；多项目组只探索本需求涉及项目及 `_shared`。
4. 加载 Understand 阶段 spec。
5. 探索仓库中相关现有功能。
6. 提取目标、边界、Domain、AC、NFR、约束。
7. 调用 `ship-grill-me` 做 blocking 质询。
8. 写入 `requirements.md(status: ready)`。
9. 运行 `validate_requirements.py <feature_dir>`。
10. 更新 `meta.yml.current_stage: design`。

关键变化：

- 删除 `quick_start/prd_direct/split_first` 触发差异。
- PRD/UIUX/link 只是 `source_refs.type`，不是流程模式。
- 不创建 feature 目录；缺目录即停止。

### 5.3 ship-design

硬前置：

- 用户必须提供 `feature_dir`。
- `requirements.md` 必须 `status: ready`。
- 必须创建/恢复本阶段 TODO。

推荐 TODO：

1. 加载需求目录、`meta.yml`、`requirements.md`。
2. 运行 `validate_requirements.py <feature_dir>`。
3. 根据 `workspace_mode/projects` 限定技术探索、代码阅读和架构影响面。
4. 探索项目结构与相关代码。
5. 加载 Design 阶段 spec。
6. 解析 `requested_design_template`，选择 Design Reference Template。
7. 针对阻塞设计决策采访用户。
8. 编写推荐技术方案 `design.md`。
9. 调用 `ship-grill-me` 做对抗式设计审查。
10. 运行 `validate_design.py <feature_dir>`。
11. 标记 `design.md(status: ready)`。
12. 更新 `meta.yml.status: blocked`、`blocked_reason: awaiting_user_confirmation`。
13. 停止并询问是否进入 Build。
14. 输出 handoff：要求用户回到/调用 `ship-orchestrator` 处理 Build approval；`ship-design` 自身不得把 `current_stage` 改为 `build`，也不得直接启动 `ship-build`。

关键变化：

- Design Reference Template 对所有 ShipKit feature 都是必需事实，不再有 quick warning。
- `ship-grill-me` 在 Design 阶段总是执行。
- `design.md` 必须保留“方案模板引用”和“设计审查记录”。

### 5.4 ship-build

硬前置：

- 用户必须提供 `feature_dir`。
- `meta.yml.current_stage: build`。
- `meta.yml.status: in_progress`。
- `meta.yml.build_approved_at` 已由 orchestrator 写入。
- `design.md(status: ready)`。
- 必须创建/恢复本阶段 TODO。

推荐 TODO：

1. 加载 `meta.yml`、`requirements.md`、`design.md`。
2. 根据 `workspace_mode/projects` 限定实现和测试命令选择；多项目组只运行相关项目及必要集成测试。
3. 运行 `validate_design.py <feature_dir>`。
4. 生成 `build-plan.yml`。
5. 按依赖顺序实现代码。
6. 按任务运行相关测试。
7. 运行项目真实 test/lint/typecheck。
8. 写 `verification.md`，逐项映射 AC。
9. 运行 `validate_build.py <feature_dir>`。
10. 更新 spec existing-features 或提出沉淀建议。
11. 更新 `meta.yml.current_stage: done`、`status: completed`。

### 5.5 ship-split

定位调整：独立前置分析技能，不再写 `scenario: split_first`，也不直接创建子 feature 目录。

输出：

- 只生成 `splits.yml` 与拆分建议。
- 用户确认后，把“批量创建子 feature”的动作交回 `ship-orchestrator` 执行。
- `ship-orchestrator` 为每个子 feature 创建目录和 `meta.yml`，并统一写 `workflow: full_flow`。
- 依赖仍用 `parent_split_id/split_id/split_dependency/blocked_reason` 表达。
- `splits.yml.template` 也必须同步调整：`ship-split` 可写 `suggested_slug`、`suggested_feature_name`、依赖和优先级；不得默认写实际 `feature_dir`。实际 `created_feature_dir` 只能由 orchestrator 批量创建子 feature 后回填，默认应为空。

### 5.6 ship-grill-me

定位保持：嵌入式质询助手，不是独立阶段。

变化：

- 删除按 scenario 的触发矩阵。
- Understand 和 Design 都必须执行 blocking review。
- 每个问题必须包含：当前阻塞、已检查证据、推荐答案、影响。
- 一次只问当前最关键的阻塞问题。

### 5.7 ship-spec

定位保持：项目事实与规范知识库。

变化：

- 删除“quick_start 可接受”的表述。
- 无 `.docs/spec` 时仍可 warning，但 full flow 需要在 requirements/design 中记录缺失影响。
- 明确 spec 与 `source_refs` 的边界：source 是需求输入，spec 是项目约束。
- 与 workspace scope 对齐：若 `.docs/ship/project.yml` 存在，orchestrator 用它作为创建需求时的推荐配置；阶段技能加载 spec 时以 `meta.yml.workspace_mode/projects` 为准。
- 多项目组下永远加载 `_shared`，再加载 `meta.yml.projects` 指定项目；不得让未涉及项目的 spec 污染设计和实现。

## 6. Validator 与测试改造计划

### 6.1 路径修复

- `skills/README.md`、`skills/MANIFEST.yml`、`skills/ACCEPTANCE.md`：把 `new-skills` 改为当前实际根 `skills`。
- `skills/ship-orchestrator/tests/test_validators.py`：`SCRIPTS` 改为当前 `skills/ship-orchestrator/scripts`。

### 6.1.1 Meta parser 前置

在大规模修改技能文案前，先让工具链理解新 `meta.yml`：

- 新增或替换为 `parse_meta_yaml()`，支持顶层标量、顶层 list、list-of-map，以及读取 `.docs/ship/project.yml` 所需的 `projects` 列表。
- 先在 `test_validators.py` 加入新 meta fixture，确保 parser 能读到 `workflow/workspace_mode/projects/source_refs/build_approved_at`。
- 后续 validator 和技能文案改造都依赖这个解析能力；不得把 parser 放到最后才改。

### 6.2 scenario 移除

- `meta.yml.template`：删除 `scenario`，新增 `workflow: full_flow`、`workspace_mode/workspace_name/projects` 与 `source_refs`。
- `validate_design.py`：删除 `TEMPLATE_REQUIRED_SCENARIOS` 和 quick_start warning；所有 ShipKit feature 默认必须有 `design_template_ref` 与 `## 方案模板引用`。
- `test_validators.py`：删除 `quick_start missing template only warns` 正向用例，改为“missing template fails”；新增 workspace scope fixture。
- `splits.yml.template`：把实际 `feature_dir` 改为 `suggested_slug` 或空的 `created_feature_dir`，避免 split 阶段绕过 orchestrator 建目录。

### 6.3 source_refs 校验

建议不新增第四个核心 validator，避免扩大工具面；把基础检查放入现有阶段 validator。但实施前必须先解决解析能力：

- `_lib.parse_loose_yaml` 当前只解析顶层 `key: value` 且跳过缩进行，不能读取 `source_refs` 的 list-of-map；也不能稳定读取复杂 workspace scope；需要新增最小 YAML 解析能力，或引入明确可用的 YAML 解析依赖。
- 推荐保持零依赖：新增 `parse_meta_yaml()`，只支持本项目需要的顶层标量、顶层 list、list-of-map。
- `validate_requirements.py`：读取 `meta.yml`，若 `source_refs` 为空则 error；若 primary source 的 `status` 为 `inaccessible/needs_user` 则 error；若 `workspace_mode: project_group` 但 `projects` 为空则 error；若 `.docs/ship/project.yml` 存在，则 `meta.yml.projects` 必须是配置项目子集。
- `test_validators.py`：新增 5 类用例：valid primary source 通过、缺 `source_refs` 失败、primary source 不可用失败、project_group 缺 projects 失败、projects 不属于 project.yml 失败。
- `validate_current_stage.py`：聚合时透传对应阶段错误。
- `validate_build.py`：读取 `meta.yml`，若缺少 `build_approved_at` 或 `current_stage` 不是 `build/done`，不得通过 Build 验证；`test_validators.py` 增加缺 Build approval 失败用例。

### 6.4 TODO 规则校验

TODO 是 agent 行为，不适合用 Python validator 静态验证运行时工具调用。建议用文档验收：

- 所有可独立调用的 `ship-*` 技能必须有 `## TODO preflight` 章节：`ship-orchestrator`、`ship-split`、`ship-understand`、`ship-design`、`ship-build`、`ship-spec`。
- `ship-grill-me` 作为嵌入式 helper 时不单独创建新 TODO，但必须更新父阶段 TODO/审查记录；若被用户单独调用，也必须创建自己的 TODO。
- 章节必须明确“开始阶段工作前调用可用 TODO 工具创建/恢复阶段任务”。
- 验收时用文本 grep 检查 `TODO preflight`、`TaskCreate` 或“todo 工具”。

## 7. 建议实施顺序

1. 修正文档与测试路径：先让现有测试能跑。
2. 前置改 parser/tests：新增 `parse_meta_yaml()`，让测试 fixture 能读取 `workflow/workspace_mode/projects/source_refs/build_approved_at`。
3. 改 `meta.yml.template`：引入 `workflow/workspace_mode/workspace_name/projects/source_refs/build_approved_*`，删除 `scenario`。
4. 改 validator/tests：移除 scenario 分支，新增 source_refs、workspace scope、project.yml 子集校验、Build approval 校验。
5. 改 orchestrator：单一 full flow、读取 `.docs/ship/project.yml`、固定访谈三问、只创建目录和 meta、处理 Build approval、输出新窗口 handoff。
6. 改阶段技能：强制 feature_dir、TODO preflight、按 workspace/projects 限定调研范围、删除场景分支；Design 完成后必须 handoff 回 orchestrator。
7. 改 split/grill/spec：split 不建目录且更新 `splits.yml.template`；grill/spec 删除 quick/prd/split 场景矩阵与 quick_start 文案，并让 spec 加载服从 `meta.yml.projects`。
8. 运行测试并更新 ACCEPTANCE。

## 8. 验收标准

- AC-1：`skills/` 内除明确标注“旧设计/历史背景”的迁移说明外，不再出现 `quick_start/prd_direct/split_first` 作为流程模式，也不再保留“4 种场景识别”“按场景触发”“quick 可接受”等多模式语义表述。
- AC-2：`skills/` 内不再引用不存在的 `new-skills/` 执行路径。
- AC-3：`meta.yml.template` 包含 `workflow: full_flow`、`workspace_mode/workspace_name/projects`、`source_refs` 和 `build_approved_*`，不包含 `scenario`。
- AC-4：orchestrator 创建需求目录前必须先读取 `.docs/ship/project.yml`；若存在，固定访谈必须基于该配置给出推荐答案并让用户确认。
- AC-5：`workspace_mode: project_group` 时，`projects` 必须至少包含 1 个项目名；若 `.docs/ship/project.yml` 存在，`meta.yml.projects` 必须是配置项目子集；阶段技能和 `ship-spec` 必须据此限定探索/spec 加载范围。
- AC-6：`ship-understand`、`ship-design`、`ship-build` 都明确要求用户提供 `feature_dir`。
- AC-7：`ship-orchestrator` 是唯一创建 feature 目录和初始 `meta.yml` 的技能；`ship-split` 只产出 `splits.yml`，不直接建子 feature。
- AC-8：`splits.yml.template` 不再默认写实际 `feature_dir`；只允许 `suggested_slug` 或默认空的 `created_feature_dir`，由 orchestrator 创建后回填。
- AC-9：所有可独立调用的 `ship-*` 技能都有 `TODO preflight`，并列出阶段 TODO；`ship-grill-me` 嵌入调用时必须更新父阶段 TODO/审查记录，单独调用时也必须创建 TODO。
- AC-10：Design 阶段对所有 ShipKit feature 都要求 `design_template_ref` 和 `## 方案模板引用`。
- AC-11：Design → Build 确认必须持久化到 `meta.yml.build_approved_at/build_approved_by/build_approval_note`；`ship-design` 必须 handoff 回 orchestrator 处理确认，`ship-build` 缺 `build_approved_at` 必须停止。
- AC-12：`validate_requirements.py` 对缺失 `source_refs` 报错，对 primary source `inaccessible/needs_user` 报错，对 `project_group` 缺 `projects` 报错，对 `projects` 不属于 `.docs/ship/project.yml` 配置报错，对 valid primary source + valid project scope 通过。
- AC-13：`python3 skills/ship-orchestrator/tests/test_validators.py` 通过。
- AC-14：`README.md`、`MANIFEST.yml`、`ACCEPTANCE.md` 与实际 `skills/` 路径一致。
- AC-15：新窗口 handoff 文案明确包含 `feature_dir`、下一阶段技能名、`workspace_mode` 和 `projects`。

## 9. 对抗式审查

### Round 1：单一 full_flow 会不会太重？

质疑：小改动也走完整流程，会拖慢个人使用。  
回应：ShipKit 不应覆盖普通问答/小修 bug。`ship-orchestrator` 的第一个判断仍是“是否进入 feature flow”；一旦进入 feature flow，就完整推进，避免 quick mode 造成需求/设计缺口。

结论：保留“非 feature 不进入 ShipKit”的逃生口；删除 ShipKit 内部 quick mode。

### Round 2：强制 feature_dir 会不会降低易用性？

质疑：用户开新窗口时可能忘记目录。  
回应：这正是 orchestrator handoff 要解决的问题。阶段技能自动扫描 `.docs/feature-*` 的风险更高，尤其是团队并行多个需求时会误读。

结论：阶段技能缺 `feature_dir` 必须停止并提示用户提供；不自动猜。

### Round 3：`source_refs` 会不会把 meta.yml 变复杂？

质疑：来源多时 meta 会膨胀。  
回应：`source_refs` 只放索引和状态，不放正文；正文放 `resource/` 或外部链接。这样新窗口可以先读 meta 得知输入在哪里，同时避免 meta 变成 PRD。

结论：采用轻量 `source_refs`；大内容留在 resource 或链接。

### Round 4：TODO preflight 能否被 validator 验证？

质疑：Python validator 无法证明 agent 真的调用了 TODO 工具。  
回应：这是运行时行为约束，不应伪装成文件结构校验。技能说明必须硬性要求；执行时由 agent 遵循，交付审查用文本验收和实际运行观察。

结论：在所有阶段技能中写成 MUST；不新增伪验证器。

### Round 5：删除 scenario 后 split/prd_direct 的差异如何表达？

质疑：PRD 直通和拆分确实有不同输入形态。  
回应：输入形态不等于流程模式。PRD/UIUX/link 用 `source_refs.type` 表达；拆分用独立 `ship-split` 产出拆分建议，再由 orchestrator 创建子 feature；子 feature 仍走完整流程。

结论：删除 scenario 分支；保留 source 和 split 元数据。

### Round 6：所有设计都要求模板，会不会模板化过度？

质疑：简单后端配置改动也要 Design Reference Template。  
回应：模板是 checklist，不是固定文档；已有 `config-change` 等轻量模板。要求模板引用的价值是让 agent 明确自己选了什么检查清单，并说明不涉及项。

结论：保留“所有 ShipKit feature 必须选择模板”；通过轻量模板控制成本。

### Round 7：路径从 new-skills 改为 skills 是否可能破坏历史设计说明？

质疑：README/ACCEPTANCE 可能是在描述旧交付计划。  
回应：当前仓库实际没有 `new-skills/`，测试也因此失败。面向当前工件的可交付状态应以实际路径为准；历史说明可在迁移说明中保留，但不能作为执行路径。

结论：执行路径统一为 `skills/`；如需保留历史，放入“历史背景”而不是命令示例。

### Round 8：`source_refs` 嵌套 YAML 当前 parser 读不了怎么办？

质疑：当前 `_lib.parse_loose_yaml` 跳过缩进行，只能读顶层字段，无法校验 `source_refs` 的 `role/status`。  
回应：这是实施阻塞点，不能只改 schema。实施计划必须先扩展解析能力，推荐新增零依赖 `parse_meta_yaml()`，覆盖顶层标量、顶层 list、list-of-map，并用 validator 测试锁定。

结论：`source_refs` 改造必须与 parser/test 同步交付。

### Round 9：Design → Build 确认跨窗口会不会丢？

质疑：如果用户在一个窗口确认 Build，另一个窗口启动 `ship-build`，仅靠对话记忆会丢失确认事实。  
回应：确认事实必须持久化到 `meta.yml`。orchestrator 收到确认后写 `current_stage: build/status: in_progress/build_approved_at/build_approved_by/build_approval_note`；Build 只信 meta。

结论：Build 阶段不得接受“对话里确认过”作为唯一依据。

### Round 10：workspace scope 每次都问会不会繁琐？

质疑：创建每个需求都问单项目/多项目和项目名，可能增加心智负担。  
回应：先读 `.docs/ship/project.yml`，把仓库已有配置作为推荐答案；用户只需确认或修正。只有 `project_group` 且无法确定需求涉及项目时才阻塞。这样既避免重复询问仓库已有答案，也避免多项目组下误探索无关项目。

结论：workspace scope 是创建需求目录阶段的固定确认项，但不是盲问；必须“先读配置，再给推荐，再确认”。

### Round 11：parser 和 validator 放到最后会不会造成实施断层？

质疑：如果先改技能文案和模板，后改 parser/validator，中途会出现新 meta 已被要求、工具链却读不了的断层。  
回应：实施顺序必须前置 parser 和测试 fixture。先让 `parse_meta_yaml()` 能读新 schema，再改 template、validator 和技能文案。

结论：parser/tests 是 schema 迁移的第一依赖，不得后置。

### Round 12：项目名写错时如何避免错误探索？

质疑：`project_group` 只要求 projects 非空还不够；项目名填错会导致 spec 缺失或探索范围错误。  
回应：若 `.docs/ship/project.yml` 存在，`meta.yml.projects` 必须是配置项目子集；若配置不存在，orchestrator 必须确认项目名能对应仓库目录，否则阻塞。

结论：workspace scope 不只是记录字段，还必须有项目名合法性校验。

### Round 13：split 模板会不会绕过 orchestrator 建目录？

质疑：当前 `splits.yml.template` 仍有 `feature_dir`，即使改了 `ship-split/SKILL.md`，模板也会诱导 split 阶段预创建目录。
回应：模板必须同步改为 `suggested_slug` 或空 `created_feature_dir`；实际 feature 目录只能由 orchestrator 创建后回填。

结论：`ship-split` 职责收敛必须覆盖 `splits.yml.template`。

## 10. 下一步安全动作

等待用户确认本设计后，再修改 `skills/` 文件。建议实施时按第 7 节顺序进行，并在每一步后运行/更新对应 validator 测试。

当前设计已完成多轮独立和自检式对抗审查，并回补了交付阻塞点：`ship-split` 建目录职责冲突、`splits.yml.template` 耦合、`source_refs` parser 能力缺口、parser/validator 实施顺序倒置、Design → Build 确认持久化与 handoff、workspace 项目名合法性校验、`source_refs`/workspace 验收缺口、`new-skills` 路径失效、多模式语义残留。
