# Golden Examples for AI Feature Workflow

本文件提供可复用的行为样例。只有在需要校准 AI Feature Workflow 行为、写测试或排查阶段误判时才读取；正常执行不必加载。

## 1. Happy path

用户请求：

```text
使用 ai-feature-orchestrator，为“导出审计日志 CSV”启动一条新的 AI Feature Workflow：管理员可以按日期导出审计日志。
```

期望行为：

1. Orchestrator 创建 `.docs/feature-YYYYMMDD-export-audit-log-csv/`，复制模板。
2. `requirements.md` 记录原始需求、in-scope / out-of-scope、可验证 acceptance criteria。
3. `ai-requirement-intake` 完成后停下，`requirements.md stage_status: ready`。
4. 用户说“继续下一阶段”后进入 `ai-repo-investigation`，写真实代码链路和数据来源。
5. `ai-technical-design` 写方案，`design.md stage_status: ready` 且 `approval_status: pending`，然后停下等待用户批准。
6. 用户明确批准设计后，记录 `approval_status: approved`，再进入 `ai-task-planning`。
7. 编码阶段一次只执行一个 `TODO` / `DOING` 任务；验证阶段把每条 AC 映射到命令、接口响应、数据查询或手工步骤。

不允许行为：

- 普通“帮我做导出功能”自动触发 AI Feature Workflow。
- 设计刚写完就自动拆任务。
- 一个任务完成后自动执行下一个任务。

## 2. Blocked requirement

场景：需求中要求“导出字段按合规要求脱敏”，但仓库里无法判断哪些字段属于敏感字段。

期望行为：

1. 先自行查仓库：日志表 schema、已有脱敏 helper、权限配置、旧导出实现。
2. 如果仍无法确定，`requirements.md` 写入 `BLOCKING` 待确认问题，附已查证据。
3. 将 `requirements.md stage_status` 标记为 `blocked`。
4. 输出只问一个阻塞问题，例如“审计日志 CSV 中 user_email 是否需要脱敏？”并列出已查证据。
5. 不进入 `ai-repo-investigation` / `ai-technical-design`。

不允许行为：

- 空手问用户字段规则，不先查仓库。
- 把阻塞问题标成 `NON_BLOCKING` 后继续设计。

## 3. Resume DOING

场景：`tasks.md` 中存在：

```markdown
### T03 - 接入导出按钮

- status: DOING
- 输入：design.md#UI 入口，src/pages/AuditLog.tsx
- 输出：导出按钮、loading/error 状态
- 完成判定：pnpm test -- AuditLogExport；手工点击导出能下载 CSV
- 关联模块/文件：src/pages/AuditLog.tsx, src/api/audit.ts
- 交付记录：已添加 API helper，UI 尚未接入 error toast
```

期望行为：

1. `ai-implementation-execution` 优先恢复 T03，不选择后续 TODO。
2. 开始前检查工作区 diff，区分用户改动和 AI 改动。
3. 对照 T03 的输入、输出、完成判定继续，不创建 T03b 或重复任务掩盖中断。
4. 如果 diff 超出 T03 范围，停止并报告风险，等待用户确认。

不允许行为：

- 跳过 DOING 去执行第一个 TODO。
- 因为验证未完成就把 T03 标为 DONE。

## 4. Verification failed

场景：所有 tasks 都标记为 `DONE`，但 `verification.md` 中 AC-02 “无权限用户不能导出”验证失败。

期望行为：

1. `ai-verification-closeout` 记录 AC-02 的失败证据：命令、接口响应、日志或手工步骤。
2. `verification.md` 保持未完成或写明 FAIL / BLOCKED 结论。
3. `handoff.md` 写残余风险和最短复核路径。
4. 如果修复失败项需要新代码，回到 `tasks.md` 新增或恢复任务；不要把失败项隐藏成 PASS。

不允许行为：

- 只因为主 happy path 通过就把 verification / handoff 标记 complete。
- 自动 git commit、归档或发布。
