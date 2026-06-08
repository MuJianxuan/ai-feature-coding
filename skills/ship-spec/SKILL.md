---
name: ship-spec
description: "ShipKit utility. Manages workspace coding specifications and connects them into the workflow through stage hooks rather than canonical stages."
---

# 规范管理 (Spec Management)

## Overview

`ship-spec` 是一个 **workflow utility**，不是 canonical stage，不进入 `workflow_stage_map.py`，也不占用 `meta.yml.current_stage`。它的职责是：

- 维护 workspace 下 `spec_root` 的规范文件
- 通过 helper 在关键阶段解析和匹配规范
- 让各阶段产物与任务证据显式记录引用过的 `spec_id`
- 在 `ship-handoff` 阶段生成待沉淀 proposal，而不是静默修改规范

统一协议以 [`workflow-protocol.md`](./../ship-orchestrator/_templates/protocol/workflow-protocol.md) 为准；本文件只描述 utility 自身职责和使用方法。

## When to Use

- 初始化项目规范目录时
- `ship-tech-discovery / ship-frontend-design / ship-backend-design / ship-build / ship-handoff` 需要消费规范时
- 用户明确要求“把这个模式沉淀为规范”时
- code review 中发现重复问题，需要升级为稳定规则时

## When NOT to Use

- 简单 bug fix 且不涉及复用模式时
- `ship-build` 中途为追求局部整洁而打断当前任务去写规范
- 把规范当成新的 workflow stage 使用

## Directory Structure

单项目：

```text
project-a/
└── .docs/
    ├── ship/project.yml
    └── spec/
        ├── INDEX.md
        ├── frontend/<topic>.md
        ├── backend/<topic>.md
        └── shared/<topic>.md
```

多项目组：

```text
workspace/
├── .docs/
│   ├── ship/project.yml
│   └── spec/
│       ├── INDEX.md              # 顶层导航，不作为具体规范全集
│       ├── _shared/
│       │   ├── INDEX.md
│       │   └── <topic>.md
│       ├── web/
│       │   ├── INDEX.md
│       │   └── frontend/<topic>.md
│       └── api/
│           ├── INDEX.md
│           └── backend/<topic>.md
├── web/
└── api/
```

约束：

- `single_project` 下 `.docs/spec/INDEX.md` 是人工路由入口
- `project_group` 下 `.docs/spec/INDEX.md` 只做顶层导航；具体规范入口是 `.docs/spec/_shared/INDEX.md` 和 `.docs/spec/<project>/INDEX.md`
- `project_group` 下 `<project>` 必须来自 `.docs/ship/project.yml.projects`
- `INDEX.md` 表格只使用 `frontend / backend / shared` 三类；`_shared` 仅用于 error code、date/time、trace id 等真正跨项目规范
- 运行时 helper 仍可读取每个规范文件的 frontmatter 做 scan / resolve / 校验；frontmatter 不新增 `spec_type` 或 `discipline`
- `INDEX.md` 与 spec 文件 frontmatter 必须保持一致；不一致时记录 warning，默认 Warn Then Continue
- 缺少 `INDEX.md` 时默认告警但不中断流程
- project_group 只支持一级目录项目名；不支持 `apps/web` 作为 project registry 基础模型

## INDEX.md Template

`INDEX.md` 推荐写法：

```markdown
# Spec Index

| Spec ID | 分类 | 适用阶段 | 适用技术/模块 | 文件路径 | 何时使用 | 备注 |
|---|---|---|---|---|---|---|
| react-query-data-fetching | frontend | ship-frontend-design, ship-build | React, data fetching | frontend/react-query-data-fetching.md | 页面需要 server state / cache / mutation |  |
| backend-service-methods | backend | ship-backend-design, ship-build | Node, service layer | backend/service-methods.md | 设计 Service 方法签名和调用边界 |  |
| redis-cache-policy | backend | ship-backend-design, ship-build | Redis | backend/redis-cache-policy.md | 需求涉及缓存、限流、会话、分布式锁 |  |
| mq-event-contract | backend | ship-contract, ship-backend-design, ship-build | MQ | backend/mq-event-contract.md | 需求涉及异步消息、事件、worker |  |
| shared-error-codes | shared | ship-contract, ship-frontend-design, ship-backend-design, ship-build | Error Model | shared/error-codes.md | 需求涉及跨端错误码或异常处理 |  |
```

