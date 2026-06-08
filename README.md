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

这 5 个大阶段是默认对外视图，其中 `ship-discover` 只在场景 A（零到一）和场景 C（迭代增强）出现；`ship-shape` 默认随 A/C 激活，场景 B/D 在 UIUX Material Gate 中经用户显式授权生成 wireframe 时可临时插入。内部仍然保留细阶段、硬门禁、文档产物和恢复协议，用于精确推进与诊断。

`ship-spec` 以 workflow utility 形态接入，不占用 stage map；它会在 `ship-tech-discovery`、`ship-frontend-design`、`ship-backend-design`、`ship-build`、`ship-handoff` 被自动消费并通过 `meta.yml.spec_context` 留痕。规范边界始终是 workspace；single_project 读 `.docs/spec/INDEX.md`，project_group 读 `.docs/spec/_shared/INDEX.md`，并按当前目标项目读取 `.docs/spec/<project>/INDEX.md`。

Design 大阶段现在采用 Project Reality First：已有项目上的需求必须先通过 `ship-tech-discovery` 发现真实功能、表、API、页面、服务、权限、worker/MQ、日志/metrics 和既有 feature 文档，再进入技术调研、选型、contract、frontend/backend design。规范索引仍只使用 `frontend / backend / shared` 分类，frontmatter schema 不新增 `spec_type`。

`technical_plan_provided`（技术方案选区）入口适用于已有项目迭代：用户提供技术方案文件或粘贴片段，并指定章节、接口、模块等 selected scope。该入口要求 `existing_project`，跳过 `ship-define` 执行阶段与 `ship-define-review` hard gate；但 `ship-tech-discovery` 会为 selected scope 派生最小 `requirements.md` index，frontmatter 仍使用 `stage: ship-define`、`generation_mode: technical_plan`，仅用于 AC traceability。不会把整份技术方案纳入计划，未选中内容默认 `out_of_scope`，进入 `ship-delivery-plan` 前仍必须通过 `ship-design-review`。

源码修改屏障：除 workspace `feature_root` 下的 `feature-*` 工作流产物（默认 `.docs/feature-*`）外，任何业务源码、测试、配置、迁移、脚本或构建文件修改都必须等到 `current_stage: ship-build`，且 `review-plan.md` 已 `approved + user_sign_off + signed_at`，并通过 `stage_transition_check.py --target-stage ship-build` 与 `build_task_preflight.py`。技术方案选区入口即使从 `ship-tech-discovery` 开始，也不得在 Design / Plan / Review 阶段直接编码。

Build 阶段的任务源（`frontend-plan.md`、`backend-plan.md`）都使用同一任务项合同：机器字段保留 `allowed_files`、AC refs、verification command，同时每个任务必须包含 `任务目标 / 上下文 / 约束 / 验收 / 输出` 执行简报。

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

### 技术方案选区

```text
使用 ship-orchestrator，基于 resource/order-export-tech-design.md 的 3.2 订单导出异步任务章节生成 delivery plan。
```

### 继续已有 feature

```text
继续 <workspace>/<feature-root>/feature-YYYYMMDD-<short-name>/
```

### 高级模式

如果你明确知道要打到哪个内部阶段，也可以直接调用对应 `ship-*` skill；但这不是默认路径。

## 结构说明

- `skills/README.md`：默认用户视图，重点讲 5 个大阶段（Discover 可选）
- `skills/ship-orchestrator/`：统一入口与路由规则
- `skills/ship-orchestrator/_templates/`：协议与模板
- `skills/agents/openai.yaml`：安装后默认入口与维护命令元数据
- `skills/ship-orchestrator/tests/regression-prompts.md`：workflow 回归场景
- `skills/ship-*/references/`：阶段内参考模板，不属于共享协议
- `.docs/ship/project.yml`：workspace 级显式配置，声明 `workspace_mode / workspace_name / feature_root / spec_root / projects`
- `.docs/spec/INDEX.md`：single_project 下的人工 spec 路由入口；project_group 下作为顶层导航
- `.docs/spec/_shared/INDEX.md` 与 `.docs/spec/<project>/INDEX.md`：project_group 下的具体 spec 路由入口
- workspace 下的 `.docs/`：默认 feature 运行时产物和规范沉淀位置

## 维护

修改 workflow 相关文档后，至少检查：

- README 与 `workflow-protocol.md` 的阶段描述一致
- `meta.yml.template` 的字段与 orchestrator 说明一致
- 默认视图仍然是 5 大阶段（Discover 可选），细阶段只在高级/诊断视图暴露

可执行校验命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_product_brief.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_ui_artifacts.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_requirements.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_contract.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_tech_discovery.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_frontend_design.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_backend_design.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_design_alignment.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_delivery_plan.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_traceability.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/build_task_preflight.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_verification.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/validate_handoff.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/workflow_doctor.py <workspace>/.docs/feature-YYYYMMDD-demo
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <workspace>/.docs/feature-YYYYMMDD-demo --target-stage ship-tech-discovery
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
python3 skills/ship-orchestrator/scripts/spec_runtime.py scan --project-config <workspace>/.docs/ship/project.yml
```

最小 runtime helper：

```bash
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init-workspace <workspace> --workspace-mode project_group --workspace-name demo-workspace --project web --project api
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init feature-YYYYMMDD-demo --project-config <workspace>/.docs/ship/project.yml --project web --project api --feature-name "Demo Feature" --feature-id "feature-YYYYMMDD-demo" --scenario product_provided
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py refresh <workspace>/.docs/feature-YYYYMMDD-demo/meta.yml
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec <workspace>/.docs/feature-YYYYMMDD-demo/meta.yml --project-config <workspace>/.docs/ship/project.yml --stage ship-build --project web --file web/src/app.ts
```

最小 workspace config 示例：

```yaml
schema_version: 2
workspace_mode: project_group
workspace_name: demo-workspace
feature_root: ".docs"
spec_root: ".docs/spec"
projects:
  - web
  - api
```

多项目父目录场景下，必须先初始化 workspace config，再为 feature 选择关联 projects；缺少 spec 只会 warning，缺少 workspace config 会直接阻塞。
