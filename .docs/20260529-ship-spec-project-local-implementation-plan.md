---
doc_type: implementation_plan
doc_status: draft
topic: ship-spec-project-local-resolution
created_at: "2026-05-29"
updated_at: "2026-05-29"
source_design: ".docs/20260529-ship-spec-project-local-design.md"
---

# ship-spec 项目本地规范解析工程实施清单

## 1. 计划结论

本次按以下口径实施：

- 采用 **新协议直切**，不做旧 spec 兼容层。
- 把 **项目侧落地迁移** 纳入正式范围，不仅修改本仓库 runtime/doc/template。
- 第一波只支持 **显式 `.docs/ship/project.yml`**，不保留 `project_markers` heuristic fallback。
- `ship-spec` 继续是 **workflow utility**，不升级为 canonical stage。
- 缺少 spec 继续保持 **Warn Then Continue**；但 **无法确定 target project** 必须阻塞。

这样做的原因：

- 当前 runtime 已硬编码 cwd 语义，继续叠兼容只会保留双路径协议。
- 当前仓库没有真实 spec 样本负担，切换成本主要在协议和测试，不在数据迁移。
- 多项目父目录下最危险的问题是 silent guess；第一波去掉 heuristic，才能把 project boundary 切干净。

## 2. 当前证据

以下现状已经在仓库中确认：

- [`skills/ship-orchestrator/scripts/spec_runtime.py`](/Users/rao/Documents/DailyWork/aicoding/skills/ship-orchestrator/scripts/spec_runtime.py:119) 以 `scan_specs(spec_root, project_root=Path.cwd())` 为默认行为，CLI 也默认 `--spec-root .docs/spec`。
- [`skills/ship-orchestrator/scripts/feature_meta_runtime.py`](/Users/rao/Documents/DailyWork/aicoding/skills/ship-orchestrator/scripts/feature_meta_runtime.py:36) 把 `FEATURES_ROOT` 固定为仓库根下 `.docs`，[`sync_spec_context(...)`](/Users/rao/Documents/DailyWork/aicoding/skills/ship-orchestrator/scripts/feature_meta_runtime.py:842) 也把 `Path.cwd()` 当作 `project_root`。
- [`skills/ship-orchestrator/_templates/meta/meta.yml.template`](/Users/rao/Documents/DailyWork/aicoding/skills/ship-orchestrator/_templates/meta/meta.yml.template:67) 的 `spec_context` 只有 `index_status / last_checked_at / last_checked_stage / referenced_spec_ids / warnings / pending_proposals`，没有 target project 字段。
- [`skills/ship-spec/SKILL.md`](/Users/rao/Documents/DailyWork/aicoding/skills/ship-spec/SKILL.md:10) 明确写的是“维护 `.docs/spec/*.md`”，尚未引入 target project / project root / feature root 概念。
- [`README.md`](/Users/rao/Documents/DailyWork/aicoding/README.md:73) 和 `ship-spec` helper 示例仍然以仓库当前 cwd 下的 `.docs/spec` 为默认输入。
- 仓库当前 `.docs/spec/` 只有 `INDEX.md` 和 `coding/.gitkeep`，没有真实 spec 文件样本；可直接切换协议，无需处理历史 spec 兼容。
- 现有 `ship-spec` 单元测试可跑通：`python3 skills/ship-orchestrator/scripts/test_spec_runtime.py` 当前通过 `24` 个测试。

## 3. 实施范围

### In Scope

- `ship-spec` / `ship-orchestrator` 的 project resolution 协议
- feature 目录创建位置从“仓库根 `.docs/`”切到“target project 的 `feature_root`”
- `spec_runtime.py` / `feature_meta_runtime.py` CLI、返回结构、meta 落盘字段
- workflow protocol、shared template、README、各 `ship-*` SKILL 文档同步
- 新增项目侧配置模板 / 示例 / authoring checklist
- runtime / validator / unittest / smoke test 全链路补齐

### Out of Scope

