# skills-new — 开发工作流技能套件

> 一套从需求到交付的端到端开发工作流，把 PRD/原型/UI-UX 设计稿转化为可验证的可工作软件。对外默认只展示 4 个大阶段，内部仍保留严格的细阶段、门禁和产物。

## 默认视图

日常使用时，只需要记住一个入口和四个阶段：

- 入口：`ship-orchestrator`
- 大阶段：`Define → Design → Build → Close`

### 四阶段模型

| 大阶段 | 目标 | 用户默认会看到什么 |
|--------|------|--------------------|
| `Define` | 把需求整理成可验证输入，并完成首道确认 | 当前目标、需求是否已明确、下一次确认点 |
| `Design` | 完成调研、选型、接口契约、前后端方案，并通过设计评审 | 方案是否成形、是否需要你批准设计 |
| `Build` | 完成实施计划、编码执行、自动化验证 | 是否可以开始编码、当前进展、下一次确认点 |
| `Close` | 完成 AC 映射验收与交付总结 | 是否已可交付、残余风险、handoff 结论 |

默认原则：

- 用户默认只和 `ship-orchestrator` 交互
- 状态默认显示大阶段，不要求记住 12 个内部阶段名
- 只有在恢复断点、排查阻塞、直接调用某阶段时，才展开内部细阶段
- `ship-spec` 作为 workflow utility 隐式接入，不作为单独阶段暴露给默认用户视图

## 为什么这样设计

- **外部简单**：首屏只暴露 4 个阶段，降低学习成本
- **内部严格**：三道硬门禁、Contract-First、前后端分离、测试与验收都保留
- **恢复精确**：`meta.yml.current_stage` 仍然使用 canonical stage id，便于断点恢复和诊断
- **展示收敛**：对外使用 `macro_stage` 摘要，不把所有细阶段名直接压给用户

## 启动方式

### 新建 feature

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流：<需求描述>

附件资料：resource/<file>.md / Figma 链接 / ...
```

默认响应应类似：

- 当前处于 `Define`
- 系统正在整理需求并准备首道确认
- 下一次需要你的动作：确认需求评审结论

### 继续已有 feature

```text
继续 .docs/feature-20260522-todo-app/
```

默认返回大阶段视图；需要诊断时，再展开 `current_stage` 对应的细阶段。

### 高级模式：直接调用内部阶段

```text
使用 ship-frontend-design，基于 .docs/feature-20260522-todo-app/api-contract.md 做前端方案
```

这类调用保留给高级用户、诊断场景和精确恢复场景，不作为默认使用路径。

补充说明：

- `ship-contract`、`ship-frontend-design`、`ship-backend-design` 各自维护独立的 `references/` 目录
- 这些目录中的模板属于阶段内参考资产，用于帮助 agent 产出更完整的设计文档，不属于 workflow 共享协议

## 内部阶段映射

对外是 4 阶段，内部仍然是 12 个 canonical stages：

| 大阶段 | 内部阶段 |
|--------|----------|
| `Define` | `ship-intake`, `ship-intake-review` |
| `Design` | `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `Build` | `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `Close` | `ship-handoff` |

说明：

- 大阶段是展示层概念
- 细阶段是协议层和路由层事实源
- 三道硬门禁仍然存在：`ship-intake-review`、`ship-design-review`、`ship-plan-review`

## 核心设计原则

### 1. 产物驱动而非对话驱动

- 每个阶段的完成以产物文件和 frontmatter 为准
- 阶段文档 frontmatter 是事实源
- `meta.yml` 只做恢复、汇总和展示索引

### 2. Progressive Disclosure

- 首屏只讲一个入口和四个大阶段
- 12 个细阶段只在高级模式或内部协议中展开
- 用户默认看到“当前目标”和“下一次需要决策的动作”，而不是一长串阶段名

### 3. 三道硬门禁

| 门禁 | 所属大阶段 | 目的 |
|------|------------|------|
| `ship-intake-review` | `Define` | 确认需求清晰、AC 可验证、无歧义 |
| `ship-design-review` | `Design` | 交叉验证 contract ↔ frontend ↔ backend |
| `ship-plan-review` | `Build` | 确认任务粒度合理、依赖正确、AC 全覆盖 |

### 4. Contract-First Slicing

实施阶段任务顺序保持不变：

1. 契约层任务
2. 前后端并行任务
3. 集成任务

这条规则仍然是内部执行顺序的硬约束。

### 5. 子代理委派是执行策略，不是新阶段

- 默认流程不新增 stage，也不改变 12 个 canonical stages
- 只有 `ship-frontend-design` 与 `ship-backend-design` 是显式并行阶段
- research 取证、计划审计、测试分轨、证据整理等可以作为辅助委派
- 所有硬门禁、`ship-build` 正式任务推进、最终 close 决策仍由主上下文与用户完成

## Feature 目录结构

```text
.docs/feature-YYYYMMDD-<short-name>/
├── meta.yml
├── requirements.md
├── review-requirement.md
├── tech-research.md
├── tech-selection.md
├── api-contract.md
├── frontend-design.md
├── backend-design.md
├── review-design.md
├── frontend-plan.md
├── backend-plan.md
├── review-plan.md
├── verification.md
├── handoff.md
└── resource/
```

其中：

- `current_stage` 记录内部细阶段
- `macro_stage` 记录默认对外展示的大阶段摘要
- `spec_context` 记录最近一次规范解析状态、已引用规范和待沉淀 proposal

## Advanced

以下内容属于内部实现或高级使用方式：

- 完整 12 阶段路由顺序
- `meta.yml` 细阶段状态维护
- `ship-spec` hook 契约与 `spec_context` 摘要字段
- 各阶段 SKILL 的详细输入输出
- review gate frontmatter 协议
- fast-track 的最小路径和升级/降级规则

这些内容以 `ship-orchestrator/_templates/protocol/workflow-protocol.md` 为准。

## 维护

修改 SKILL.md 后：

- 检查与 `ship-orchestrator/_templates/protocol/workflow-protocol.md` 的协议对齐
- 检查与 `ship-orchestrator/_templates/meta/meta.yml.template` 的字段对齐
- 检查与 `ship-orchestrator/_templates/review/review.md.template` 的章节对齐