规则：

- `single_project` 只保留 `.docs/spec/INDEX.md` 一个规范索引
- `project_group` 保留 `.docs/spec/INDEX.md` 作为导航，并为 `_shared` 和每个项目维护自己的 `INDEX.md`
- `分类` 只允许 `frontend / backend / shared`
- `文件路径` 使用相对当前 `INDEX.md` 所在 spec root 的路径
- 表格是人工路由入口，不替代 spec 文件 frontmatter

## Workspace Config

`ship-spec` 的 workspace boundary 由 workspace `.docs/ship/project.yml` 显式声明：

```yaml
schema_version: 2
workspace_mode: project_group
workspace_name: demo-workspace
feature_root: ".docs"
projects:
  - web
  - api
```

规则：

- `workspace_mode` 只能是 `single_project` 或 `project_group`
- `feature_root` 按 workspace root relative 表示
- `project_group` 下 `projects` 必须是 workspace 下一级目录名
- feature `projects` 是默认执行范围，不是硬安全边界
- project_group 下 spec resolve 只能使用 `projects` 中已声明的项目名
- 缺少 workspace 配置时，不允许 silent guess
- workspace 无法确定时阻塞；workspace 已确定但 spec 缺失时只 warning

## Spec Schema

不兼容旧 schema，统一使用以下 frontmatter；本轮不新增 `spec_type`：

```markdown
---
spec_id: react-query-data-fetching
scope: module  # project | module | file
stage_hooks:
  - ship-tech-discovery
  - ship-frontend-design
  - ship-build
stack_tags:
  - react
  - tanstack-query
domains:
  - todo
  - dashboard
applies_to:
  - "src/features/todo/**/*.ts"
  - "src/features/todo/**/*.tsx"
last_updated: "2026-05-23T10:00:00+08:00"
---
```

字段说明：

- `spec_id`：稳定标识，必须唯一
- `scope`：规范适用粒度
- `stage_hooks`：允许消费该规范的 workflow hook 点
- `stack_tags`：技术栈标签；为空表示跨技术栈通用
- `domains`：业务域标签；为空表示全局规范
- `applies_to`：`ship-build` 用于文件 glob 匹配；设计阶段可忽略
- `last_updated`：最近更新时间

## Hook Model

`ship-spec` 通过以下 hook 接入主链路：

| Hook 点 | 用途 | 运行时行为 |
|--------|------|-----------|
| `ship-tech-discovery` | 检查选型与规范兼容性 | single 读 `.docs/spec/INDEX.md`；project_group 读 `_shared`，并按已确认目标项目读 `<project>/INDEX.md` |
| `ship-frontend-design` | 加载前端设计约束 | 先读 `_shared`，再按 Project Reality First 确认的 UI 项目读取 `<project>/INDEX.md` 中 `frontend/shared` 候选 |
| `ship-backend-design` | 加载后端设计约束 | 先读 `_shared`，再按 Project Reality First 确认的 API/service 项目读取 `<project>/INDEX.md` 中 `backend/shared` 候选 |
| `ship-build` | 约束任务级实现 | project_group 必须使用任务 `project:` 定位 `<project>/INDEX.md`；再按 `stage_hooks + applies_to` 匹配 |
| `ship-handoff` | 生成待沉淀规范提案 | 汇总 `meta.yml.spec_context.referenced_spec_ids`，proposal 指向 `_shared` 或具体 `<project>` spec root |

默认策略是 **Warn Then Continue**：

- 缺少 `INDEX.md`
- 找不到匹配规范
- 规范 frontmatter 不合法

