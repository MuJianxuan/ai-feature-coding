# TODO Web App — 范本文档集

本目录是一套完整的 TODO Web App 开发工作流范本，展示 skills-new 套件从需求到交付的全流程产物。

## 技术栈

- 前端: React 18 + Vite 5 + TypeScript 5 + TailwindCSS
- 后端: Node 20 + Express 4 + Prisma 5 + SQLite
- 测试: Vitest + Testing Library + Playwright + Supertest

## 文档清单

```
todo-app-example/
├── README.md                    # 本文件
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
    └── notes.md                 # 实施要点说明
```

## 使用方式

1. 阅读各文档了解每个阶段的产物标准
2. 在实际项目中用 `ship-orchestrator` 启动流程时，参考这些范本的结构和详细程度
3. 范本中的内容是"最小完整"示例——真实项目可能更复杂，但不应比这更简略