- 不做模块级 spec 继承 / overlay
- 不引入新 canonical stage
- 不在 `ship-handoff` 自动写回 `.docs/spec/*.md`
- 不兼容旧 spec schema、旧解析路径、旧 heuristic project guess

## 4. 目标交付物

本次计划完成后，仓库内应新增或更新以下交付物：

- 新的 `.docs/ship/project.yml` 协议说明
- 一份项目配置模板文件，供业务项目初始化时复制
- 更新后的 runtime helper：
  - `spec_runtime.py`
  - `feature_meta_runtime.py`
- 更新后的 shared contract：
  - `meta.yml.template`
  - `workflow-protocol.md`
  - `_templates/README.md`
- 更新后的 usage docs：
  - `README.md`
  - `skills/README.md`
  - `skills/ship-spec/SKILL.md`
  - `skills/ship-orchestrator/SKILL.md`
  - `skills/ship-tech-discovery/SKILL.md`
  - `skills/ship-frontend-design/SKILL.md`
  - `skills/ship-backend-design/SKILL.md`
  - `skills/ship-build/SKILL.md`
  - `skills/ship-handoff/SKILL.md`
- 更新后的验证资产：
  - `test_spec_runtime.py`
  - `validate_workflow_docs.py`

## 5. 关键实现决策

### 5.1 Project Resolution 决策

第一波只支持两种来源：

1. 当前 feature `meta.yml.spec_context` 已持久化的 target project
2. 显式 `.docs/ship/project.yml`

不支持：

- 没有 project config 时自动根据 `package.json` / `go.mod` / `pyproject.toml` 猜项目
- 多候选目录自动选择
- 从 agent 当前 cwd 静默推断 target project

### 5.2 配置模板落点

建议新增：

- `skills/ship-orchestrator/_templates/project/project.yml.template`

原因：

- 这是 shared contract，不属于某个单独 stage skill。
- 现有 `_templates/README.md` 已负责汇总共享模板，新增模板最自然。
- 后续业务项目初始化时，可由 orchestrator 或 README 直接引用统一模板路径。

### 5.3 Feature Root 决策

当前 `FEATURES_ROOT = ROOT / ".docs"` 需要取消固定值，改为：

- 运行时先解析 `target_project_root`
- 再基于 project config 中的 `feature_root` 计算 feature 目录

结果要求：

- 从 workspace 父目录发起 NEW_FEATURE，feature 目录也必须创建到目标项目自己的 `.docs/feature-*`
- CONTINUE_FEATURE 只能信任已有 `meta.yml` 的 target project 信息，不重新按 cwd 计算

### 5.4 Warning / Blocking 决策

- `target project` 无法唯一确定：`blocked`
- `spec_root` 缺失 / `INDEX.md` 缺失 / 无命中 spec / spec frontmatter 非法：warning，继续

## 6. 文件级工程实施清单

## 6.1 Protocol 与 Template 层

### A. `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`

修改目标：

- 增加 `Project Resolution Contract` 小节。
- 明确 `ship-spec` 的运行边界是 `target project`，不是当前 cwd。
- 明确 `.docs/ship/project.yml` 是 project boundary 的唯一显式配置源。
- 明确 `spec_context` 新字段：
  - `target_project_id`
  - `target_project_root`
  - `spec_root`
  - `feature_root`
  - `resolution_source`
- 明确阻塞边界：只在无法确定 target project 时阻塞。
- 删除或改写任何会让人理解成“默认扫 cwd/.docs/spec”的表述。

验证：

- `validate_workflow_docs.py` 能检查到新增字段与关键词。
- 协议文本不能再保留旧的单路径语义。

### B. `skills/ship-orchestrator/_templates/meta/meta.yml.template`

修改目标：

- 扩展 `spec_context` 字段：
  - `target_project_id: ""`
  - `target_project_root: ""`
  - `spec_root: ""`
  - `feature_root: ""`
  - `resolution_source: ""`
- 更新注释，把“规范事实源仍是 `.docs/spec/*.md`”改成“规范事实源是 `target project` 下的 `spec_root`”。

验证：

