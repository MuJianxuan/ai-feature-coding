# skills-new — 开发工作流技能套件

> 一套从需求到交付的端到端开发工作流，把 PRD/原型/UI-UX 设计稿转化为可验证的可工作软件。对外默认只展示 5 个大阶段（Discover 可选），内部仍保留严格的细阶段、门禁和产物。

## 默认视图

日常使用时，只需要记住一个入口和五个阶段：

- 入口：`ship-orchestrator`
- 大阶段：`[Discover →] Define → Design → Build → Close`

### 五阶段模型（Discover 可选）

| 大阶段 | 目标 | 用户默认会看到什么 | 条件 |
|--------|------|--------------------|------|
| `Discover` | 把模糊想法或变更请求转化为结构化产品简报和 UIUX 原型 | 方案对比、设计方向选择、HTML 原型预览 | 仅场景 A/C 激活 |
| `Define` | 把需求整理成可验证输入，并完成首道确认 | 当前目标、需求是否已明确、下一次确认点 | 始终 |
| `Design` | 先完成项目真实现状发现，再完成调研、选型、接口契约、前后端方案，并通过设计评审 | 方案是否成形、是否需要你批准设计 | 始终 |
| `Build` | 完成实施计划、编码执行、自动化验证 | 是否可以开始编码、当前进展、下一次确认点 | 始终 |
| `Close` | 完成 AC 映射验收与交付总结 | 是否已可交付、残余风险、handoff 结论 | 始终 |

### 四种入口场景

| 场景 | 描述 | 起点 | Discover |
|------|------|------|----------|
| A 零到一 | 只有一句话想法，无 PRD/原型/设计稿 | `ship-discover` (greenfield) | 激活 |
| B 产品提供 | 已有完整 PRD/Figma/原型/UIUX | `ship-define` (interview mode) | 跳过 |
| C 迭代增强 | 基于已有功能做修改/扩展，有旧代码但无新 PRD | `ship-discover` (evolve) | 激活 |
| D PRD 直通 | 已有完整 PRD + 原型 + 设计稿，用户明确不需要需求录入 | `ship-define` (prd_direct mode) | 跳过 |

默认原则：

- 用户默认只和 `ship-orchestrator` 交互
- orchestrator 自动识别场景（A/B/C/D）并路由到正确的起点
- 状态默认显示大阶段，不要求记住内部阶段名
- 只有在恢复断点、排查阻塞、直接调用某阶段时，才展开内部细阶段
- `ship-spec` 作为 workflow utility 隐式接入，不作为单独阶段暴露给默认用户视图
- `ship-spec` 只消费 workspace 的 `spec_root`；多项目父目录下必须先初始化 `.docs/ship/project.yml`，再为 feature 选择默认关联 projects
- 进入 Design 后，`ship-tech-discovery` 对已有项目必须 Project Reality First：先查真实功能、表、API、页面、服务、权限和既有 feature 文档，再做技术调研/选型
- 规范路由从单一 `.docs/spec/INDEX.md` 开始；INDEX 只区分 `frontend / backend / shared`，frontmatter schema 不新增 `spec_type`

## 为什么这样设计

- **外部简单**：首屏只暴露 5 个阶段（Discover 可选），降低学习成本
- **场景自适应**：orchestrator 自动识别入口场景，无需用户手动选择流程
- **内部严格**：三道硬门禁、Contract-First、前后端分离、测试与验收都保留
- **恢复精确**：`meta.yml.current_stage` 仍然使用 canonical stage id，便于断点恢复和诊断
- **展示收敛**：对外使用 `macro_stage` 摘要，不把所有细阶段名直接压给用户

## 启动方式

### 新建 feature

#### 场景 A：零到一（只有想法）

```text
启动 ship-orchestrator，我想做一个"<功能名>"：<一句话想法>
```

默认响应：
- 识别为场景 A，起点 `ship-discover`（greenfield）
- 当前处于 `Discover`
- 系统将通过结构化提问探索需求，产出 product-brief.md
- 若涉及 UI 且无设计稿，会进入 `ship-shape` 产出 HTML 原型
- 下一次需要你的动作：确认产品方向和设计方向

