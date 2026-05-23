# AI Coding Skills

一套面向 AI coding agent 的开发工作流技能集。目标不是减少实际治理动作，而是把复杂流程收敛成更易理解的默认入口和阶段视图。

## 安装

```bash
npx skills add MuJianxuan/ai-feature-coding
```

## 默认使用方式

默认只需要记住：

- 入口：`ship-orchestrator`
- 大阶段：`Define → Design → Build → Close`

这 4 个大阶段是默认对外视图。内部仍然保留细阶段、硬门禁、文档产物和恢复协议，用于精确推进与诊断。

`ship-spec` 以 workflow utility 形态接入，不占用 stage map；它会在 `ship-tech-discovery`、`ship-frontend-design`、`ship-backend-design`、`ship-build`、`ship-handoff` 被自动消费并通过 `meta.yml.spec_context` 留痕。

## 你会得到什么

- 对外更简单：首屏不再要求理解所有内部 skill 名
- 对内不降级：Contract-First、前后端分离、三道硬门禁、验证与交付都保留
- 可恢复：`meta.yml.current_stage` 继续记录内部 canonical stage id
- 可诊断：需要时可展开到具体 `ship-*` 阶段
- 更精简：内部 canonical stages 从 14 个收敛到 12 个，保留双产物但减少阶段切换

## 文档入口

- 主文档：`skills/README.md`
- 共享协议：`skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- 元数据模板：`skills/ship-orchestrator/_templates/meta/meta.yml.template`
- 规范管理：`skills/ship-spec/SKILL.md`

## 启动示例

### 新建 feature

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流：<需求描述>
```

### 继续已有 feature

```text
继续 .docs/feature-YYYYMMDD-<short-name>/
```

### 高级模式

如果你明确知道要打到哪个内部阶段，也可以直接调用对应 `ship-*` skill；但这不是默认路径。

## 结构说明

- `skills/README.md`：默认用户视图，重点讲 4 个大阶段
- `skills/ship-orchestrator/`：统一入口与路由规则
- `skills/ship-orchestrator/_templates/`：协议与模板
- `.docs/`：feature 运行时产物和规范沉淀

## 维护

修改 workflow 相关文档后，至少检查：

- README 与 `workflow-protocol.md` 的阶段描述一致
- `meta.yml.template` 的字段与 orchestrator 说明一致
- 默认视图仍然是 4 大阶段，细阶段只在高级/诊断视图暴露

可执行校验命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
python3 skills/ship-orchestrator/scripts/spec_runtime.py scan .docs/spec
```

最小 runtime helper：

```bash
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init .docs/feature-YYYYMMDD-demo --feature-name "Demo Feature" --feature-id "feature-YYYYMMDD-demo"
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py refresh .docs/feature-YYYYMMDD-demo/meta.yml
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec .docs/feature-YYYYMMDD-demo/meta.yml --stage ship-build --file src/app.ts
```
