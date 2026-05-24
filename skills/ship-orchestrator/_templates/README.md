# skills-new — 共享模板

本目录包含跨 skill 共享的协议与模板，用于维持 workflow 的单一事实源。

## 目录结构

```
_templates/
├── meta/
│   └── meta.yml.template          # feature 级索引模板（恢复 / 汇总 / 路由）
├── review/
│   └── review.md.template         # 硬门禁评审记录模板（define/design/plan 三个 hard gate 共用）
├── protocol/
│   └── workflow-protocol.md       # 共享协议单源（阶段 id / 门禁 / 状态机）
└── README.md                      # 当前说明文档
```

## 使用方式

### meta/meta.yml.template

每个新 feature 启动时，由 `ship-orchestrator` 复制到 `.docs/feature-YYYYMMDD-<short-name>/meta.yml`，作为该 feature 的索引文件。

阶段文档不再各自维护 `project_context` / `pipeline_mode` 等冗余字段，只在 `meta.yml` 中维护一次。阶段是否 `ready` / `approved` 仍以产物 frontmatter 为准。

`meta.yml` 同时维护两层视图：

- `current_stage`：内部 canonical stage id，用于恢复和精确路由
- `macro_stage`：默认对外展示的 5 大阶段摘要（Discover 可选），用于状态列表和执行摘要
- `delegation`：子代理偏好、节点级覆盖与 delegation warning，用于决定“当前上下文 vs 子代理策略”
- `spec_context`：`ship-spec` 的摘要索引，用于恢复时快速知道最近一次规范解析结果、已引用规范和待沉淀 proposal

### protocol/workflow-protocol.md

共享协议单源。凡是涉及 stage id、门禁字段、`verification.md` ownership、fast-track 规则、子代理委派边界、`ship-spec` hook 契约，都先对照此文档，再更新其他 SKILL。

其中 delegation 相关的 canonical `node_id`、自动解析顺序、warning 落点，也统一以该协议为准，不允许阶段文档自行发明 key 名。

### review/review.md.template

硬门禁阶段（ship-define-review / ship-design-review / ship-plan-review）的产物模板。每次评审产生一份独立的 `review-<stage>.md` 文件，含：

- 评审 checklist 逐条打勾
- 发现的问题（Critical / Major / Minor 三级）
- 用户原话签字
