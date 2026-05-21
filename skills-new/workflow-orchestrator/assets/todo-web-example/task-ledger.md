---
feature_stage: implementation-execution
stage_status: ready
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "TODO Web 样例执行完成后保留总账作为 workflow 闭环证据。"
task_count: 8
---

# Task Ledger

## 状态规则

- `TODO`
- `DOING`
- `DONE`
- `BLOCKED`

## 任务总览

| task_id | track | status | depends_on | source_plan | acceptance_link | deliverable | verification | delivery_record |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FE-T01 | frontend | DONE | [] | `frontend-plan.md` | AC-01, AC-05 | page shell, API client | UI test | 列表加载、空态与错误态已实现 |
| FE-T02 | frontend | DONE | [FE-T01, BE-T01] | `frontend-plan.md` | AC-01 | create form | UI test | 创建交互与提交反馈已实现 |
| FE-T03 | frontend | DONE | [FE-T01, BE-T02] | `frontend-plan.md` | AC-02, AC-03, AC-04 | item actions | UI test | 编辑、完成、删除交互已实现 |
| FE-T04 | frontend | DONE | [FE-T01, BE-T03] | `frontend-plan.md` | AC-05 | filter tabs | UI test + smoke | 筛选交互和空结果展示已实现 |
| BE-T01 | backend | DONE | [] | `backend-plan.md` | AC-05 | schema + repository + list route | API test | 列表与筛选接口已实现 |
| BE-T02 | backend | DONE | [BE-T01] | `backend-plan.md` | AC-01 | create route | API test | 创建接口与非空校验已实现 |
| BE-T03 | backend | DONE | [BE-T01] | `backend-plan.md` | AC-02, AC-03 | patch route | API test | 编辑标题与切换完成接口已实现 |
| BE-T04 | backend | DONE | [BE-T01] | `backend-plan.md` | AC-04 | delete route | API test | 删除接口与 404 处理已实现 |

