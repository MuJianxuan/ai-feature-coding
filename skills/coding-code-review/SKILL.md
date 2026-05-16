---
name: coding-code-review
description: "Coding 代码审查技能。Activation restricted: use only when explicitly named or called via composition contract. Do not auto-trigger for ordinary code review requests."
---

# Coding Code Review

## 目标

对 Coding Feature Workflow 中 implementation 阶段完成的代码变更进行结构化审查，确保代码质量、安全性和一致性达到交付标准。

## 共享契约

本 skill 遵守 `coding-feature-orchestrator/WORKFLOW_CONTRACT.md` 中的 safety policy。
本 skill 的调用协议定义在 `coding-feature-orchestrator/COMPOSITION_CONTRACT.md` 中，作为 Validation Call 被调用。

## Activation policy

本 skill 是 explicit opt-in，不参与普通 Agent 工作流的自动触发。

允许启动的情况：

1. `direct_explicit`：用户在当前请求中明确写出 `coding-code-review`。
2. `composition_call`：`coding-implementation-execution` 或 `coding-verification-closeout` 通过 Validation Call 调用。

禁止启动的情况：

- 普通"帮我 review 代码 / 看看这段代码"不触发本 skill。
- 只有历史上下文曾经提过本 skill，但当前请求没有显式继续。

## 前置条件

- 存在 `feature_dir`（`.docs/feature-YYYYMMDD-short-name/`）。
- `tasks.md` 中所有任务状态为 `DONE`（或由调用方指定特定任务范围）。
- `design.md` 可读取（用于对照设计意图）。

## 审查流程

### Step 1: 收集审查上下文

1. 读取 `design.md` 的方案摘要、目标链路和验证策略。
2. 读取 `tasks.md` 中所有 `DONE` 任务的交付记录（改动文件列表）。
3. 读取项目规范（如 `.docs/spec/INDEX.md` 存在，读取相关 spec）。
4. 收集代码变更（通过 `git diff` 或任务交付记录中的文件列表）。

### Step 2: 逐维度审查

按 `references/review-dimensions.md` 中定义的 6 个维度逐一审查：

1. **Correctness** — 代码是否正确实现了 design.md 中的方案？
2. **Security** — 是否有注入、越权、信息泄露风险？
3. **Performance** — 是否有 N+1 查询、内存泄漏、不必要的计算？
4. **Maintainability** — 命名、结构、注释是否清晰？
5. **Test Coverage** — 关键路径是否有测试？边界情况是否覆盖？
6. **Consistency** — 是否与项目现有模式和 spec 一致？

### Step 3: 分级输出

每个发现按严重程度分级：

- `BLOCKING`：必须修复才能进入 verification（安全漏洞、逻辑错误、数据丢失风险）。
- `WARNING`：强烈建议修复但不阻塞（性能问题、可维护性问题）。
- `NITPICK`：可选改进（命名、格式、微小优化）。

### Step 4: 输出结果

输出结构化审查报告：

```markdown
## Code Review Report

### 总体评估
- 评估结果：PASS | PASS_WITH_WARNINGS | FAIL
- 审查范围：<文件数量和主要模块>

### BLOCKING Issues
1. [文件:行号] <问题描述> — <修复建议>

### WARNING Issues
1. [文件:行号] <问题描述> — <修复建议>

### NITPICK
1. [文件:行号] <问题描述> — <修复建议>

### 亮点
- <值得肯定的设计或实现>
```

## 与 Coding Feature Workflow 的集成

### 作为 Validation Call 被调用时

- 调用方提供：feature_dir + 审查范围（全部任务或指定任务）。
- 返回：审查报告 + pass/fail 判定。
- 如果结果为 `FAIL`（存在 BLOCKING issue）：调用方将相关任务回退为 `DOING`，记录 review finding。
- 如果结果为 `PASS` 或 `PASS_WITH_WARNINGS`：审查报告写入 `verification.md` 的"代码审查"section。

### 与 fast-track 的关系

- Fast-track 模式下，code review 是可选的（用户可跳过）。
- Standard 模式下，code review 是 verification 的前置条件。

## Safety policy

- 不修改任何源代码文件（只读审查）。
- 不修改 feature 目录下的阶段文档（由调用方负责写入）。
- 审查意见基于证据，引用具体文件和行号。
- 不对审查范围外的代码提出修改建议。

## Metrics 写入规则

本 skill 被调用时，由调用方负责向 `metrics.json` 追加 `composition_call` 事件（参见 WORKFLOW_CONTRACT.md section 16）。本 skill 自身不写入 metrics。
