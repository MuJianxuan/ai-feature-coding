# ShipKit Skills 重构验收清单

本清单把 `.docs/shipkit-skills-refactor-design.md` 的 AC-1 到 AC-15 映射到 `skills/` 实际工件。它用于交付审查，不是额外流程文档。

## 验收映射

| AC | 要求 | 证据 |
|---|---|---|
| AC-1 | `skills/` 内不再保留多流程模式语义 | `ship-orchestrator/SKILL.md`、`ship-understand/SKILL.md`、`ship-design/SKILL.md`、`ship-grill-me/SKILL.md` 均写成 `workflow: full_flow` 单一完整推进；全文 grep 验证无旧多模式关键词 |
| AC-2 | 不再引用不存在的执行路径 | `README.md`、`MANIFEST.yml`、测试脚本均使用 `skills/`；全文 grep 验证无旧实现根路径字符串 |
| AC-3 | `meta.yml.template` 新 schema | `ship-orchestrator/templates/meta.yml.template` 包含 `workflow`、`workspace_mode`、`workspace_name`、`projects`、`source_refs`、`build_approved_*`，不包含旧流程分支字段 |
| AC-4 | orchestrator 创建前读取 project.yml | `ship-orchestrator/SKILL.md` 的职责、TODO preflight、固定访谈均要求先读 `.docs/ship/project.yml` 并给推荐答案让用户确认 |
| AC-5 | workspace scope 校验与阶段隔离 | `validate_requirements.py` 校验 project group projects 和 project.yml 子集；`ship-understand/design/build/spec` 均要求按 `meta.yml.projects` 限定范围 |
| AC-6 | 阶段技能必须提供 feature_dir | `ship-understand/SKILL.md`、`ship-design/SKILL.md`、`ship-build/SKILL.md` 的“硬前置”均明确要求用户提供 `feature_dir` |
| AC-7 | 只有 orchestrator 创建 feature 目录 | `ship-orchestrator/SKILL.md` 负责创建；`ship-understand/design/split` 均明确不创建目录 |
| AC-8 | split 模板不默认写实际目录 | `templates/splits.yml.template` 使用 `suggested_slug`/`suggested_feature_name`，`created_feature_dir: ""` 默认空 |
| AC-9 | 独立技能都有 TODO preflight | 7 个 `ship-*` 技能均包含 `## TODO preflight`；`ship-grill-me` 区分嵌入调用和单独调用 |
| AC-10 | Design 对所有 feature 要求模板引用 | `validate_design.py` 无条件要求 `meta.yml.design_template_ref` 和 `## 方案模板引用`；测试覆盖缺模板失败 |
| AC-11 | Design → Build 确认持久化 | `ship-orchestrator/SKILL.md` 写入 `build_approved_*`；`ship-design/SKILL.md` handoff 回 orchestrator；`ship-build/SKILL.md` 和 `validate_build.py` 要求 `build_approved_at/build_approved_by/build_approval_note` |
| AC-12 | requirements validator 校验 source_refs/workspace | `validate_requirements.py` 校验缺 source_refs、primary 不可用、project group 缺 projects、projects 不属于 project.yml；测试覆盖正负样例 |
| AC-13 | validator 测试通过 | `python3 skills/ship-orchestrator/tests/test_validators.py` 通过 |
| AC-14 | README/MANIFEST/ACCEPTANCE 路径一致 | `README.md`、`MANIFEST.yml`、`ACCEPTANCE.md` 均使用当前 `skills/` 根路径 |
| AC-15 | handoff 包含 feature_dir、阶段技能、workspace、projects | `ship-orchestrator/SKILL.md`、`ship-understand/SKILL.md`、`ship-design/SKILL.md` 的输出 handoff 示例包含这些字段 |

## 已执行验证

```bash
python3 skills/ship-orchestrator/tests/test_validators.py
```

结果：

```text
PASS: valid requirements
PASS: valid design with template
PASS: valid build
PASS: valid current stage
PASS: meta YAML parser reads workflow/workspace/source_refs/build approval
PASS: loose YAML preserves quoted project template fragment
PASS: project template ref with fragment
PASS: requirements missing AC
PASS: requirements bad AC format
PASS: requirements missing source_refs
PASS: requirements primary source unavailable
PASS: project_group missing projects
PASS: valid project.yml subset scope
PASS: projects outside project.yml fail
PASS: design uncovered AC
PASS: design missing error response
PASS: missing template ref fails
PASS: template id does not exist
PASS: missing template section
PASS: design base sections must be top-level
PASS: ready design contains TBD
PASS: async-task missing required subsection
PASS: build uncovered AC
PASS: build tests failed
PASS: build mixed passed and failed
PASS: build missing approval fails
PASS: build missing approval by fails
PASS: build missing approval note fails
PASS: build wrong stage fails
All validator smoke tests passed.
```

## 已知边界

- 这是 skill 指令和验证脚本，不是独立 CLI 产品。
- validator 做结构和覆盖性检查，不替代项目真实测试；`ship-build` 必须运行仓库自己的 test/lint/typecheck 并写入 `verification.md`。
- TODO preflight 是 agent 行为约束，无法由 Python validator 证明真实工具调用；本次交付用技能文本和执行审查约束。
- Design Reference Template 是 Design 阶段护栏，不是新阶段；内置模板 checklist 不替代项目 spec，也不替代 `ship-grill-me` 语义审查。
