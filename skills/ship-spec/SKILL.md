---
name: ship-spec
description: "ShipKit utility. Manages project coding specifications and connects them into the workflow through stage hooks rather than canonical stages."
---

# 规范管理 (Spec Management)

## Overview

`ship-spec` 是一个 **workflow utility**，不是 canonical stage，不进入 `workflow_stage_map.py`，也不占用 `meta.yml.current_stage`。它的职责是：

- 维护 `.docs/spec/*.md` 规范文件
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

```text
.docs/spec/
├── INDEX.md
├── coding/
│   └── <topic>.md
└── <domain>/
    └── <topic>.md
```

约束：

- `INDEX.md` 是 registry，面向人工浏览与目录维护
- 运行时匹配事实源是每个规范文件的 frontmatter，不是 `INDEX.md` 表格正文
- 缺少 `INDEX.md` 时默认告警但不中断流程

## Spec Schema

不兼容旧 schema，统一使用以下 frontmatter：

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
| `ship-tech-discovery` | 检查选型与规范兼容性 | 按 `stage_hooks + stack_tags` 匹配 |
| `ship-frontend-design` | 加载前端设计约束 | 按 `stage_hooks + stack_tags + domains` 匹配 |
| `ship-backend-design` | 加载后端设计约束 | 按 `stage_hooks + stack_tags + domains` 匹配 |
| `ship-build` | 约束任务级实现 | 按 `stage_hooks + applies_to` 匹配，并记录 `spec_id` |
| `ship-handoff` | 生成待沉淀规范提案 | 汇总 `meta.yml.spec_context.referenced_spec_ids` |

默认策略是 **Warn Then Continue**：

- 缺少 `INDEX.md`
- 找不到匹配规范
- 规范 frontmatter 不合法

以上都应写入 `meta.yml.spec_context.warnings` 和阶段产物的 `spec_warnings`，但默认不阻塞推进。

## Runtime Helpers

推荐 helper：

- `python3 skills/ship-orchestrator/scripts/spec_runtime.py scan .docs/spec`
- `python3 skills/ship-orchestrator/scripts/spec_runtime.py resolve ship-build --spec-root .docs/spec --file src/app.ts`
- `python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py sync-spec .docs/feature-YYYYMMDD-demo/meta.yml --stage ship-build --file src/app.ts`
- `python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py record-spec-proposal .docs/feature-YYYYMMDD-demo/meta.yml --proposal-id proposal-001 --title "抽取统一错误处理规范" --source-stage ship-handoff --target-spec-id error-handling --summary "来自本次交付的重复错误处理模式"`

约束：

- `spec_runtime.py` 负责 scan / resolve，不负责修改阶段产物
- `feature_meta_runtime.py sync-spec` 负责把最近一次解析结果同步到 `meta.yml.spec_context`
- 阶段 skill 必须自行把 `spec_checked_at`、`referenced_spec_ids`、`spec_warnings` 写入产物或任务证据

## Proposal-First Writeback

`ship-handoff` 采用 **Proposal-First** 策略：

- 先在 `handoff.md` 和 `meta.yml.spec_context.pending_proposals` 记录待沉淀 proposal
- proposal 至少包含 `proposal_id`、`title`、`source_stage`、`target_spec_id`、`summary`
- 不在 `ship-handoff` 中直接创建或修改 `.docs/spec/*.md`
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
