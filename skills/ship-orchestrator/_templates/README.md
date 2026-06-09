# Ship Orchestrator Templates

本目录保存新版 Ship Solo workflow 的共享模板。默认面向个人开发者：轻量门禁、证据驱动、一次一个 slice。

## Layout

```text
_templates/
├── meta/
│   └── meta.yml.template
├── project/
│   └── project.yml.template
├── protocol/
│   ├── workflow-protocol.md
│   ├── stage-routing.md
│   ├── gate-protocol.md
│   ├── routing-protocol.md
│   ├── resume-protocol.md
│   ├── scenario-detection.md
│   ├── scope-detection.md
│   └── feature-initialization.md
└── review/
    ├── review.md.template
    └── review-gate-reference.md
```

## Default Workspace

每个新工作项默认写入：

```text
.docs/ship/<work-id>/meta.yml
```

旧版 `feature-*` 目录可以兼容读取，但新版模板和文档以 `.docs/ship/<work-id>/` 为准。

## Source of Truth

- 阶段映射：`scripts/workflow_stage_map.py`
- 主协议：`protocol/workflow-protocol.md`
- 元数据模板：`meta/meta.yml.template`
- 校验：`scripts/validate_workflow_docs.py`

凡是涉及 stage id、review checklist、source edit barrier、子代理委派边界、`ship-spec` hook 契约，都先对照 `workflow-protocol.md`，再更新其他文档。
