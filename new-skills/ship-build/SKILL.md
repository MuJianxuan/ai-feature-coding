---
name: ship-build
description: "新 ShipKit Build 阶段。用户确认设计后，按 design.md 生成任务清单、实现代码、运行测试、验证 AC，并生成 verification.md。"
---

# ship-build

## 目标

把 `design.md(status: ready)` 变成可工作的代码，并证明所有 AC 被测试或验证覆盖。Build 的成功标准不是“写完代码”，而是“可交付”。

## 前置条件

必须同时满足：

- `meta.yml.current_stage: build`。
- `design.md` frontmatter `status: ready`。
- `meta.yml` 或对话中有明确用户确认进入 Build。
- `validate_design.py <feature_dir>` 无 errors。

不满足就退回 orchestrator/design。不要开后门。

## 流程

1. 加载 `design.md`、`requirements.md`、Build 阶段 spec（coding conventions、test standards）。
2. 从设计生成 `build-plan.yml`。
3. 按依赖顺序实现：数据层 → 后端 → 前端 → 集成。
4. 每完成一个任务，运行相关测试。
5. 最后运行项目真实测试/lint/typecheck（按仓库现有命令，不臆造）。
6. 生成 `verification.md`，逐项映射 AC 到测试或证据。
7. 运行 `validate_build.py`。
8. 成功后更新 spec 的 existing-features，并按评分决定是否建议沉淀新规范。
9. 更新 `meta.yml.current_stage: done`、`status: completed`。

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

## 完成后 spec 更新

调用 `ship-spec`：

- 更新 `.docs/spec/shared/existing-features.md` 或对应项目的 existing-features。
- 提取表、API、页面、重要实现路径。
- 按 60 分规则判断是否建议新增规范：复用次数、稳定性、影响范围、复杂度。

## 不做什么

- 不跳过测试声称完成。
- 不把“validator 通过”当成真实测试通过。
- 不扩大修改范围；每个改动必须能追溯到 AC 或 design。
