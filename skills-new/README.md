# Skills-New Workflow

这是一套基于现有 coding workflow 重组后的完整开发工作流。

## 设计目标

- 基于 PRD、原型、UIUX、Figma、墨刀等需求资料推进完整交付
- 显式经过需求评审、技术方案、实施计划三道门禁
- 支持 `frontend-plan.md + backend-plan.md` 双计划文档
- 支持 `existing_project` 与 `greenfield_project` 两类路径
- 最终可通过编码、测试、验收和实施汇报完成收口

## Skill 结构

| Skill | 作用 |
| --- | --- |
| `workflow-orchestrator` | 总控、路由、gate 判定、模板初始化 |
| `product-requirements` | 需求吸收、评审、范围澄清、业务域和 AC |
| `technical-solution` | 技术调研、技术选型、架构选型、前后端方案 |
| `implementation-planning` | 前后端独立实施计划、依赖、测试任务 |
| `implementation-execution` | 基于计划逐项编码与记录证据 |
| `verification-handoff` | 前后端测试、AC 映射、验收汇报 |

## 关键目录

```text
skills-new/
  workflow-orchestrator/
    WORKFLOW_CONTRACT.md
    assets/workflow-template/
    assets/todo-web-example/
    scripts/validate_skills_new.py
```

## 验证

运行：

```bash
python3 skills-new/workflow-orchestrator/scripts/validate_skills_new.py
```