#### 场景 B：产品提供完整材料

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流：<需求描述>

附件资料：resource/<file>.md / Figma 链接 / ...
```

默认响应：
- 识别为场景 B，起点 `ship-define`（interview mode），跳过 Discover
- 当前处于 `Define`
- 系统正在整理需求并准备首道确认
- 下一次需要你的动作：确认需求评审结论

#### 场景 D：PRD 直通（不需要需求录入）

```text
启动 ship-orchestrator，为"<功能名>"开启完整工作流，PRD 已完整不需要需求录入：<需求描述>

附件资料：resource/prd.docx / resource/prototype.html / ...
```

默认响应：
- 识别为场景 D，起点 `ship-define`（prd_direct mode），跳过 Discover
- 当前处于 `Define`
- 系统正在从 PRD 和原型中提取结构化索引（零提问）
- 产出的 requirements.md 为索引式（引用 PRD 来源位置，不复制原文）
- 下一次需要你的动作：确认 PRD 质量 + 提取准确性评审结论

#### 场景 C：迭代增强

```text
启动 ship-orchestrator，基于 <target-project>/.docs/feature-20260520-old-feature/ 的现有实现，<变更需求描述>
```

默认响应：
- 识别为场景 C，起点 `ship-discover`（evolve）
- 当前处于 `Discover`
- 系统将扫描现有代码与文档，分析变更影响
- 下一次需要你的动作：确认变更范围和影响分析

### 继续已有 feature

```text
继续 <target-project>/.docs/feature-20260522-todo-app/
```

默认返回大阶段视图；需要诊断时，再展开 `current_stage` 对应的细阶段。

### 高级模式：直接调用内部阶段

```text
使用 ship-frontend-design，基于 <target-project>/.docs/feature-20260522-todo-app/api-contract.md 做前端方案
```

这类调用保留给高级用户、诊断场景和精确恢复场景，不作为默认使用路径。

补充说明：

- `ship-contract`、`ship-frontend-design`、`ship-backend-design` 各自维护独立的 `references/` 目录
- 这些目录中的模板属于阶段内参考资产，用于帮助 agent 产出更完整的设计文档，不属于 workflow 共享协议

## 内部阶段映射

对外是 5 阶段（Discover 可选），内部是 14 个 canonical stages（前 2 个条件性）：

| 大阶段 | 内部阶段 | 条件 |
|--------|----------|------|
| `Discover` | `ship-discover`, `ship-shape` | 仅场景 A/C |
| `Define` | `ship-define`, `ship-define-review` | 始终 |
| `Design` | `ship-tech-discovery`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` | 始终 |
| `Build` | `ship-delivery-plan`, `ship-plan-review`, `ship-build`, `ship-verify` | 始终 |
| `Close` | `ship-handoff` | 始终 |

说明：

- 大阶段是展示层概念
- 细阶段是协议层和路由层事实源
- 三道硬门禁仍然存在：`ship-define-review`、`ship-design-review`、`ship-plan-review`

## 核心设计原则

### 1. 产物驱动而非对话驱动

- 每个阶段的完成以产物文件和 frontmatter 为准
- 阶段文档 frontmatter 是事实源
- `meta.yml` 只做恢复、汇总和展示索引

### 2. Progressive Disclosure

- 首屏只讲一个入口和五个大阶段（Discover 可选）
- 14 个细阶段（前 2 个条件性）只在高级模式或内部协议中展开
- 用户默认看到“当前目标”和“下一次需要决策的动作”，而不是一长串阶段名

### 3. 三道硬门禁

| 门禁 | 所属大阶段 | 目的 |
|------|------------|------|
| `ship-define-review` | `Define` | 确认需求清晰、AC 可验证、无歧义 |
| `ship-design-review` | `Design` | 交叉验证 contract ↔ frontend ↔ backend |
| `ship-plan-review` | `Build` | 确认任务粒度合理、依赖正确、AC 全覆盖 |

### 4. Contract-First Slicing

实施阶段任务顺序保持不变：

1. 契约层任务
2. 前后端并行任务
3. 集成任务

