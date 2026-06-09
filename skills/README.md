# Ship skills — 个人开发者通用开发流程套件

这套 skills 用 `ship-orchestrator` 统一入口，把常见个人开发任务（feature、bugfix、refactor、UI、docs、release）推进成一个轻量闭环：

```text
Discover → Define → Understand → Design → Plan → Build → Verify → Close
```

新版不再默认执行企业式 hard gate。`ship-define-review`、`ship-design-review`、`ship-plan-review` 保留为可选 review checklist，用于复杂或高风险任务。

## 默认阶段

| 阶段 | Skill | 目标 | 产物 |
|---|---|---|---|
| Discover | `ship-discover` | 弄清真实目标、约束和最小范围 | `intent.md` |
| Define | `ship-define` | 写 brief、AC、假设、风险 | `brief.md` |
| Understand | `ship-tech-discovery` | 查仓库现状和技术事实 | `context-map.md` |
| Design | `ship-contract` | 定义最小稳定边界 | `contract.md` |
| Plan | `ship-delivery-plan` | 拆成原子 slices | `plan.md` |
| Build | `ship-build` | 单 slice 实现和记录 | `build-log.md` |
| Verify | `ship-verify` | 验证 AC 与收集证据 | `verification.md` |
| Close | `ship-handoff` | 交付总结和后续事项 | `handoff.md` |

## 自动压缩规则

- **bugfix**：通常从 `ship-tech-discovery` 开始，`brief.md` 可压缩为现象 / 期望 / 复现。
- **refactor**：`contract.md` 写行为不变量，不要求 API 契约。
- **UI**：可插入 `ship-shape` 生成或分析 UI 方向。
- **docs**：可跳过深度设计，直接 brief → plan → build → verify。
- **release**：从 verify/close 恢复，聚焦验证证据和发布说明。

## 工作目录

默认产物写入：

```text
.docs/ship/<work-id>/
├── meta.yml
├── intent.md
├── brief.md
├── context-map.md
├── contract.md
├── plan.md
├── build-log.md
├── verification.md
├── handoff.md
├── reviews/
└── resource/
```

## 轻量门禁

每个阶段只回答四件事：

1. 输入是否可信？
2. 输出是否足够进入下一步？
3. 是否还有 blocking gap？
4. 有什么证据支持这个结论？

如果答案不清楚，先查仓库或问用户；不要假设。

## 支持技能

- `ship-shape`：UI/UX 原型与设计方向。
- `ship-frontend-design` / `ship-backend-design`：复杂任务的深度设计。
- `ship-define-review` / `ship-design-review` / `ship-plan-review`：可选质量检查。
- `ship-grill-me`：一次一个阻塞问题。
- `ship-spec`：规范沉淀与引用。

## 维护

修改 workflow 后至少运行：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
```
