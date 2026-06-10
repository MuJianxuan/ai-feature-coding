# 新 ShipKit 交付验收清单

本清单把 `.docs/new-shipkit-design/` 的显式要求映射到 `new-skills/` 实际交付物。它用于交付审查，不是额外流程文档。

## 目标拆解

| 目标要求 | 交付证据 | 状态 |
|---|---|---|
| 所有新设计技能放到 `new-skills/` | `new-skills/ship-*/SKILL.md` 共 7 个；旧 `skills/` 未作为本次实现目录 | ✅ |
| 全新设计，不沿用旧 14 阶段 ShipKit | `ship-orchestrator/SKILL.md` 明确 4 阶段、单一 `meta.yml`、不创建旧细阶段 | ✅ |
| 按 `.docs/new-shipkit-design/` 完成技能创建 | `MANIFEST.yml` 映射设计职责；7 个技能覆盖 orchestrator/split/understand/design/build/spec/grill-me | ✅ |
| 确保技能完整性 | 每个 `SKILL.md` 包含触发、输入、流程、输出、门禁/阻塞、不做什么 | ✅ |
| 持续对抗性审查直到可交付 | validator 编译、happy path、负向测试；本清单记录覆盖关系 | ✅ |
| Design 参考模板机制按 `13-design-reference-template-plan.md` 实施 | `ship-design/SKILL.md`、`ship-orchestrator/SKILL.md`、`ship-grill-me/SKILL.md`、`ship-spec/SKILL.md`、`templates/design-reference/`、`validate_design.py`、`test_validators.py` | ✅ |

## 技能覆盖矩阵

| 设计文档要求 | 实施文件 | 覆盖点 |
|---|---|---|
| 技能清单：`ship-orchestrator`、`ship-split`、`ship-understand`、`ship-design`、`ship-build`、`ship-spec`、`ship-grill-me` | `MANIFEST.yml`、7 个 `SKILL.md` | 7 个技能全部存在 |
| 4 阶段 + 1 辅助技能 | `ship-orchestrator/SKILL.md`、`README.md` | `[Split] → Understand → Design → Build`，Spec 贯穿 |
| 4 种场景：quick_start/full_flow/prd_direct/split_first | `ship-orchestrator/SKILL.md`、`ship-grill-me/SKILL.md` | 场景识别和 grill-me 策略矩阵 |
| `meta.yml` 单一事实源和 feature 目录结构 | `ship-orchestrator/SKILL.md`、`templates/meta.yml.template`、`README.md` | current_stage/status/scenario/spec_refs/artifacts 等核心字段 |
| Understand 阶段 spec 加载、需求解析、requirements.md | `ship-understand/SKILL.md`、`templates/requirements.md.template`、`validate_requirements.py` | Domain、AC、NFR、约束、grill-me 触发 |
| Design 阶段 API Contract + 前后端方案合一 | `ship-design/SKILL.md`、`templates/design.md.template`、`validate_design.py` | API、数据模型、前端、后端、AC 覆盖、性能 |
| Design Reference Template 机制 | `ship-design/SKILL.md`、`ship-orchestrator/SKILL.md`、`ship-grill-me/SKILL.md`、`ship-spec/SKILL.md`、`templates/design-reference/`、`validate_design.py` | orchestrator 只记录模板意图；design 选择并记录 `design_template_ref/reason`；grill-me 审查错选/漏项/偏离；spec 优先于模板；validator 校验引用、存在性、正文一致、章节、占位符 |
| Design → Build 唯一用户确认门禁 | `ship-orchestrator/SKILL.md`、`ship-design/SKILL.md` | ready 后停止并询问 `[yes]/[modify]/[review]` |
| Build 阶段任务生成、实现顺序、验证报告 | `ship-build/SKILL.md`、`templates/build-plan.yml.template`、`templates/verification.md.template`、`validate_build.py` | 数据层→后端→前端→集成；AC 验证 |
| Split 依赖追踪和 TAPD/Jira 框架 | `ship-split/SKILL.md`、`templates/splits.yml.template` | `splits.yml`、`dependencies`、`blocked_by`、API 成功才写远程 id |
| spec 知识库、多项目隔离、规范沉淀 | `ship-spec/SKILL.md` | `.docs/spec`、`_shared` + project、60 分沉淀规则 |
| grill-me 精确触发、一次一个问题、先查仓库/spec | `ship-grill-me/SKILL.md` | blocking 判定、证据、推荐答案、输出给阶段技能 |
| 3 个核心 validator | `validate_requirements.py`、`validate_design.py`、`validate_build.py` | requirements/design/build 三类核心验证 |
| 当前阶段聚合验证 | `validate_current_stage.py` | 按 `meta.yml.current_stage` 调用对应核心 validator；不是第四个核心 validator |
| 性能和安全考量 | `ship-spec/SKILL.md`、`ship-build/SKILL.md`、`ship-orchestrator/SKILL.md` | 按阶段加载、避免敏感信息进入 spec、真实测试不被 validator 替代 |

## 已执行验证

```bash
python3 - <<'PY'
from pathlib import Path
for path in list(Path('new-skills/ship-orchestrator/scripts').glob('*.py')) + list(Path('new-skills/ship-orchestrator/tests').glob('*.py')):
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
print('all validator and test scripts compile')
PY
```

结果：`all validator and test scripts compile`（本次实现另以完整测试脚本覆盖编译路径）

```bash
python3 new-skills/ship-orchestrator/tests/test_validators.py
```

结果：

```text
PASS: valid requirements
PASS: valid design with template
PASS: valid build
PASS: valid current stage
PASS: loose YAML preserves quoted project template fragment
PASS: project template ref with fragment
PASS: requirements missing AC
PASS: requirements bad AC format
PASS: design uncovered AC
PASS: design missing error response
PASS: full_flow missing template ref
PASS: template id does not exist
PASS: non quick_start missing template section
PASS: design base sections must be top-level
PASS: ready design contains TBD
PASS: async-task missing required subsection
PASS: quick_start missing template only warns
PASS: build uncovered AC
PASS: build tests failed
PASS: build mixed passed and failed
All validator smoke tests passed.
```

## 已知边界

- 这是一套 skill 指令和验证脚本，不是独立 CLI 产品。
- 旧 `skills/ship-*` 仍存在；使用新设计时必须显式引用 `new-skills/`，避免加载旧技能。
- validator 做结构和覆盖性检查，不替代项目真实测试；`ship-build` 必须运行仓库自己的 test/lint/typecheck 并写入 `verification.md`。
- Design Reference Template 是 Design 阶段护栏，不是新阶段；内置模板 checklist 不替代项目 spec，也不替代 `ship-grill-me` 语义审查。