以上都应写入 `meta.yml.spec_context.warnings` 和阶段产物的 `spec_warnings`，但默认不阻塞推进。

### Agent 使用规则

每个需要 spec 的阶段必须：

1. 先根据 `.docs/ship/project.yml.workspace_mode` 判断 spec 路由
2. `single_project` 读取 `.docs/spec/INDEX.md`；`project_group` 读取 `.docs/spec/_shared/INDEX.md`，并按当前目标项目读取 `.docs/spec/<project>/INDEX.md`
3. 根据当前阶段、需求 domain、project_scope、tech_stack 和涉及文件，从 `frontend / backend / shared` 分类中挑选候选 spec
4. 再读取候选 spec 文件
5. 把实际使用的 `spec_id` 写入对应产物的 `referenced_spec_ids` 或任务 `spec_refs`
6. 若 INDEX 和 frontmatter 不一致，记录 warning
7. 若找不到匹配 spec，Warn Then Continue

## Runtime Helpers

推荐 helper：

- `python3 skills/ship-orchestrator/scripts/spec_runtime.py scan --project-config <workspace>/.docs/ship/project.yml`
- `python3 skills/ship-orchestrator/scripts/spec_runtime.py resolve ship-build --project-config <workspace>/.docs/ship/project.yml --project web --file web/src/app.ts`
- `python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec <workspace>/.docs/feature-YYYYMMDD-demo/meta.yml --project-config <workspace>/.docs/ship/project.yml --stage ship-build --project web --file web/src/app.ts`
- `python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py record-spec-proposal <workspace>/.docs/feature-YYYYMMDD-demo/meta.yml --proposal-id proposal-001 --title "抽取统一错误处理规范" --source-stage ship-handoff --target-spec-id error-handling --summary "来自本次交付的重复错误处理模式"`

约束：

- `spec_runtime.py` 负责 scan / resolve，不负责修改阶段产物
- `feature_meta_runtime.py sync-spec` 负责把最近一次解析结果同步到 `meta.yml.spec_context`
- 阶段 skill 必须自行把 `spec_checked_at`、`referenced_spec_ids`、`spec_warnings` 写入产物或任务证据
- 多项目父目录下必须先显式初始化 workspace config，并在 feature meta 中记录默认关联 projects
- project_group 下 `ship-build` 必须由任务 `project:` 显式提供目标项目；不得从 `allowed_files` 路径反推
- 本轮 runtime helper 不把 `INDEX.md` 变成唯一机器事实源；若后续增强 INDEX 表格校验，只能产生 warning，不阻塞流程

## Proposal-First Writeback

`ship-handoff` 采用 **Proposal-First** 策略：

- 先在 `handoff.md` 和 `meta.yml.spec_context.pending_proposals` 记录待沉淀 proposal
- proposal 至少包含 `proposal_id`、`title`、`source_stage`、`target_spec_id`、`summary`
- 不在 `ship-handoff` 中直接创建或修改 workspace `spec_root` 下的规范文件
- 用户确认后，才执行真正的规范写回

## Authoring Checklist

- [ ] 每份规范都使用统一 frontmatter
- [ ] `stage_hooks` 只包含允许的 hook 值
- [ ] `stack_tags`、`domains`、`applies_to` 与目标阶段的消费方式一致
- [ ] `spec_id` 全局唯一
- [ ] 规则具备正例 / 反例 / 例外，不写“写好代码”式空话
- [ ] 若规范仅适用于 `ship-build`，`applies_to` 不能留空
- [ ] 若规范只用于设计约束，`applies_to` 可为空但 `stage_hooks` 不能空

## Red Flags

- 把 `ship-spec` 当作新的 stage 接入 stage map
- `INDEX.md` 表格和真实 spec 文件长期不一致
- 设计阶段或 build 阶段消费了规范，但产物/任务证据里没有 `referenced_spec_ids`
- `ship-handoff` 直接写规范文件而未经过 Proposal-First
- `spec_runtime.py` 告警长期存在但没人处理
