---
name: ai-task-planning
description: "AI 任务拆解技能。Activation restricted: use only when the user explicitly names `ai-task-planning`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary planning, TODO creation, or implementation breakdown requests."
---

# AI Task Planning

## 目标

把技术设计拆成 AI 可以逐项执行的任务清单。`tasks.md` 是编码执行的唯一驱动文件。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-task-planning`，或明确要求使用这套 AI feature workflow 的任务拆解阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通任务拆解自动升级成这套工作流。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md`、`investigation.md` 和 `design.md` 已存在。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## 拆解规则

1. 每项任务只覆盖一个清晰目标，能独立完成和验证。
2. 按依赖顺序排序：schema/config -> backend/domain -> API/adapter -> frontend/state -> tests/docs。
3. 每项任务必须写：
   - `status`: `TODO` / `DOING` / `DONE` / `BLOCKED`
   - 输入：依赖的需求、设计、证据或文件。
   - 输出：预期改动文件或行为。
   - 完成判定：可执行命令、接口响应、UI 行为或数据状态。
   - 关联模块/文件：尽量列路径或搜索关键词。
   - 风险：可能影响的兼容性、数据、权限或性能。
4. 不把“验证全部功能”作为单个大任务；验证也要按风险拆分。
5. 如果发现设计不可拆或范围过大，回到 `design.md` 缩小边界。

## 推荐任务模板

```markdown
### T01 - <任务名>

- status: TODO
- 输入：
- 输出：
- 关联模块/文件：
- 执行要点：
- 完成判定：
- 风险：
- 交付记录：
```

## 输出

更新 `tasks.md`。除非用户明确要求，否则不要开始编码。
