# 新 ShipKit 技能集

这是按 `.docs/new-shipkit-design/` 从零实现的新 ShipKit 设计。它不修改、不依赖旧 `skills/` 目录；所有新技能和配套脚本都放在 `new-skills/` 下。

使用时应显式引用 `new-skills/ship-orchestrator` 或该目录下的具体 skill；仓库旧 `skills/ship-*` 仍然存在时，不要混用两套 ShipKit。

## 技能清单

| 技能 | 类型 | 作用 | 必需 |
|---|---|---|---|
| `ship-orchestrator` | 编排层 | 统一入口，识别场景，路由阶段，执行门禁 | 是 |
| `ship-split` | 可选前置 | 拆分大需求，生成 `splits.yml`，追踪依赖 | 可选 |
| `ship-understand` | 核心阶段 | 理解需求，加载 spec，产出 `requirements.md` | 是 |
| `ship-design` | 核心阶段 | 技术设计，选择 Design Reference Template，产出 `design.md`，等待用户确认 | 是 |
| `ship-build` | 核心阶段 | 实现、测试、AC 验证，产出 `build-plan.yml` 和 `verification.md` | 是 |
| `ship-spec` | 工具技能 | 管理 `.docs/spec/` 知识库，多项目隔离加载 | 是 |
| `ship-grill-me` | 质询助手 | 嵌入 Understand/Design，发现阻塞问题并逐个质询 | 是 |

## 核心流程

```text
[可选] ship-split
    ↓
ship-understand  → requirements.md(status: ready)
    ↓
ship-design      → design.md(status: ready) → 用户确认
    ↓
ship-build       → verification.md(all_ac_passed: true) → done
```

贯穿全程：`ship-spec` 按阶段加载规范；`ship-grill-me` 在 Understand/Design 中按场景触发。

## 目录结构

```text
new-skills/
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
│   │       ├── INDEX.md
│   │       ├── backend-service.md
│   │       ├── frontend-ui.md
│   │       ├── fullstack-feature.md
│   │       ├── async-task.md
│   │       ├── data-migration.md
│   │       ├── integration.md
│   │       └── config-change.md
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
current_stage: understand # understand | design | build | done
status: in_progress       # in_progress | blocked | completed
scenario: full_flow       # quick_start | full_flow | prd_direct | split_first
created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T14:30:00Z"
spec_refs: []
requested_design_template: "" # 可选：用户显式模板意图原话
design_template_ref: ""       # Design 阶段解析后的模板引用
design_template_reason: ""    # Design 阶段写入的选择依据
artifacts:
  requirements: requirements.md
  design: design.md
  build_plan: build-plan.yml
  verification: verification.md
```

## Design Reference Template

Design 阶段支持轻量参考模板机制：

- `ship-orchestrator` 只记录用户显式模板意图到 `requested_design_template`，不解析模板。
- `ship-design` 选择项目级模板或内置模板，写入 `design_template_ref` 和 `design_template_reason`。
- `design.md` 必须包含 `## 方案模板引用`；模板机器事实只存在 `meta.yml`，不写进 frontmatter。
- `full_flow`、`prd_direct`、`split_first` 子 feature 必须记录模板引用；`quick_start` 缺模板只 warning。
- 内置模板目录：`new-skills/ship-orchestrator/templates/design-reference/`。
- 模板只是 checklist，项目 spec 优先；validator 只查结构和占位符，不假装自己是架构师。

## 验证命令

```bash
python new-skills/ship-orchestrator/scripts/validate_requirements.py .docs/feature-YYYYMMDD-name
python new-skills/ship-orchestrator/scripts/validate_design.py .docs/feature-YYYYMMDD-name
python new-skills/ship-orchestrator/scripts/validate_build.py .docs/feature-YYYYMMDD-name
python new-skills/ship-orchestrator/scripts/validate_current_stage.py .docs/feature-YYYYMMDD-name
```

这些 validator 是结构和覆盖性检查，不替代项目自己的测试命令；`ship-build` 必须同时运行真实测试并把结果写入 `verification.md`。

设计要求的核心 validator 是 3 个：`validate_requirements.py`、`validate_design.py`、`validate_build.py`；`validate_current_stage.py` 只是聚合入口，不算第四个核心 validator。

## 自测

```bash
python3 new-skills/ship-orchestrator/tests/test_validators.py
```

该脚本覆盖 happy path 和负向样例：缺 AC、AC 格式错误、design 未覆盖 AC、design 缺错误响应、project 模板 fragment 解析、full_flow 缺模板引用、模板不存在、非 quick_start 缺 `方案模板引用`、基础章节必须是 `##` 顶层、ready 含 TBD、async-task 缺必填子章节、quick_start 缺模板 warning、build 未覆盖 AC、测试失败、passed 与 failed 混合出现。
