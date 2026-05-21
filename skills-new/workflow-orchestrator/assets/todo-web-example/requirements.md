---
feature_stage: product-requirements
stage_status: ready
updated_at: 2026-05-21T00:00:00+08:00
evidence_complete: true
project_mode: greenfield_project
project_mode_evidence: "样例假定从 0 创建一个 Web 应用，用于验证 workflow 的 greenfield 路径。"
---

# Requirements

## 1. 背景与目标

- 业务背景：提供一个最小但完整的 TODO Web 应用，用来验证 workflow 是否能支撑从需求到验收
- 用户问题：用户需要创建、编辑、完成、删除和筛选个人 todo
- 成功指标：核心 CRUD 与筛选路径全部可用，关键 AC 可通过前后端测试与手工 smoke 验证

## 2. 项目模式判定

- project_mode：greenfield_project
- 判定证据：目标明确为完整 TODO Web 应用样例，不依赖已有业务仓库

## 3. 范围

### In Scope

- Todo 列表页
- 创建 todo
- 编辑 todo 文本
- 切换完成状态
- 删除 todo
- 按 `all / active / completed` 筛选

### Out of Scope

- 登录注册
- 多用户共享
- 标签、提醒、拖拽排序

## 4. 原型 / UI 约束

- 页面范围：单页列表页
- 核心交互：输入框创建、列表编辑、checkbox 完成、删除按钮、筛选切换
- 页面差异点：空态与错误态都要显式展示

## 5. 业务域建模

| Domain ID | 业务域 | Actor / Role | 核心 Entity | 关键规则 | 对应页面 / 接口 | 关联 AC |
| --- | --- | --- | --- | --- | --- | --- |
| TODO-CORE | todo 管理 | end user | Todo | 标题不能为空；删除后不可见；完成状态可切换 | `/todos`、`GET/POST/PATCH/DELETE /api/todos` | AC-01, AC-02, AC-03, AC-04 |
| TODO-FILTER | todo 筛选 | end user | TodoQuery | `all / active / completed` 必须与列表展示一致 | `/todos?filter=`、`GET /api/todos?filter=` | AC-05 |

## 6. 用户路径

- 用户进入列表页，看到 todo 列表和创建输入框
- 输入标题后提交，列表即时出现新项
- 用户可编辑文本、切换完成状态、删除某项
- 用户切换筛选条件查看不同集合

## 7. Acceptance Criteria

| AC ID | 优先级 | 描述 | 验证方式 | 状态 |
| --- | --- | --- | --- | --- |
| AC-01 | Must | 用户提交非空标题后可创建 todo | API test + UI test | ready |
| AC-02 | Must | 用户可编辑已有 todo 标题 | API test + UI test | ready |
| AC-03 | Must | 用户可切换完成状态 | API test + UI test | ready |
| AC-04 | Must | 用户可删除 todo | API test + UI test | ready |
| AC-05 | Must | 用户可按状态筛选 todo | API test + UI test + smoke | ready |

