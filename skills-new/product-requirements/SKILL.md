---
name: product-requirements
description: "需求阶段 skill。仅在用户明确点名 `product-requirements`，或被 `workflow-orchestrator` 路由时使用。适用于吸收 PRD、原型、UIUX、Figma、墨刀、会议纪要和接口草案，完成需求评审、范围收敛、业务域建模、AC 设计和 Requirements Gate。"
---

# Product Requirements

## 目标

合并旧 `discovery + requirement-intake` 的精华，在一个阶段内完成：

- 需求资料索引
- 仓库现状与项目模式判定
- 需求评审与范围澄清
- 业务域建模
- AC 设计
- `requirements-gate.md`

## 前置要求

- 存在 `workflow_dir`
- `source-index.md` 可写
- 至少有一份原始需求资料或明确的需求描述

## 工作方式

1. 先查仓库、现有模块、相似能力和项目入口
2. 再吸收 PRD / 原型 / UIUX / Figma / 墨刀资料
3. 识别 `existing_project` 或 `greenfield_project`
4. 输出 `requirements.md`
5. 对照 gate 清单更新 `requirements-gate.md`

## 强制覆盖项

- in-scope / out-of-scope
- 业务域与 actor
- 页面 / UI 范围
- AC 与验证方式
- 非功能要求
- 待确认问题

## Gate 通过条件

- `requirements.md stage_status: ready`
- `requirements.md evidence_complete: true`
- `requirements-gate.md gate_status: pass`

