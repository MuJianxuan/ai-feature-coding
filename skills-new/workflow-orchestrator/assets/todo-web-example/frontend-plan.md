---
feature_stage: implementation-planning
stage_status: ready
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "TODO Web 样例采用 greenfield 前端工程。"
track: frontend
---

# Frontend Plan

## 1. 目标

- 实现单页 TODO 界面和所有核心交互，并与后端 API 对齐

## 2. 页面与交互切片

| FE ID | 页面 / 组件 | 目标 | 依赖接口 | 验收关联 | 状态 |
| --- | --- | --- | --- | --- | --- |
| FE-01 | TodoPage | 列表加载与空态 | `GET /api/todos` | AC-01, AC-05 | ready |
| FE-02 | CreateForm | 创建 todo | `POST /api/todos` | AC-01 | ready |
| FE-03 | TodoItem | 编辑 / 完成 / 删除 | `PATCH /api/todos/:id`, `DELETE /api/todos/:id` | AC-02, AC-03, AC-04 | ready |
| FE-04 | FilterTabs | 筛选展示 | `GET /api/todos?filter=` | AC-05 | ready |

## 3. 实施任务

| FE Task | 依赖 | 改动文件 / 模块 | 完成判定 | 测试任务 |
| --- | --- | --- | --- | --- |
| FE-T01 | [] | page shell, API client | 列表成功加载 | UI test |
| FE-T02 | [FE-T01, BE-T01] | create form | 可创建 todo | UI test |
| FE-T03 | [FE-T01, BE-T02] | item actions | 可编辑、完成、删除 | UI test |
| FE-T04 | [FE-T01, BE-T03] | filter tabs | 筛选结果正确 | UI test + smoke |

