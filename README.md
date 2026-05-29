# AI Coding Skills

一套面向 AI coding agent 的开发工作流技能集。目标不是减少实际治理动作，而是把复杂流程收敛成更易理解的默认入口和阶段视图。

## 安装

```bash
npx skills add MuJianxuan/ai-feature-coding
```

## 默认使用方式

默认只需要记住：

- 入口：`ship-orchestrator`
- 大阶段：`[Discover →] Define → Design → Build → Close`

这 5 个大阶段是默认对外视图，其中 `Discover` 只在场景 A（零到一）和场景 C（迭代增强）出现。内部仍然保留细阶段、硬门禁、文档产物和恢复协议，用于精确推进与诊断。

`ship-spec` 以 workflow utility 形态接入，不占用 stage map；它会在 `ship-tech-discovery`、`ship-frontend-design`、`ship-backend-design`、`ship-build`、`ship-handoff` 被自动消费并通过 `meta.yml.spec_context` 留痕。规范边界始终是 `target project`，不是当前 cwd。

## 你会得到什么

- 对外更简单：首屏不再要求理解所有内部 skill 名
- 对内不降级：Contract-First、前后端分离、三道硬门禁、验证与交付都保留
- 可恢复：`meta.yml.current_stage` 继续记录内部 canonical stage id
- 可诊断：需要时可展开到具体 `ship-*` 阶段
- 精确恢复：内部 canonical stages 保持 14 个阶段，其中前 2 个是条件性 Discover 前置阶段

## 文档入口

- 主文档：`skills/README.md`
- 共享协议：`skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- 元数据模板：`skills/ship-orchestrator/_templates/meta/meta.yml.template`
- 项目配置模板：`skills/ship-orchestrator/_templates/project/project.yml.template`
- 规范管理：`skills/ship-spec/SKILL.md`

## 启动示例

### 新建 feature

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流：<需求描述>
```

### 继续已有 feature

```text
继续 <target-project>/<feature-root>/feature-YYYYMMDD-<short-name>/
```

### 高级模式

如果你明确知道要打到哪个内部阶段，也可以直接调用对应 `ship-*` skill；但这不是默认路径。

## 结构说明

- `skills/README.md`：默认用户视图，重点讲 5 个大阶段（Discover 可选）
- `skills/ship-orchestrator/`：统一入口与路由规则
- `skills/ship-orchestrator/_templates/`：协议与模板
- `skills/ship-*/references/`：阶段内参考模板，不属于共享协议
- `.docs/ship/project.yml`：target project 级显式配置，声明 `project_root / spec_root / feature_root`
- `target project` 下的 `.docs/`：默认 feature 运行时产物和规范沉淀位置

## 维护

修改 workflow 相关文档后，至少检查：

- README 与 `workflow-protocol.md` 的阶段描述一致
- `meta.yml.template` 的字段与 orchestrator 说明一致
- 默认视图仍然是 5 大阶段（Discover 可选），细阶段只在高级/诊断视图暴露

可执行校验命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
python3 skills/ship-orchestrator/scripts/spec_runtime.py scan --project-config <target-project>/.docs/ship/project.yml
```

最小 runtime helper：

```bash
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init feature-YYYYMMDD-demo --project-config <target-project>/.docs/ship/project.yml --feature-name "Demo Feature" --feature-id "feature-YYYYMMDD-demo" --scenario product_provided
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py refresh <target-project>/.docs/feature-YYYYMMDD-demo/meta.yml
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec <target-project>/.docs/feature-YYYYMMDD-demo/meta.yml --project-config <target-project>/.docs/ship/project.yml --stage ship-build --file src/app.ts
```

最小 project config 示例：

```yaml
schema_version: 1
project_id: demo-project
project_name: Demo Project
project_root: "."
spec_root: ".docs/spec"
feature_root: ".docs"
module_layout:
  mode: project_level_only
  module_roots: []
notes: ""
```

多项目父目录场景下，必须先选定 target project；缺少 spec 只会 warning，缺少 target project 会直接阻塞。
