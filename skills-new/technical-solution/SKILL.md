---
name: technical-solution
description: "技术方案阶段 skill。仅在用户明确点名 `technical-solution`，或被 `workflow-orchestrator` 路由时使用。适用于技术最新信息获取、技术选型、架构选型、greenfield / existing project 分岔、前后端详细方案、页面到接口映射、数据模型与 Solution Gate。"
---

# Technical Solution

## 目标

把已通过需求门禁的内容变成可审查的技术方案。输出：

- `tech-research.md`
- `solution.md`
- `solution-gate.md`

## 输入要求

- `requirements.md stage_status: ready`
- `requirements-gate.md gate_status: pass`

## 工作方式

1. 对第三方框架、库、OpenAI/API、脚手架、版本行为做一手资料验证
2. 区分 `greenfield_project` 与 `existing_project`
3. 写清前端方案、后端方案、页面 / API / 数据模型映射
4. 写明风险、降级、回滚和验证策略
5. 更新 `solution-gate.md`

## 关键约束

- `greenfield_project` 优先官方脚手架
- 前端方案必须吸收原型 / UIUX 约束
- 页面接哪个接口、接口返回什么、异常怎么处理，必须落文

## Gate 通过条件

- `solution.md stage_status: ready`
- `solution.md evidence_complete: true`
- `solution-gate.md gate_status: pass`

