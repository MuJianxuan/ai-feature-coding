---
feature_stage: verification-handoff
stage_status: complete
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "TODO Web 样例用作 greenfield workflow 验证。"
---

# Verification

## 1. AC 映射

| AC ID | 验证方式 | 证据 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| AC-01 | API test + UI test | create case | PASS | 标题非空 |
| AC-02 | API test + UI test | edit case | PASS | 标题更新可见 |
| AC-03 | API test + UI test | toggle case | PASS | 完成状态切换正确 |
| AC-04 | API test + UI test | delete case | PASS | 删除后列表不再显示 |
| AC-05 | API test + UI test + smoke | filter case | PASS | all / active / completed 一致 |

## 2. 后端测试

| 命令 / 步骤 | 目标 | 结果 | 摘要 |
| --- | --- | --- | --- |
| `npm test -- api` | CRUD 与筛选 | PASS | 覆盖 create/edit/toggle/delete/filter |

## 3. 前端测试

| 命令 / 步骤 | 目标 | 结果 | 摘要 |
| --- | --- | --- | --- |
| `npm test -- ui` | 交互与状态展示 | PASS | 覆盖列表、空态、错误态、筛选 |

## 4. 手工 Smoke

| 步骤 | 预期 | 实际 | 结果 |
| --- | --- | --- | --- |
| 创建 todo 并筛选 | 新项出现且筛选正确 | 与预期一致 | PASS |

