# skills-new — 共享模板与示例

本目录包含跨 skill 共享的模板和一份完整的 TODO Web App 范本。

## 目录结构

```
_templates/
├── meta/
│   └── meta.yml.template          # feature 级元数据模板（集中维护，替代 6 处 frontmatter 重复）
├── review/
│   └── review.md.template         # 硬门禁评审记录模板（02/08/11 阶段共用）
└── todo-app-example/              # TODO Web App 完整范本（端到端示例）
    ├── README.md
    ├── requirements/
    │   └── requirements.md
    ├── design/
    │   ├── tech-selection.md
    │   ├── api-contract.md
    │   ├── frontend-design.md
    │   └── backend-design.md
    ├── plan/
    │   ├── frontend-plan.md
    │   └── backend-plan.md
    └── implementation/
        └── notes.md
```

## 使用方式

### meta/meta.yml.template

每个新 feature 启动时，由 `ship-orchestrator` 复制到 `.docs/feature-YYYYMMDD-<short-name>/meta.yml`，作为该 feature 的中央元数据文件。

阶段文档不再各自维护 `project_context` / `pipeline_mode` 等冗余字段，只在 `meta.yml` 中维护一次。

### review/review.md.template

硬门禁阶段（ship-intake-review / ship-design-review / ship-plan-review）的产物模板。每次评审产生一份独立的 `review-<stage>.md` 文件，含：

- 评审 checklist 逐条打勾
- 发现的问题（Critical / Major / Minor 三级）
- 用户原话签字

### todo-app-example/

一套完整的端到端示例，展示从需求到交付的所有产物。技术栈：

- 前端: React 18 + Vite 5 + TypeScript 5 + TailwindCSS + TanStack Query + Zustand
- 后端: Node 20 + Express 4 + Prisma 5 + SQLite + zod + pino
- 测试: Vitest + Testing Library + Playwright + Supertest

适用场景：

- 学习 skills-new 流程时作为"标准答案"参考
- 实际项目启动时作为模板基准（详细程度的下限）
- 验证 skills 套件能端到端跑通的最小可运行示例
