---
name: ship-orchestrator
description: "Default entrypoint for the Ship solo-developer workflow. Use whenever the user wants to build, fix, refactor, redesign, document, verify, or ship code through a lightweight evidence-driven development loop."
---

# Ship Orchestrator

`ship-orchestrator` 是新版 ShipKit 的唯一默认入口。它面向个人开发者：少 ceremony、强事实依据、一次推进一个可验证 slice。

默认流程：

```text
Discover → Define → Understand → Design → Plan → Build → Verify → Close
```

实际执行时可以压缩或跳过不必要阶段，但不能跳过“先理解事实再修改代码”的原则。

## When to Use

- 用户要做 feature、bugfix、refactor、UI、docs、release 或恢复上一项工作。
- 用户说“帮我实现 / 修复 / 改造 / 继续 / 验证 / 交付”。
- 当前任务跨越多个步骤，需要 brief、计划、实现、验证和交付总结。

## When Not to Use

- 用户只问一个纯知识问题。
- 用户明确指定某个支持 skill，并且上下文足够清楚。
- 一步就能完成的微小编辑，且不需要工作流记录。

## Mode Detection

先判断 `work_mode`：

| Mode | 信号 | 默认起点 |
|---|---|---|
| `feature` | 新功能、MVP、增强 | `ship-discover` 或 `ship-define` |
| `bugfix` | 报错、失败、回归、线上问题 | `ship-tech-discovery` |
| `refactor` | 不改变行为、整理结构、迁移 | `ship-tech-discovery` |
| `ui` | 页面、组件、交互、视觉 | `ship-define`，可插入 `ship-shape` |
| `docs` | README、文档、规范 | `ship-define` |
| `release` | 验证、发布说明、交付总结 | `ship-verify` |

如果模式不清楚，先问一个具体问题；不要猜。

## Runtime Rules

1. **先采访到足够清楚**：目标、非目标、验收、风险不清时，先问。
2. **能从仓库找到答案就不要问用户**：先读文件、测试、配置和历史产物。
3. **默认轻量门禁**：review skills 是 checklist，不是审批关卡。
4. **单 slice 实现**：每次只推进一个 DOING slice。
5. **修改前要有文件范围**：plan 中写清 `allowed_files` 和 `verification_command`。
6. **验证失败要诊断根因**：不要机械重试。
7. **收尾要有证据**：handoff 必须列出命令、结果、风险和 follow-up。

## Stage Routing

| Stage | Route when | Output |
|---|---|---|
| `ship-discover` | 目标、用户、成功标准或边界不清 | `intent.md` |
| `ship-define` | 需要把意图变成可验收 brief | `brief.md` |
| `ship-tech-discovery` | 需要理解现有项目、复现 bug、查依赖 | `context-map.md` |
| `ship-contract` | 需要稳定 API、事件、CLI、数据或行为不变量 | `contract.md` |
| `ship-delivery-plan` | 需要拆任务、排序、确定文件范围 | `plan.md` |
| `ship-build` | 有明确 DOING slice 后实现 | `build-log.md` |
| `ship-verify` | 需要跑测试、构建、review diff 或映射 AC | `verification.md` |
| `ship-handoff` | 工作完成或停止时总结 | `handoff.md` |

## Support Skill Routing

- UI 没有设计稿但需要方向：调用 `ship-shape`。
- 前端或后端复杂到单个 contract 不够：调用 `ship-frontend-design` / `ship-backend-design`。
- 用户要求检查质量，或任务高风险：调用对应 review skill。
- 只剩一个关键业务取舍：调用 `ship-grill-me` 一次问一个问题。
- 发现重复工程规则：调用 `ship-spec` 记录或引用规范。

## Work Directory

默认使用：

```text
.docs/ship/<work-id>/
```

若已有旧版 `.docs/feature-*`，可以读取并迁移理解，但新产物默认写入 `.docs/ship/<work-id>/`。

## Standard Response Shape

开始时简要说明：

```text
我会按 lightweight Ship 流程推进：先确认目标和验收，再读仓库事实，拆一个最小 slice，实现后跑验证并交付总结。
```

阶段交付时汇报：

```text
当前阶段：<Label>
已确认：<facts>
阻塞点：<blocking_gaps 或 无>
下一步：<具体动作>
需要你决定：<仅用户能决定的问题>
```