- `ensure_spec_context()` 刷新后不会丢字段。
- `validate_workflow_docs.py` 新增片段校验通过。

### C. `skills/ship-orchestrator/_templates/README.md`

修改目标：

- 在目录结构中新增 `project/project.yml.template`。
- 补充该模板的用途说明：
  - project root
  - spec root
  - feature root
  - project-level-only

验证：

- `validate_workflow_docs.py` 新增对模板 README 关键字校验。

### D. 新增 `skills/ship-orchestrator/_templates/project/project.yml.template`

建议内容：

```yaml
schema_version: 1
project_id: ""
project_name: ""
project_root: "."
spec_root: ".docs/spec"
feature_root: ".docs"
module_layout:
  mode: project_level_only
  module_roots: []
notes: ""
```

要求：

- 不保留 `project_markers` fallback 字段，避免第一波协议表达与实现不一致。
- 注释中明确“本期不支持 module-level spec root”。

验证：

- README / ship-spec / orchestrator 文档都引用这一模板。

## 6.2 Runtime 层

### E. `skills/ship-orchestrator/scripts/spec_runtime.py`

修改目标：

1. 新增 project config 解析能力。
2. 支持从 `.docs/ship/project.yml` 解析：
   - `target_project_id`
   - `target_project_root`
   - `spec_root`
   - `feature_root`
3. `scan` / `resolve` 的默认输入不再直接假设 `.docs/spec`，而是：
   - 显式 `--project-config`
   - 或显式 `--spec-root + --project-root`
4. 返回 payload 中补充：
   - `target_project_id`
   - `target_project_root`
   - `spec_root`
   - `feature_root`
   - `resolution_source`
5. `ship-build` 的 `--file` 先归一化到 `target_project_root` 相对路径再做 glob。

CLI 建议：

- 保留 `--spec-root` / `--project-root` 作为低层调试入口
- 新增 `--project-config`
- 当 `--project-config` 提供时，覆盖 `--spec-root` / `--project-root`

不做的事：

- 不在这里实现多候选交互
- 不在这里保留 marker fallback

验证：

- 单元测试覆盖单项目、多项目父目录、路径归一化、缺 spec warning。
- 输出 JSON 结构稳定。

### F. `skills/ship-orchestrator/scripts/feature_meta_runtime.py`

修改目标：

1. 去掉仓库级固定 `FEATURES_ROOT` 语义。
2. 新增 project config 读取逻辑：
   - `init`
   - `sync-spec`
   - 任何需要创建或刷新 feature meta 的入口
3. `create_feature_meta(...)` 支持写入：
   - `spec_context.target_project_id`
   - `spec_context.target_project_root`
   - `spec_context.spec_root`
   - `spec_context.feature_root`
   - `spec_context.resolution_source`
4. `feature_dir_for(...)` 改为依赖 target project config，而不是依赖仓库根 `.docs`
5. `sync_spec_context(...)` 改为使用 target project root 做 `project_root`，不能再传 `Path.cwd()`
6. `sync-spec` CLI 增加 `--project-config`
7. `init` CLI 增加 `--project-config`

阻塞策略：

- `init` 时缺少 `--project-config` 且无法从 feature dir / cwd 上溯解析 project config：报错退出
- `sync-spec` 时 `meta.yml` 无 target project 信息，且未提供 `--project-config`：报错退出

实现注意：

- `meta.yml` 落盘时，路径建议统一写“相对 workspace 启动目录的稳定相对路径”或“相对 feature 所在项目根的路径”，不要混写绝对/相对。
- 需要先在计划评审时定死一种；我建议：
  - `target_project_root` 落盘为相对当前 workspace 的路径字符串
  - runtime 内部一律转绝对路径处理

验证：

- `init` 创建的 feature 目录进入 target project 下的 `.docs/feature-*`
- `sync-spec` 不再受调用 cwd 影响
- 旧路径 hardcode 全部移除

## 6.3 Validator / Test 层

### G. `skills/ship-orchestrator/scripts/test_spec_runtime.py`

新增测试组：

