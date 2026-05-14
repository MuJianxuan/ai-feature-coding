# Golden Examples for Coding Feature Workflow

本文件提供可复用的行为样例。只有在需要校准 Coding Feature Workflow 行为、写测试或排查阶段误判时才读取；正常执行不必加载。

## 1. Happy path

用户请求：

```text
使用 coding-feature-orchestrator，为“导出审计日志 CSV”启动一条新的 Coding Feature Workflow：管理员可以按日期导出审计日志。
```

期望行为：

1. Orchestrator 创建 `.docs/feature-YYYYMMDD-export-audit-log-csv/`，复制模板。
2. `discovery.md` 记录仓库广扫、必要外部调研、2-3 个方案方向、全部模糊点和逐问逐答记录。
3. `coding-feature-discovery` 完成后停下，`discovery.md stage_status: ready`、`evidence_complete: true`，并更新 `updated_at`。
4. 用户说“继续下一阶段”后进入 `coding-requirement-intake`，把 discovery 结论规格化为 in-scope / out-of-scope、可验证 acceptance criteria；完成时 `requirements.md stage_status: ready`、`evidence_complete: true`。
5. 用户说“继续下一阶段”后进入 `coding-repo-investigation`，按 ready PRD 精查真实代码链路和数据来源；完成时 `investigation.md stage_status: ready`、`evidence_complete: true`，并更新 `updated_at`。
6. `coding-technical-design` 写方案，`design.md stage_status: ready`、`evidence_complete: true` 且 `approval_status: pending`，然后停下等待用户批准。
7. 用户明确批准设计后，记录 `approval_status: approved`、`approved_by`、`approved_at`、`approval_evidence`，同步更新 `updated_at`，再进入 `coding-task-planning`。
8. `coding-task-planning` 写真实任务后，`tasks.md stage_status: ready`、`evidence_complete: true`、`task_count` 等于真实任务数量，并更新 `updated_at`；真实任务 ID 不重复。
9. 编码阶段一次只执行一个 `TODO` / `DOING` 任务；`DONE` 任务交付记录必须包含改动文件、验证命令或证据、结果、残余风险。验证阶段必须读取 `discovery.md` 的澄清边界，且必须读取 `investigation.md` 的真实调用链、数据来源，再把每条 AC 映射到命令、接口响应、数据查询或手工步骤。

不允许行为：

- 普通“帮我做导出功能”自动触发 Coding Feature Workflow。
- 跳过 `discovery.md` 直接写 `requirements.md`。
- 设计刚写完就自动拆任务。
- 一个任务完成后自动执行下一个任务。
- `task_count` 仍为 0 或 `updated_at` 未更新却声称任务规划完成。
- 同时存在多个 `DOING` 任务时自行选择一个继续。
- 用“已完成”替代结构化交付记录。
- 验证阶段只按 `design.md` / `tasks.md` 做纸面验证，跳过 `investigation.md` 的真实链路和 source of truth。

## 2. Blocked requirement

场景：需求中要求“导出字段按合规要求脱敏”，但仓库里无法判断哪些字段属于敏感字段。

期望行为：

1. 先在 discovery 阶段自行查仓库：日志表 schema、已有脱敏 helper、权限配置、旧导出实现。
2. 如果仍无法确定，`discovery.md` 写入 `BLOCKING` 模糊点，附已查证据。
3. 将 `discovery.md stage_status` 标记为 `blocked`、`evidence_complete: false`，并更新 `updated_at`。
4. 输出只问一个阻塞问题，例如“审计日志 CSV 中 user_email 是否需要脱敏？”并列出已查证据。
5. 不进入 `coding-requirement-intake` / `coding-repo-investigation` / `coding-technical-design`。

不允许行为：

- 空手问用户字段规则，不先查仓库。
- 把阻塞问题标成 `NON_BLOCKING` 后继续设计。
- `stage_status: blocked` 时仍写成 `evidence_complete: true`。

## 3. Resume DOING

场景：`tasks.md` 中存在：

```markdown
### T03 - 接入导出按钮

- status: DOING
- 输入：design.md#UI 入口，src/pages/AuditLog.tsx
- 输出：导出按钮、loading/error 状态
- 完成判定：pnpm test -- AuditLogExport；手工点击导出能下载 CSV
- 关联模块/文件：src/pages/AuditLog.tsx, src/api/audit.ts
- 执行要点：复用既有 API client 和 toast 模式，保持导出按钮 loading/error 状态一致。
- 风险：导出失败提示可能与现有列表错误态不一致；需手工覆盖失败路径。
- 交付记录：已添加 API helper，UI 尚未接入 error toast
```

期望行为：

1. `coding-implementation-execution` 优先恢复 T03，不选择后续 TODO。
2. 开始前检查工作区 diff，区分用户改动和 AI 改动。
3. 对照 T03 的输入、输出、完成判定继续，不创建 T03b 或重复任务掩盖中断。
4. 修改 `tasks.md` 的任务状态、交付记录或风险时，更新 `updated_at`，并保持 `task_count` 等于真实任务数量；如果发现多个 `DOING` 或重复任务 ID，先停止整理状态，不自行选择。
5. 如果 diff 超出 T03 范围，停止并报告风险，等待用户确认。

不允许行为：

- 跳过 DOING 去执行第一个 TODO。
- 因为验证未完成就把 T03 标为 DONE。
- 编码执行阶段未经 scope change 回流就随意修改 `task_count` 或把 `tasks.md stage_status` 改成其他状态。

## 4. Verification failed

场景：所有 tasks 都标记为 `DONE`，但 `verification.md` 中 AC-02 “无权限用户不能导出”验证失败。

期望行为：

1. `coding-verification-closeout` 先读取 `discovery.md` 的澄清边界，再读取 `investigation.md` 的真实调用链、数据来源、相似实现和风险，最后记录 AC-02 的失败证据：命令、接口响应、日志或手工步骤。
2. `verification.md` 保持未完成或写明 FAIL / BLOCKED 结论，`evidence_complete: false`，并更新 `updated_at`。
3. `handoff.md` 写残余风险和最短复核路径；如果交付信息仍不完整，保持 `evidence_complete: false`。
4. `handoff.md` 必须写明配置 / SQL / 部署 / 数据修复事项；无相关事项也要显式写“无”。
5. 如果修复失败项需要新代码，回到 `tasks.md` 新增或恢复任务；不要把失败项隐藏成 PASS。

不允许行为：

- 只因为主 happy path 通过就把 verification / handoff 标记 complete。
- 自动 git commit、归档或发布。
- 未读取 `investigation.md` 就把验证结论写成 complete。
- 存在 FAIL / BLOCKED 却把 `verification.md evidence_complete` 标成 true。
