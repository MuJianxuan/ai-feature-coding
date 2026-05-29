---
doc_type: design
doc_status: draft
topic: ship-spec-project-local-resolution
created_at: "2026-05-29"
updated_at: "2026-05-29"
---

# ship-spec 项目本地规范解析设计

## 1. 背景与目标

当前 `ship-spec` 的核心痛点不是规范内容怎么写，而是在多项目工作目录下无法稳定判断“这次 feature 属于哪个项目”。现有实现默认从当前工作目录读取 `.docs/spec`，当 cwd 是多个项目的父目录时，容易把父目录规范、其他项目规范或空规范误当成当前 feature 的规范事实源。

本设计目标：

- 让 `ship-spec` 以目标项目为边界消费规范，而不是以 agent 当前 cwd 为边界。
- 用 `.docs/ship/project.yml` 显式声明项目根与规范根，减少 silent heuristic。
- 本期只支持项目级规范：目标项目根下的 `.docs/spec/`。
- feature 运行时产物写入目标项目自己的 `.docs/feature-*`，避免多项目集中目录混用。
- 保持现有 `Warn Then Continue` 策略：缺少规范或无匹配规范时留痕，不默认阻塞 workflow。

非目标：

- 不把 `ship-spec` 改成 canonical stage。
- 不引入模块级 spec 继承/覆盖；模块差异先通过 `domains`、`applies_to`、`stack_tags` 表达。
- 不在 `ship-handoff` 中直接写回 `.docs/spec/*.md`；继续采用 Proposal-First。

## 2. 当前证据

从当前仓库静态检查可确认：

- `skills/ship-spec/SKILL.md` 声明只维护 `.docs/spec/*.md`，没有 target project / project root 概念。
- `skills/ship-orchestrator/scripts/spec_runtime.py` 的 `scan` / `resolve` 默认 `--spec-root .docs/spec`。
- `skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec` 同样默认 `--spec-root .docs/spec`，并以 `Path.cwd()` 作为 `project_root`。
- `skills/ship-orchestrator/_templates/meta/meta.yml.template` 的 `spec_context` 只记录 `index_status`、`last_checked_at`、`last_checked_stage`、`referenced_spec_ids`、`warnings`、`pending_proposals`。
- `.docs/spec/INDEX.md` 当前只是人工 registry，且没有真实 spec 文件样本。
- `workflow-protocol.md` 已明确 `ship-spec` 是 workflow utility，不进入 stage map；这个定位应保持。

结论：需要补的是“项目选择与规范根解析协议”，不是新增一个 workflow stage。

## 3. 目标模型

### 3.1 目录模型

单项目目录：

```text
project-a/
├── .docs/
│   ├── ship/
│   │   └── project.yml
│   ├── spec/
│   │   ├── INDEX.md
│   │   └── coding/*.md
│   └── feature-YYYYMMDD-xxx/
└── src/
```

多项目父目录：

```text
workspace/
├── project-a/
│   └── .docs/
│       ├── ship/project.yml
│       ├── spec/
│       └── feature-YYYYMMDD-xxx/
└── project-b/
    └── .docs/
        ├── ship/project.yml
        ├── spec/
        └── feature-YYYYMMDD-yyy/
```

模块化项目目录：

```text
project-a/
├── .docs/
│   ├── ship/project.yml
│   └── spec/
├── apps/
│   ├── web/
│   └── admin/
└── packages/
    └── shared/
```

模块化项目仍只消费 `project-a/.docs/spec/`，不扫描 `apps/web/.docs/spec` 或 `packages/shared/.docs/spec`。

### 3.2 `.docs/ship/project.yml`

推荐 schema：

```yaml
schema_version: 1
project_id: ""
project_name: ""
project_root: "."          # 相对本文件所在项目根，通常为 "."
spec_root: ".docs/spec"    # 相对 project_root
feature_root: ".docs"      # feature-* 运行时产物根，相对 project_root
module_layout:
  mode: project_level_only  # project_level_only
  module_roots:
    - "apps/*"
    - "packages/*"
project_markers:
  - "package.json"
  - "pyproject.toml"
  - "Cargo.toml"
  - "go.mod"
notes: ""
```

字段语义：

- `project_id`：稳定项目标识，用于写入 `meta.yml.spec_context.target_project_id`。
- `project_root`：目标项目根；本期只推荐 `"."`，避免跨目录引用造成混乱。
- `spec_root`：项目级规范目录；默认 `.docs/spec`。
- `feature_root`：feature runtime docs 目录；默认 `.docs`。
- `module_layout.mode`：本期固定 `project_level_only`，为后续模块级策略预留扩展点。
- `module_roots`：只作为文档和未来匹配辅助，不改变本期 spec root。
- `project_markers`：仅用于缺少显式配置时的 fallback 探测，不优先于配置。

## 4. 解析规则

### 4.1 Project Resolution

`ship-orchestrator` 在 NEW_FEATURE / CONTINUE_FEATURE / sync-spec 前应先解析 target project：

1. 从当前 cwd 向上查找 `.docs/ship/project.yml`。
2. 若找到，读取为当前 target project。
3. 若未找到，扫描 cwd 下一级子目录中是否存在 `.docs/ship/project.yml`。
4. 若只有一个候选，可提示用户确认后使用。
5. 若有多个候选，必须询问用户选择 target project，不允许自动猜测。
6. 若没有候选，再使用 `project_markers` heuristic 判断当前 cwd 是否是项目根。
7. 若仍无法判断，进入 blocked / awaiting_project_selection，不创建 feature 目录。

