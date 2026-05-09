---
name: ai-verification-closeout
description: "AI 验证收口技能。Activation restricted: use only when the user explicitly names `ai-verification-closeout`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary testing, verification, QA, release notes, or handoff requests."
---

# AI Verification Closeout

## 目标

证明需求已经按 scope 交付，或清楚说明还剩什么风险和阻塞。验证不是跑一个命令，而是把 acceptance criteria 和实际证据对齐。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-verification-closeout`，或明确要求使用这套 AI feature workflow 的验证收口阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 testing / QA / handoff 自动升级成这套工作流。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md`、`design.md` 和 `tasks.md` 已存在。
- `verification.md` 和 `handoff.md` 已由 orchestrator/template 准备好。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## 验证顺序

1. 读取 `requirements.md` 的 acceptance criteria。
2. 读取 `tasks.md`，确认所有 in-scope 任务为 `DONE` 或有明确 `BLOCKED` 说明。
3. 按 `design.md` 的验证策略执行 targeted checks。
4. 对每条验收标准记录证据：命令、日志、截图路径、接口响应摘要、数据查询或手工步骤。
5. 检查相关同类路径是否需要回归。
6. 汇总无法验证的项目和原因。

## 文档更新

`verification.md` 记录：

- 验收标准映射表
- 执行过的命令和结果
- 手工验证步骤
- 未覆盖场景
- 回归风险

`handoff.md` 记录：

- 交付摘要
- 变更文件和影响范围
- 配置、SQL、部署或数据操作
- 用户复核入口
- 后续建议

## 完成定义

- in-scope acceptance criteria 都有验证结论。
- 失败或未覆盖项不能被隐藏，必须写入残余风险。
- 如果需要用户验收，给出最短复核路径，不要求用户自行翻找。
