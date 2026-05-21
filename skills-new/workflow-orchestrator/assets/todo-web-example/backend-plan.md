---
feature_stage: implementation-planning
stage_status: ready
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "TODO Web 样例采用 greenfield 后端工程。"
track: backend
---

# Backend Plan

## 1. 目标

- 提供 todo CRUD 与筛选 API，并保证校验、错误处理和持久化完整

## 2. 业务模块切片

| BE ID | 模块 / API | 目标 | 数据影响 | 验收关联 | 状态 |
| --- | --- | --- | --- | --- | --- |
| BE-01 | `GET /api/todos` | 列表与筛选 | 读 `todos` | AC-05 | ready |
| BE-02 | `POST /api/todos` | 创建 | 写 `todos` | AC-01 | ready |
| BE-03 | `PATCH /api/todos/:id` | 编辑与完成切换 | 写 `todos` | AC-02, AC-03 | ready |
| BE-04 | `DELETE /api/todos/:id` | 删除 | 删 `todos` | AC-04 | ready |

## 3. 实施任务

| BE Task | 依赖 | 改动文件 / 模块 | 完成判定 | 测试任务 |
| --- | --- | --- | --- | --- |
| BE-T01 | [] | schema + repository + list route | 列表与筛选接口可用 | API test |
| BE-T02 | [BE-T01] | create route | 可创建 todo | API test |
| BE-T03 | [BE-T01] | patch route | 可编辑标题与切换完成 | API test |
| BE-T04 | [BE-T01] | delete route | 可删除 todo | API test |