这条规则仍然是内部执行顺序的硬约束。

### 5. 子代理委派是执行策略，不是新阶段

- 默认流程不新增 stage，也不改变 14 个 canonical stages
- 只有 `ship-frontend-design` 与 `ship-backend-design` 是显式并行阶段
- research 取证、计划审计、测试分轨、证据整理等可以作为辅助委派
- hard gate 可由子代理起草正式 `review-*.md` 草案，但最终 `review_status`、`user_sign_off`、`signed_at` 仍由主上下文与用户完成
- `ship-build` 正式任务推进与最终 close 决策仍由主上下文与用户完成

## Feature 目录结构

```text
<target-project>/.docs/feature-YYYYMMDD-<short-name>/
├── meta.yml
├── product-brief.md           ← 仅场景 A/C（来自 ship-discover）
├── design-brief.md            ← 仅场景 A/C 且涉及 UI（来自 ship-shape）
├── requirements.md
├── review-define.md
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
    ├── wireframes/            ← 仅 ship-shape 激活时（HTML 原型 + 变体）
    │   ├── index.html
    │   ├── variant-conservative.html
    │   ├── variant-neutral.html
    │   └── variant-bold.html
    ├── brand-spec.md          ← 仅走了 Core Asset Protocol 时
    └── (其他原始资料：PRD / Figma 链接 / 截图 / ...)
```

其中：

- `current_stage` 记录内部细阶段
- `scenario` 记录入口场景（greenfield / product_provided / evolve）
- `macro_stage` 记录默认对外展示的大阶段摘要
- `workspace_mode` 记录当前 feature 来自 `single_project` 还是 `project_group`
- `projects` 记录本 feature 默认关联的一级项目名列表
- `spec_context` 记录最近一次规范解析状态、已引用规范和待沉淀 proposal
- `spec_context.workspace_mode / workspace_name / spec_root / feature_root` 记录本 feature 绑定的 workspace 解析结果

## Advanced

以下内容属于内部实现或高级使用方式：

- 完整 14 阶段路由顺序（前 2 个为条件性 Discover 前置阶段）
- `meta.yml` 细阶段状态维护
- `ship-spec` hook 契约与 `spec_context` 摘要字段
- 各阶段 SKILL 的详细输入输出
- review gate frontmatter 协议
- fast-track 的最小路径和升级/降级规则
- `agents/openai.yaml` 的安装展示元数据
- `ship-orchestrator/tests/regression-prompts.md` 的 workflow 回归场景

这些内容以 `ship-orchestrator/_templates/protocol/workflow-protocol.md` 为准。

## Workspace Spec Boundary

- `ship-spec` 的显式配置源是 workspace `.docs/ship/project.yml`
- 默认 `spec_root` 是 workspace `.docs/spec`
- 默认 `feature_root` 是 workspace `.docs`
- `project_group` 下 `projects` 是默认执行范围，不是硬安全边界
- `.docs/spec/INDEX.md` 是唯一人工路由入口；agent 先读 INDEX，再按当前阶段、domain、tech_stack 和文件范围读取候选 spec
- INDEX 分类只使用 `frontend / backend / shared`；runtime helper 仍用各 spec frontmatter 做 scan / resolve / 校验
- 缺少 `spec_root` / `INDEX.md` / 匹配 spec 时只 warning；无法确定 workspace 时直接阻塞

## 维护

修改 SKILL.md 后：

- 检查与 `ship-orchestrator/_templates/protocol/workflow-protocol.md` 的协议对齐
- 检查与 `ship-orchestrator/_templates/meta/meta.yml.template` 的字段对齐
- 检查与 `ship-orchestrator/_templates/review/review.md.template` 的章节对齐

常用校验与诊断命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_product_brief.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_ui_artifacts.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_requirements.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_contract.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_tech_discovery.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_frontend_design.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_backend_design.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_design_alignment.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_delivery_plan.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_traceability.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/build_task_preflight.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_verification.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_handoff.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/workflow_doctor.py <target-project>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <target-project>/.docs/feature-YYYYMMDD-demo --target-stage ship-tech-discovery
```
