# ShipKit 技能集

这套技能把 `skills/` 重构为单一完整推进的 ShipKit feature flow。它不覆盖普通问答或小修 bug；一旦进入 ShipKit feature flow，就按完整流程推进。

## 技能清单

| 技能 | 类型 | 作用 | 必需 |
|---|---|---|---|
| `ship-orchestrator` | 编排层 | 访谈、创建/恢复 feature 目录、维护 `meta.yml`、路由阶段、持久化 Build approval | 是 |
| `ship-split` | 可选前置 | 拆分大需求，只生成 `splits.yml` 建议，不创建 feature 目录 | 可选 |
| `ship-understand` | 核心阶段 | 必须接收 `feature_dir`，产出 `requirements.md(status: ready)` | 是 |
| `ship-design` | 核心阶段 | 必须接收 `feature_dir`，选择 Design Reference Template，产出 `design.md(status: ready)` 并 handoff 回 orchestrator | 是 |
| `ship-build` | 核心阶段 | 必须接收 `feature_dir` 和持久化 Build approval，实现、测试、验证 AC | 是 |
| `ship-spec` | 工具技能 | 管理 `.docs/spec/` 知识库，按 `meta.yml.projects` 隔离加载 | 是 |
| `ship-grill-me` | 质询助手 | 嵌入 Understand/Design，执行 blocking review | 是 |

## 核心流程

```text
[可选] ship-split（只产出拆分建议）
    ↓
ship-orchestrator → 创建/恢复 feature_dir + meta.yml(workflow: full_flow)
    ↓
ship-understand   → requirements.md(status: ready)
    ↓
ship-design       → design.md(status: ready) → handoff 回 orchestrator
    ↓
ship-orchestrator → 持久化 build_approved_*
    ↓
ship-build        → verification.md(all_ac_passed: true) → done
```

贯穿全程：`ship-spec` 按阶段和 workspace scope 加载规范；`ship-grill-me` 在 Understand/Design ready 前必须执行 blocking review。

## 目录结构

```text
skills/
├── README.md
├── MANIFEST.yml
├── ACCEPTANCE.md
├── ship-orchestrator/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── _lib.py
│   │   ├── validate_requirements.py
│   │   ├── validate_design.py
│   │   ├── validate_build.py
│   │   └── validate_current_stage.py
│   ├── templates/
│   │   ├── meta.yml.template
│   │   ├── requirements.md.template
│   │   ├── design.md.template
│   │   ├── build-plan.yml.template
│   │   ├── verification.md.template
│   │   ├── splits.yml.template
│   │   └── design-reference/
│   └── tests/
│       └── test_validators.py
├── ship-split/SKILL.md
├── ship-understand/SKILL.md
├── ship-design/SKILL.md
├── ship-build/SKILL.md
├── ship-spec/SKILL.md
└── ship-grill-me/SKILL.md
```

## 单一事实源

Feature 状态以 `.docs/feature-*/meta.yml` 为单一事实源：

```yaml
feature_name: "用户登录"
workflow: full_flow
workspace_mode: single_project # single_project | project_group
workspace_name: "my-workspace"
projects: []
current_stage: understand # understand | design | build | done
status: in_progress # in_progress | blocked | completed
created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T14:30:00Z"
source_refs:
  - id: SRC-001
    type: prd
    title: "登录 PRD"
    path_or_url: "resource/prd.md"
    role: primary
    status: available
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
# build_approved_at: ""
# build_approved_by: ""
# build_approval_note: ""
```

## Design Reference Template

Design 阶段使用轻量参考模板机制：

- `ship-orchestrator` 只记录用户显式模板意图到 `requested_design_template`，不解析模板。
- `ship-design` 选择项目级模板或内置模板，写入 `design_template_ref` 和 `design_template_reason`。
- 所有 ShipKit feature 都必须记录 `design_template_ref`。
- `design.md` 必须包含 `## 方案模板引用`；模板机器事实只存在 `meta.yml`，不写进 frontmatter。
- 内置模板目录：`skills/ship-orchestrator/templates/design-reference/`。
- 模板只是 checklist，项目 spec 优先；validator 只查结构和占位符，不替代架构审查。

## 验证命令

```bash
python3 skills/ship-orchestrator/scripts/validate_requirements.py .docs/feature-YYYYMMDD-name
python3 skills/ship-orchestrator/scripts/validate_design.py .docs/feature-YYYYMMDD-name
python3 skills/ship-orchestrator/scripts/validate_build.py .docs/feature-YYYYMMDD-name
python3 skills/ship-orchestrator/scripts/validate_current_stage.py .docs/feature-YYYYMMDD-name
```

这些 validator 是结构和覆盖性检查，不替代项目自己的测试命令；`ship-build` 必须同时运行真实测试并把结果写入 `verification.md`。

## 自测

```bash
python3 skills/ship-orchestrator/tests/test_validators.py
```

该脚本覆盖 happy path 和负向样例：新 meta parser、source_refs、workspace scope、project.yml 子集、Design 模板必填、缺模板失败、Build approval、AC 覆盖、测试失败等。