选择结果应写入 feature `meta.yml`，而不是每次靠 cwd 重新推断。

### 4.2 Spec Resolution

`ship-spec` 只读取 target project 的 `spec_root`：

```text
target_project_root + spec_root
```

匹配规则沿用现有 schema：

- `ship-tech-discovery`：`stage_hooks + stack_tags`
- `ship-frontend-design` / `ship-backend-design`：`stage_hooks + stack_tags + domains`
- `ship-build`：`stage_hooks=ship-build + applies_to`，`stack_tags / domains` 作为附加过滤
- `ship-handoff`：汇总 `meta.yml.spec_context.referenced_spec_ids` 并生成 proposal

当 `applies_to` 匹配文件时，文件路径应先归一化为相对 `target_project_root` 的路径，避免父目录 cwd 导致 glob 失效。

### 4.3 Missing Spec Policy

默认仍是 `Warn Then Continue`：

- 找不到 `.docs/ship/project.yml`：需要选择项目时阻塞；已明确 target project 但缺少 spec 目录时不阻塞。
- 缺少 `spec_root` 或 `INDEX.md`：写入 `spec_context.warnings`。
- 无匹配 spec：写入 `spec_context.warnings` 和阶段产物 `spec_warnings`。
- frontmatter 非法：该 spec 跳过，warning 留痕。

阻塞边界只在“无法确定目标项目”发生；“目标项目确定但规范缺失”不阻塞。

## 5. meta.yml 扩展建议

`spec_context` 建议扩展为：

```yaml
spec_context:
  target_project_id: ""
  target_project_root: ""
  spec_root: ""
  resolution_source: ""      # project_config | selected_project | marker_fallback
  index_status: missing
  last_checked_at: ""
  last_checked_stage: ""
  referenced_spec_ids: []
  warnings: []
  pending_proposals: []
```

说明：

- `target_project_root` 使用相对启动 workspace 的路径或绝对路径需要在实现时统一；建议 runtime 内部用绝对路径，落盘用稳定相对路径。
- `resolution_source` 用于诊断为什么选择了这个项目。
- `referenced_spec_ids` 继续保持 feature 级累计集合。

## 6. ship-* workflow 影响

### ship-orchestrator

- NEW_FEATURE 入口在创建 feature 目录前先执行 project resolution。
- 当 cwd 是多项目父目录时，feature 目录必须创建到目标项目的 `feature_root` 下。
- CONTINUE_FEATURE 读取已有 `meta.yml.spec_context.target_project_root`，不重新猜测。
- 进入 spec hook 阶段前，把 target project spec context 传给阶段 skill。

### ship-spec

- 文档中明确“规范边界 = target project”，不是 agent cwd。
- 增加 `.docs/ship/project.yml` authoring checklist。
- 增加多项目父目录、单项目目录、模块化项目三种使用场景。

### ship-tech-discovery

- selection 子段执行 spec compatibility check 时，使用 target project 的 `spec_root`。
- 产物 frontmatter 继续写 `spec_checked_at`、`referenced_spec_ids`、`spec_warnings`。

### ship-frontend-design / ship-backend-design

- 只消费 target project spec，不消费父目录或其他项目 spec。
- 模块路径只作为 `domains/applies_to` 匹配辅助，不改变 spec 根。

### ship-build

- 每个任务开始前按任务文件清单解析 spec。
- 文件路径归一化到 target project root。
- 任务证据写 `spec_refs`，无匹配时写明“无匹配规范”与 warning。

### ship-handoff

- 继续 Proposal-First。
- proposal 目标路径默认是 target project 的 `.docs/spec/`。
- 若 feature 过程中存在 spec warnings，应在 handoff 中列为 follow-up。

## 7. 后续实现清单

后续真正实现时建议按以下顺序修改：

1. 更新 `skills/ship-spec/SKILL.md`，加入 target project / `.docs/ship/project.yml` 协议。
2. 更新 `workflow-protocol.md` 和 `meta.yml.template`，补齐 `spec_context` 扩展字段。
3. 扩展 `spec_runtime.py`：
   - 支持读取 `--project-config`
   - 输出 `target_project_id`、`target_project_root`、`spec_root`、`resolution_source`
   - 按 target project root 归一化 `--file`
4. 扩展 `feature_meta_runtime.py sync-spec`：
   - 支持 `--project-config`
   - 将 target project 解析结果写入 `meta.yml.spec_context`
5. 更新 `test_spec_runtime.py`：
   - 单项目 cwd
   - 多项目父目录候选
   - 模块化项目仍使用项目级 spec
   - 无匹配 spec 保持 warning
6. 更新 `validate_workflow_docs.py`，确保共享协议、模板、skill 文档包含新字段。
7. 更新 README 的 helper 示例，展示 `--project-config .docs/ship/project.yml`。

## 8. 验收标准

设计层验收：

- 文档明确区分 project root、spec root、feature root。
- 文档明确当前只支持项目级 spec，不支持模块级 spec。
- 文档明确无法确定 target project 时才阻塞；缺少 spec 本身不阻塞。
- 文档明确 feature 产物写入目标项目 `.docs/`。
- 文档明确后续需要同步修改 runtime、meta template、protocol、tests、validator。

实现层验收：

- `python3 skills/ship-orchestrator/scripts/test_spec_runtime.py` 通过。
- `python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py` 通过。
- `python3 skills/ship-orchestrator/scripts/spec_runtime.py scan --project-config <project>/.docs/ship/project.yml` 能扫描目标项目 spec。
- 从多项目父目录执行 sync-spec 时，不会读取父目录 `.docs/spec` 作为目标项目 spec。