1. `project config -> spec_root` 解析
2. `project config -> feature_root` 解析
3. 多项目父目录下存在两个 project config 时：
   - runtime 不自动猜
   - 需要显式 project config 或报错
4. `sync_spec_context()` 会把 target project 字段写回 `meta.yml`
5. `ship-build --file` 在父目录 cwd 下仍能按 target project 相对路径命中 `applies_to`
6. target project 已确定但 spec 目录缺失，只产出 warning 不抛错

保留并改写现有测试：

- 现有基于 `Path.cwd()` 的假设需要改成显式 `project_root`

建议补一组集成味更强的测试场景：

- `workspace/project-a/.docs/ship/project.yml`
- `workspace/project-b/.docs/ship/project.yml`
- 从 `workspace/` 调用 helper，验证 feature 目录与 spec 命中都指向 `project-a`

验证命令：

```bash
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
```

### H. `skills/ship-orchestrator/scripts/validate_workflow_docs.py`

修改目标：

- 在 `validate_meta_template()` 中校验新 `spec_context` 字段
- 在 `validate_protocol_doc()` 中校验：
  - `target project`
  - `.docs/ship/project.yml`
  - `resolution_source`
  - `feature_root`
  - “无法确定 target project 才阻塞”
- 在 `validate_ship_spec_doc()` 中校验新 helper 用法和 project config 说明
- 在 `validate_root_readme_commands()` 中校验 README 新命令示例
- 增加对 `_templates/project/project.yml.template` 存在性的校验

验证命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

## 6.4 文档与 Skill 层

### I. `skills/ship-spec/SKILL.md`

修改目标：

- 把职责改写为“维护 target project 下的 `spec_root`”
- 新增 `.docs/ship/project.yml` 章节
- 更新目录结构示例：
  - 单项目
  - 多项目父目录
  - 模块化项目但 project-level-only
- 更新 runtime helper 命令，改成显式 `--project-config`
- 明确本期不支持 module-level spec root
- 明确 project boundary 缺失会阻塞，而 spec 缺失不阻塞

验证：

- `validate_workflow_docs.py` 关键字检查通过

### J. `skills/ship-orchestrator/SKILL.md`

修改目标：

- 在 Spec Hook Model 中明确 orchestrator 负责 project resolution
- 说明 NEW_FEATURE / CONTINUE_FEATURE / sync-spec 的 project boundary 行为
- 修改任何“feature 默认创建到仓库根 `.docs/`”的描述

### K. `skills/ship-tech-discovery/SKILL.md`

修改目标：

- 明确 selection 读取的是 target project spec
- 若 target project 不明确，不允许进入 selection

### L. `skills/ship-frontend-design/SKILL.md`

修改目标：

- 明确只消费 target project 的 spec，不读取父目录或其他项目 spec

### M. `skills/ship-backend-design/SKILL.md`

修改目标：

- 同前端设计，强调 project-local spec boundary

### N. `skills/ship-build/SKILL.md`

修改目标：

- 把“匹配 `.docs/spec/*.md`”改成“匹配 target project `spec_root`”
- 明确 `spec_refs` 的文件路径需按 target project root 归一化

### O. `skills/ship-handoff/SKILL.md`

修改目标：

- proposal 目标路径默认指向 target project `spec_root`
- 有 `spec_context.warnings` 时必须列入 follow-up

### P. `README.md`

修改目标：

- 把 helper 命令改为显式 `--project-config .docs/ship/project.yml`
- 增加最小项目初始化示例
- 说明多项目父目录场景下，必须先选定 target project

### Q. `skills/README.md`

修改目标：

- 同步更新 ship workflow 概览，确保 `ship-spec` 的 project-local 语义和主 README 一致

## 6.5 项目侧迁移资产

### R. 新增 `.docs/ship/project.yml` 示例文档

建议新增一份参考文档，位置二选一：

1. `.docs/20260529-ship-project-config-example.md`
2. 写进 `skills/ship-spec/SKILL.md` 的专门章节

推荐：

- 同时保留模板文件 + `ship-spec` 文档示例

需要说明：

