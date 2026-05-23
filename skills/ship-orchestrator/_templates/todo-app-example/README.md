# TODO Web App — 范本文档集

本目录是一套 TODO Web App 阶段产物范本，展示 skills-new 套件在 `requirements / design / plan / meta view` 上的典型写法。

重要说明：

- 本目录按产物类型分组，方便学习和复制
- 它不是某一时刻的完整 feature 运行时快照
- 运行时索引应以真实项目里的 `.docs/feature-YYYYMMDD-<short-name>/meta.yml` 为准
- 默认对外视图应展示 `Define → Design → Build → Close`，内部仍用 `current_stage` 记录 canonical stage id

## 技术栈

- 前端: React 18 + Vite 5 + TypeScript 5 + TailwindCSS
- 后端: Node 20 + Express 4 + Prisma 5 + SQLite
- 测试: Vitest + Testing Library + Playwright + Supertest

## 文档清单

```
todo-app-example/
├── README.md                    # 本文件
├── meta-view-example.md         # meta.yml / macro_stage 视图示例
├── requirements/
│   └── requirements.md          # 需求清单范本
├── design/
│   ├── tech-selection.md        # 技术选型 + ADR
│   ├── api-contract.md          # 接口规约
│   ├── frontend-design.md       # 前端方案
│   └── backend-design.md        # 后端方案
├── plan/
│   ├── frontend-plan.md         # 前端实施计划
│   └── backend-plan.md          # 后端实施计划
└── implementation/
    └── notes.md                 # 实施要点说明（示例备注目录，不代表 canonical stage id）
```

## 使用方式

1. 阅读各文档了解每个阶段的产物标准
2. 在实际项目中用 `ship-orchestrator` 启动流程时，参考这些范本的结构和详细程度
3. 范本中的内容是当前已提供阶段的参考下限；真实项目可能更复杂，但不应比这更简略

## 默认展示视图

用户默认应看到大阶段视图，而不是一长串内部阶段名：

| 默认视图 | 内部事实源 |
|----------|------------|
| `Define` | `ship-intake`, `ship-intake-review` |
| `Design` | `ship-research`, `ship-stack`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `Build` | `ship-frontend-plan`, `ship-backend-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `Close` | `ship-handoff` |

如果你想看 `meta.yml` 里的实际索引结构，参考 [meta-view-example.md](/Users/rao/AiDoWork/ai-feature-coding/skills/ship-orchestrator/_templates/todo-app-example/meta-view-example.md:1)。
