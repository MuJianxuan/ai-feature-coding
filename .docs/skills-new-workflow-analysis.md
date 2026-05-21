---
doc_type: workflow_analysis
doc_status: draft
updated_at: 2026-05-21T00:00:00+08:00
---

# 新工作流重组分析

## 1. 旧 skill 的主要问题

| 旧能力 | 现状问题 | 处理方式 |
| --- | --- | --- |
| `coding-feature-discovery` + `coding-requirement-intake` | 都在做需求证据吸收、模糊点澄清和可验证 scope 规格化，阶段边界过细 | 合并为 `product-requirements` |
| `coding-technical-design` | 技术方案本身较强，但没有把技术最新信息、new project / existing project 分岔、前后端接口映射、UI 原型映射收拢到同一阶段 | 升级为 `technical-solution` |
| `coding-task-planning` | 只有单份 `tasks.md`，不支持前后端分轨实施计划 | 重写为 `implementation-planning`，产出 `frontend-plan.md` + `backend-plan.md` |
| `coding-implementation-execution` | 主体可复用，但输入产物需要从单 `tasks.md` 迁移为“双计划 + task ledger” | 保留并改接新计划产物 |
| `coding-verification-closeout` | 能做收口，但缺“实施计划验收汇报”的显式表达 | 升级为 `verification-handoff` |
| 各阶段重复的 activation / route / safety / gate / metrics | 同类规则在多个 skill 重复，维护成本高 | 上收为共享 `WORKFLOW_CONTRACT.md` |

## 2. 新工作流目标

面向以下链路：

1. 基于需求资料吸收上下文：PRD、原型、UIUX、墨刀、Figma、会议纪要、接口草案
2. 进行需求评审、范围澄清、业务域建模和验收标准收敛
3. 通过 Requirements Gate
4. 进行技术最新信息获取、技术选型、架构选型、new project / existing project 分岔设计
5. 输出前后端详细技术方案、页面到接口映射、数据模型和风险回滚
6. 通过 Solution Gate
7. 输出可执行的 `frontend-plan.md` 和 `backend-plan.md`
8. 通过 Planning Gate
9. 基于 spec 执行编码
10. 完成前后端测试、验收映射和实施计划验收汇报

## 3. 新 skill 拆分

| 新 skill | 角色 | 说明 |
| --- | --- | --- |
| `workflow-orchestrator` | 总控 | 入口、阶段判定、门禁判定、模板初始化、恢复执行 |
| `product-requirements` | 需求阶段 | 吸收需求资料、仓库现状、业务域、AC、需求评审门禁 |
| `technical-solution` | 技术方案阶段 | 技术调研、技术选型、架构选型、前后端方案、接口映射、方案门禁 |
| `implementation-planning` | 实施计划阶段 | 输出前后端独立计划文档、依赖和测试任务、计划门禁 |
| `implementation-execution` | 编码阶段 | 按 task ledger 执行一个任务并留下证据 |
| `verification-handoff` | 验收阶段 | 前后端测试、AC 映射、代码审查、验收汇报、残余风险 |

## 4. 三道硬门禁

### Requirements Gate

通过条件：

- 需求资料已索引
- 业务目标、in-scope、out-of-scope 明确
- 业务域建模完成
- AC 可验证
- 原型 / UI 关键约束已落文

### Solution Gate

通过条件：

- 技术调研结论有证据来源
- 已确定 `existing_project` 或 `greenfield_project`
- 前后端方案、接口、数据模型、异常路径、风险回滚完整
- 页面到接口映射或调用链完整

### Planning Gate

通过条件：

- `frontend-plan.md` 可独立执行
- `backend-plan.md` 可独立执行
- 依赖顺序与并行边界明确
- 前后端测试任务和交付记录入口已进入计划

## 5. 为什么不用“一个超级 skill”

- 你的流程包含多次门禁，单 skill 会让状态恢复与审批记录混乱。
- 前后端计划是显式双文档，不适合塞进单个超长说明。
- 技术方案门禁和实施计划门禁是两层不同职责，强行合并会削弱审查质量。

## 6. TODO Web 应用作为验证样例

新工作流至少要支持一个完整 TODO Web 应用。样例应覆盖：

- 前端：列表页、创建、编辑、完成、删除、筛选、空态、错误态
- 后端：Todo CRUD API、校验、错误模型、存储结构
- 计划：页面到 API 映射、前后端依赖、测试任务
- 验收：AC 映射、自动化验证、手工 smoke、残余风险

## 7. 结论

最终采用：

- `1 个总控 + 5 个阶段 skill`
- `3 道硬门禁`
- `frontend-plan.md + backend-plan.md`
- `explicit opt-in`

