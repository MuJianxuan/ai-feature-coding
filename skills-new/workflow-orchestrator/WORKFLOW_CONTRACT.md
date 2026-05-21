# Skills-New Workflow Contract

本文件定义 `workflow-orchestrator` 与各阶段 skill 的共享契约。所有 `skills-new/*` 阶段 skill 必须优先遵守本契约。

## 1. Activation contract

本 workflow 采用 `explicit opt-in`：

- 允许：用户明确要求使用该 workflow，或明确写出 `workflow-orchestrator` / 阶段 skill 名
- 禁止：普通“帮我做功能 / 帮我设计方案 / 帮我写计划 / 帮我测一下”

## 2. Route contract

被总控路由到阶段 skill 时，必须携带：

```yaml
activation_source: workflow-orchestrator
workflow_dir: .docs/workflows/workflow-YYYYMMDD-short-name
stage_evidence:
  reason: "<为什么进入该阶段>"
  files:
    - path: <相关文档路径>
      finding: <关键证据>
```

阶段 skill 在以下情况下必须拒绝启动：

- 缺 `workflow_dir`
- 缺 `activation_source`
- 缺 `stage_evidence`
- 上游 gate 不满足

## 3. Directory contract

标准目录：

```text
.docs/workflows/workflow-YYYYMMDD-short-name/
  README.md
  source-index.md
  requirements.md
  requirements-gate.md
  tech-research.md
  solution.md
  solution-gate.md
  frontend-plan.md
  backend-plan.md
  plan-gate.md
  task-ledger.md
  verification.md
  handoff.md
  sql/
    DDL.sql
    DML.sql
    ROLLBACK.sql
```

## 4. Metadata contract

阶段主文档使用：

```yaml
feature_stage: product-requirements | technical-solution | implementation-planning | implementation-execution | verification-handoff
stage_status: draft | ready | blocked | complete
updated_at: "2026-05-21T00:00:00+08:00"
evidence_complete: false
project_mode: unknown | existing_project | greenfield_project
project_mode_evidence: ""
```

gate 文档使用：

```yaml
doc_type: gate
gate_name: requirements | solution | planning
gate_status: pending | pass | blocked
updated_at: "2026-05-21T00:00:00+08:00"
decision_by: ""
decision_evidence: ""
```

辅助文档 `README.md`、`source-index.md`、`tech-research.md`、`sql/*.sql` 不使用 `feature_stage`。

## 5. Gate definitions

### Requirements Gate

必须证明：

- 需求资料已索引
- 业务目标明确
- in-scope / out-of-scope 明确
- 业务域建模完成
- AC 可验证
- 原型 / UI 关键约束已落文

### Solution Gate

必须证明：

- 技术调研引用官方或一手资料
- 已确定 `existing_project` 或 `greenfield_project`
- 前后端技术方案完整
- 页面 / API / 数据模型 / 异常路径映射完整
- 风险、降级、回滚、验证策略完整

### Planning Gate

必须证明：

- `frontend-plan.md` 可独立执行
- `backend-plan.md` 可独立执行
- 依赖顺序和并行边界明确
- 前后端测试任务已规划
- `task-ledger.md` 初始化完成

## 6. Upstream gate rules

- `product-requirements`：只要求存在工作目录和需求资料索引
- `technical-solution`：要求 `requirements.md stage_status: ready` 且 `requirements-gate.md gate_status: pass`
- `implementation-planning`：要求 `solution.md stage_status: ready` 且 `solution-gate.md gate_status: pass`
- `implementation-execution`：要求 `frontend-plan.md`、`backend-plan.md` 均 `stage_status: ready` 且 `plan-gate.md gate_status: pass`
- `verification-handoff`：要求 `task-ledger.md` 中不存在 `TODO` 或 `DOING` 任务

## 7. Task ledger rules

`task-ledger.md` 是执行阶段的唯一状态源。每个任务至少包含：

- `task_id`
- `track`: `frontend` | `backend` | `cross`
- `status`: `TODO` | `DOING` | `DONE` | `BLOCKED`
- `depends_on`
- `source_plan`
- `acceptance_link`
- `deliverable`
- `verification`
- `delivery_record`

同一时刻最多允许一个真实 `DOING` 任务。

## 8. Service startup and port-check

需要启动服务前，必须记录：

1. 目标命令
2. 预期端口
3. 端口占用检查结果
4. 已有进程是否属于当前项目
5. 停止方式

如果端口被无关进程占用，不得擅自 kill。

## 9. Scope change

发现 scope 扩大时：

1. 记录候选变更和证据
2. 先停止
3. 等用户确认
4. 回流更新 `requirements.md` / `solution.md` / `frontend-plan.md` / `backend-plan.md` / `task-ledger.md`

## 10. New project policy

`greenfield_project` 必须优先采用成熟可靠的官方脚手架初始化方案，并在 `tech-research.md` 中记录：

- 候选脚手架
- 官方来源
- 选择理由
- 初始化命令
- 后续最小可运行目标

## 11. Verification policy

验证阶段必须覆盖：

- 后端测试
- 前端测试
- AC 映射
- 手工 smoke
- 残余风险
- 用户最短复核路径

