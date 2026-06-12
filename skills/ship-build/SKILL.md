---
name: ship-build
description: "ShipKit Build 阶段。必须接收 feature_dir，验证 orchestrator 持久化的 Build approval，按 design 实现、测试并产出 verification.md。"
---

# ship-build

## 目标

把 `design.md(status: ready)` 变成可工作的代码，并证明所有 AC 被测试或验证覆盖。Build 的成功标准不是“写完代码”，而是“可交付”。

## 硬前置

必须同时满足：

- 用户明确提供 `feature_dir`。
- `feature_dir/meta.yml` 存在且可读取。
- `meta.yml.current_stage: build`。
- `meta.yml.status: in_progress`。
- `meta.yml.build_approved_at/build_approved_by/build_approval_note` 已由 `ship-orchestrator` 写入。
- `design.md` frontmatter `status: ready`。
- `validate_design.py <feature_dir>` 无 errors。

缺 `feature_dir`、缺任一 Build approval 字段、或仍停留在 Design confirmation 时停止，不接受“对话里确认过”作为唯一依据。

## TODO preflight

开始阶段工作前，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Build 阶段 TODO：

1. 加载 `meta.yml`、`requirements.md`、`design.md`。
2. 根据 `workspace_mode/projects` 限定实现和测试命令选择。
3. 运行 `validate_design.py <feature_dir>`。
4. 生成 `build-plan.yml`。
5. 按依赖顺序实现代码。
6. 按任务运行相关测试。
7. 运行项目真实 test/lint/typecheck。
8. 写 `verification.md`，逐项映射 AC。
9. 运行 `validate_build.py <feature_dir>`。
10. 更新 spec existing-features 或提出沉淀建议。
11. 更新 `meta.yml.current_stage: done`、`status: completed`。

## Workspace scope

- `workspace_mode: single_project`：实现范围默认当前项目。
- `workspace_mode: project_group`：只修改 `meta.yml.projects` 指定项目和必要 `_shared`；测试命令优先运行相关项目及必要集成测试。
- 需要扩大范围时停止并说明原因，回到 orchestrator/用户确认后再改 `meta.yml.projects`。

## 流程

1. 加载 `meta.yml`、`requirements.md`、`design.md`、Build 阶段 spec（coding conventions、test standards）。
2. 运行 `validate_design.py <feature_dir>`。
3. 从设计生成 `build-plan.yml`。
4. 按依赖顺序实现：数据层 → 后端 → 前端 → 集成。
5. 每完成一个任务，运行相关测试。
6. 最后运行项目真实 test/lint/typecheck（按仓库现有命令，不臆造）。
7. 生成 `verification.md`，逐项映射 AC 到测试或证据。
8. 运行 `validate_build.py <feature_dir>`。
9. 成功后更新 spec 的 existing-features，并按评分决定是否建议沉淀新规范。
10. 更新 `meta.yml.current_stage: done`、`status: completed`。

## build-plan.yml 生成规则

任务顺序固定，别玩花活：

1. 数据层：migration/table/index，优先级最高。
2. 后端：Service 先于 Controller/API。
3. 前端：State 可独立，页面依赖 API contract。
4. 集成：E2E/集成测试最后，依赖所有任务。

任务粒度：

- 单个任务预计不超过 60 分钟。
- 每个任务必须关联 `ac_refs`。
- `dependencies` 必须显式。
- 能并行的任务可以标注，但不要牺牲可验证性。

```yaml
tasks:
  - id: T-001
    name: 创建 Session 表迁移
    type: database
    priority: high
    files: ["migrations/001_create_sessions.sql"]
    dependencies: []
    ac_refs: ["AC-1", "AC-2"]
    status: pending
```

## verification.md 结构

```markdown
---
status: ready
updated_at: "2026-06-09T18:00:00Z"
all_ac_passed: true
---

# 验证报告

## AC 验证状态
- ✅ AC-1: 正常登录 (covered by: tests/e2e/login.spec.ts)
- ✅ AC-2: 密码错误 (covered by: tests/auth.service.test.ts)

## 测试覆盖
- Unit: 15 passed
- Integration: 3 passed
- E2E: 2 passed

## 代码质量
- Lint: 0 errors
- Typecheck: passed

## 产出文件
- src/services/auth.service.ts
- tests/auth.service.test.ts

## 未覆盖项
无。
```

## 失败处理

- 测试失败：写入 `verification.md`，更新 `meta.yml.status: blocked`、`blocked_reason: test_failures`，给最小修复计划。
- AC 无测试：不能标记 done；补测试或写可审计的人工验证证据。
- 设计缺口：退回 Design，不在 Build 阶段猜架构。
- spec 加载失败：降级为仓库现状探索，但必须记录 warning。
- `validate_build.py` 失败：逐项修复后重新运行，不能以“真实测试已过”跳过 validator。

## 完成后 spec 更新

使用 `ship-spec` CLI：

- 更新 `.docs/spec/shared/existing-features.md` 或对应项目的 existing-features。
- 多项目组下只更新 `_shared` 和 `meta.yml.projects` 指定项目。
- 提取表、API、页面、重要实现路径。
- 按 60 分规则判断是否建议新增规范：复用次数、稳定性、影响范围、复杂度。

## 不做什么

- 不跳过测试声称完成。
- 不把“validator 通过”当成真实测试通过。
- 不扩大修改范围；每个改动必须能追溯到 AC 或 design。
- 不在缺少 `build_approved_at/build_approved_by/build_approval_note` 时实现代码。
- 不修改未包含在 `workspace_mode/projects` 范围内的项目。