- 业务项目如何创建 `.docs/ship/project.yml`
- 如何声明 `project_id / project_name / spec_root / feature_root`
- 如何在 workspace 父目录运行 helper

## 7. 实施顺序

建议按以下顺序执行，避免 contract 漂移：

1. 先改 shared contract
   - `workflow-protocol.md`
   - `meta.yml.template`
   - `_templates/README.md`
   - 新增 `project.yml.template`
2. 再改 runtime
   - `spec_runtime.py`
   - `feature_meta_runtime.py`
3. 再改 unittest / validator
   - `test_spec_runtime.py`
   - `validate_workflow_docs.py`
4. 再改 skill / README 文档
5. 最后做 smoke test 和仓库自检

原因：

- 先锁 contract，runtime 和 validator 才知道要对齐什么。
- 若先改 skill 文档，再改 runtime，最容易出现“文档先变，但命令和测试还在旧合同上”的假阳性。

## 8. 可执行验收清单

## 8.1 Unit / Validator

必须通过：

```bash
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

## 8.2 Runtime Smoke Test

建议新增或手工执行以下 smoke 路径：

1. 单项目场景

```bash
python3 skills/ship-orchestrator/scripts/spec_runtime.py scan --project-config project-a/.docs/ship/project.yml
python3 skills/ship-orchestrator/scripts/spec_runtime.py resolve ship-build --project-config project-a/.docs/ship/project.yml --file src/app.ts
```

2. 多项目父目录场景

```bash
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init project-a/.docs/feature-20260529-demo --feature-name "Demo" --feature-id "feature-20260529-demo" --scenario product_provided --project-config project-a/.docs/ship/project.yml
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec project-a/.docs/feature-20260529-demo/meta.yml --stage ship-build --project-config project-a/.docs/ship/project.yml --file src/app.ts
```

3. 缺 spec 但 project config 正常

- 预期：返回 warning，不阻塞

4. 缺 project config

- 预期：直接失败并给出明确错误，不静默 fallback

## 8.3 文档一致性验收

检查项：

- README、`ship-spec/SKILL.md`、`workflow-protocol.md` 都不再把 cwd 直接等同于 project root
- 所有 helper 示例统一使用 `--project-config`
- 不再存在“默认 feature 创建到仓库根 `.docs/`”的文案
- validator 已覆盖 `project.yml.template`

## 9. 完成标准

满足以下条件才算本次修改计划执行完成：

- runtime 已以 target project 为边界，而不是以 cwd 为边界
- feature 目录创建到 target project `feature_root`
- `meta.yml.spec_context` 已保存完整 target project 解析结果
- `ship-build` 的 spec 匹配已基于 target project 相对路径工作
- 文档、模板、validator、unittest 已全部同步
- 多项目父目录场景下，不再有 silent guess
- 缺 spec 继续 warning，缺 target project 明确阻塞

## 10. 风险与注意事项

### 风险 1：路径表示不统一

表现：

- `meta.yml` 里混入绝对路径
- validator / 测试在不同 cwd 下结果不同

处理：

- 先定死落盘路径格式，再统一实现与测试

### 风险 2：runtime 已切换，但 helper 示例没同步

表现：

- README 命令仍旧可见 `.docs/spec`
- 用户照文档运行得到旧行为或失败

处理：

- README / ship-spec / orchestrator / validator 同一轮一起改

### 风险 3：feature 创建路径切换后，其他脚本仍假设仓库根 `.docs`

表现：

- init 成功，但 refresh / sync-spec / handoff 找不到 feature

处理：

- 搜全仓 `FEATURES_ROOT`、`.docs/feature-`、`.docs/spec` 的硬编码引用，逐个核对

## 11. 建议的实现后复查

执行完成后按以下顺序复查：

1. `git diff --check`
2. `python3 skills/ship-orchestrator/scripts/test_spec_runtime.py`
3. `python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py`
4. 走一遍单项目 smoke test
5. 走一遍多项目父目录 smoke test
6. 对照本计划逐项勾选，确认没有漏掉模板 / validator / README / skill 文案
